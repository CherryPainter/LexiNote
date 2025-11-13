import sqlite3
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

from logger import log_info, log_error


class DatabaseManager:
    """数据库管理器，负责所有数据库操作
    版本更新：确保core目录文件正确同步"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化数据库管理器"""
        # 确保只初始化一次
        with self._lock:
            if not hasattr(self, '_initialized'):
                self.data_dir = 'data'
                self.db_path = os.path.join(self.data_dir, 'lexinote.db')
                self._write_queue = []
                self._write_lock = threading.Lock()
                self._last_write_time = datetime.now()
                
                # 创建数据目录
                os.makedirs(self.data_dir, exist_ok=True)
                
                # 初始化数据库
                self._init_database()
                
                # 创建听写相关表结构
                self.create_dictation_tables()
                
                # 创建练习会话表
                self.create_exercise_sessions_table()
                
                # 启动延迟写入线程
                self._start_write_worker()
                
                self._initialized = True
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 启用WAL模式提升并发性能
            cursor.execute('PRAGMA journal_mode=WAL')
            # 在遇到锁时等待（毫秒），减少 "database is locked" 错误
            try:
                cursor.execute('PRAGMA busy_timeout = 5000')
            except Exception:
                pass
            
            # 创建词库信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    source TEXT,
                    create_time TEXT,
                    word_count INTEGER DEFAULT 0
                )
            ''')
            
            # 先创建默认词库
            self._create_default_word_set(conn=conn)
            
            # 检查并迁移现有的words表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            if cursor.fetchone():
                # 检查表是否有set_id列
                cursor.execute("PRAGMA table_info(words)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'set_id' not in columns:
                    # 添加set_id列
                    log_info("检测到旧版本words表，正在添加set_id列...")
                    cursor.execute("ALTER TABLE words ADD COLUMN set_id INTEGER")
                    
                    # 获取默认词库ID
                    cursor.execute("SELECT id FROM word_sets WHERE name='默认词库'")
                    default_set_id = cursor.fetchone()[0]
                    
                    # 更新所有现有单词的set_id为默认词库
                    cursor.execute("UPDATE words SET set_id = ?", (default_set_id,))
                    log_info("单词表迁移完成，所有单词已关联到默认词库")
                
                # 检查并添加其他必要的列
                columns_to_add = [
                    ('phonetic', 'TEXT'),
                    ('example', 'TEXT'),
                    ('meaning_en', 'TEXT'),
                    ('tag', 'TEXT'),
                    ('example_translation', 'TEXT')
                ]
                
                for column_name, column_type in columns_to_add:
                    if column_name not in columns:
                        log_info(f"检测到单词表缺少 {column_name} 列，正在添加...")
                        cursor.execute(f"ALTER TABLE words ADD COLUMN {column_name} {column_type}")
                        log_info(f"成功添加 {column_name} 列")
            else:
                # 创建新的单词表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        set_id INTEGER,
                        word TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    phonetic TEXT,
                    example TEXT,
                    meaning_en TEXT,
                    tag TEXT,
                    example_translation TEXT,
                        familiarity INTEGER DEFAULT 0,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_practice TIMESTAMP,
                        last_review TIMESTAMP,
                        proficiency FLOAT DEFAULT 0.0,
                        FOREIGN KEY (set_id) REFERENCES word_sets(id)
                    )
                ''')
            
            # 创建单词索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_proficiency ON words(proficiency)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_set_id ON words(set_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_set_name ON word_sets(name)')
            
            # 创建学习进度表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    practice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_correct INTEGER,
                    proficiency_change FLOAT,
                    FOREIGN KEY (word) REFERENCES words(word)
                )
            ''')
            
            # 创建日期索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_practice_date ON progress(practice_date)')
            
            # 创建设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # 创建AI缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash INTEGER NOT NULL,
                    prompt TEXT,
                    response TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    UNIQUE(prompt_hash)
                )
            ''')
            
            # 创建缓存索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompt_hash ON ai_cache(prompt_hash)')
            
            # 创建索引
            try:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_proficiency ON words(proficiency)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_set_id ON words(set_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_set_name ON word_sets(name)')
            except Exception as e:
                log_warning(f"创建索引时出错: {e}")
            # 从JSON导入现有数据（延迟执行，确保数据库结构完全创建）
            try:
                self._import_from_json()
            except Exception as e:
                log_error(f"导入JSON数据失败: {str(e)}")
            
            # 更新词库的单词数量
            self._update_all_word_counts(conn=conn)
            
            conn.commit()
            conn.close()
            log_info("数据库初始化成功")
            
        except Exception as e:
            log_error(f"初始化数据库失败: {str(e)}")
    
    def _create_default_word_set(self, conn=None):
        """创建默认词库"""
        try:
            if conn is None:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                auto_close = True
            else:
                cursor = conn.cursor()
                auto_close = False
            
            # 检查默认词库是否存在
            cursor.execute("SELECT id FROM word_sets WHERE name = '默认词库'")
            if cursor.fetchone():
                if auto_close:
                    conn.close()
                return
            
            # 创建默认词库
            from datetime import datetime
            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO word_sets (name, description, source, create_time, word_count) VALUES (?, ?, ?, ?, ?)",
                ('默认词库', '系统默认词库', 'system', create_time, 0)
            )
            default_set_id = cursor.lastrowid
            
            # 更新现有单词的set_id为默认词库
            cursor.execute("UPDATE words SET set_id = ? WHERE set_id IS NULL", (default_set_id,))
            
            # 更新词库单词数
            cursor.execute("SELECT COUNT(*) FROM words WHERE set_id = ?", (default_set_id,))
            word_count = cursor.fetchone()[0]
            cursor.execute("UPDATE word_sets SET word_count = ? WHERE id = ?", (word_count, default_set_id))
            
            log_info("默认词库创建成功")
            
            if auto_close:
                conn.commit()
                conn.close()
        except Exception as e:
            log_error(f"创建默认词库失败: {str(e)}")
            if 'conn' in locals() and not conn.in_transaction:
                conn.rollback()
                if 'auto_close' in locals() and auto_close:
                    conn.close()
    
    def _update_all_word_counts(self, conn=None):
        """更新所有词库的单词数量"""
        try:
            if conn is None:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                auto_close = True
            else:
                cursor = conn.cursor()
                auto_close = False
            
            # 获取所有词库
            cursor.execute("SELECT id FROM word_sets")
            sets = cursor.fetchall()
            
            for set_id, in sets:
                # 统计每个词库的单词数量
                cursor.execute("SELECT COUNT(*) FROM words WHERE set_id = ?", (set_id,))
                count = cursor.fetchone()[0]
                
                # 更新词库的单词数量
                cursor.execute("UPDATE word_sets SET word_count = ? WHERE id = ?", (count, set_id))
            
            log_info("所有词库单词数量更新完成")
            
            if auto_close:
                conn.commit()
                conn.close()
        except Exception as e:
            log_error(f"更新词库单词数量失败: {str(e)}")
            if 'conn' in locals() and not conn.in_transaction:
                conn.rollback()
                if 'auto_close' in locals() and auto_close:
                    conn.close()
    
    def _import_from_json(self):
        """从旧的JSON文件导入数据到SQLite"""
        try:
            # 检查是否已经导入过
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表结构是否正确
            try:
                # 先获取默认词库ID
                cursor.execute("SELECT id FROM word_sets WHERE name = '默认词库'")
                result = cursor.fetchone()
                if not result:
                    log_error("默认词库不存在，无法导入数据")
                    conn.close()
                    return
                default_set_id = result[0]
                
                # 检查words表结构
                cursor.execute("PRAGMA table_info(words)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'set_id' not in columns:
                    log_error("words表没有set_id列，跳过导入")
                    conn.close()
                    return
                
                # 检查是否已经导入过数据
                cursor.execute("SELECT COUNT(*) FROM words")
                count = cursor.fetchone()[0]
                
                # 如果已经有数据，跳过导入
                if count > 0:
                    log_info(f"数据库已有{count}条单词记录，跳过导入")
                    conn.close()
                    return
                
                # 导入单词数据
                word_dict_file = os.path.join(self.data_dir, 'word_dict.json')
                if os.path.exists(word_dict_file):
                    import json
                    with open(word_dict_file, 'r', encoding='utf-8') as f:
                        word_dict = json.load(f)
                        
                        imported_count = 0
                        for word, translation in word_dict.items():
                            try:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO words (set_id, word, translation) VALUES (?, ?, ?)",
                                    (default_set_id, word, translation)
                                )
                                imported_count += cursor.rowcount
                            except Exception as e:
                                log_warning(f"导入单词 {word} 失败: {e}")
                                continue
                        
                        log_info(f"成功导入 {imported_count} 个单词到默认词库")
                        
                        # 更新默认词库的单词数量
                        if imported_count > 0:
                            cursor.execute("UPDATE word_sets SET word_count = ? WHERE id = ?", 
                                         (imported_count, default_set_id))
                
                # 导入设置数据
                settings_file = os.path.join(self.data_dir, 'settings.json')
                if os.path.exists(settings_file):
                    import json
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                        
                        for key, value in settings.items():
                            try:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                                    (key, json.dumps(value))
                                )
                            except Exception as e:
                                log_warning(f"导入设置 {key} 失败: {e}")
                                continue
                
                conn.commit()
                log_info("JSON数据导入成功")
            except Exception as inner_e:
                log_error(f"导入JSON数据时出错: {str(inner_e)}")
                conn.rollback()
            finally:
                conn.close()
        except Exception as e:
            log_error(f"导入JSON数据失败: {str(e)}")
    
    def _start_write_worker(self):
        """启动延迟写入工作线程"""
        import threading
        import time
        
        def write_worker():
            while True:
                time.sleep(1)  # 每秒检查一次
                now = datetime.now()
                
                with self._write_lock:
                    # 如果队列不为空且距离上次写入超过10秒，执行批量写入
                    if (self._write_queue and 
                        (now - self._last_write_time).total_seconds() > 10):
                        self._process_write_queue()
        
        # 启动工作线程
        worker = threading.Thread(target=write_worker, daemon=True)
        worker.start()
    
    # 词库管理相关方法
    def get_all_word_sets(self):
        """获取所有词库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM word_sets ORDER BY name")
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            conn.close()
            return results
        except Exception as e:
            log_error(f"获取词库列表失败: {str(e)}")
            return []
    
    def get_word_set_by_id(self, set_id):
        """根据ID获取词库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM word_sets WHERE id = ?", (set_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            conn.close()
            return dict(zip(columns, row)) if row else None
        except Exception as e:
            log_error(f"获取词库信息失败: {str(e)}")
            return None
    
    def get_word_set_by_name(self, name):
        """根据名称获取词库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM word_sets WHERE name = ?", (name,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            conn.close()
            return dict(zip(columns, row)) if row else None
        except Exception as e:
            log_error(f"根据名称获取词库失败: {str(e)}")
            return None
    
    def create_word_set(self, name, description='', source='user_upload'):
        """创建新的词库"""
        try:
            # 检查词库名是否已存在
            if self.get_word_set_by_name(name):
                return None, "词库名称已存在"
            
            from datetime import datetime
            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO word_sets (name, description, source, create_time, word_count) VALUES (?, ?, ?, ?, ?)",
                (name, description, source, create_time, 0)
            )
            set_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            log_info(f"创建词库成功: {name}")
            return set_id, "创建成功"
        except Exception as e:
            log_error(f"创建词库失败: {str(e)}")
            return None, str(e)
    
    def update_word_set(self, set_id, **kwargs):
        """更新词库信息"""
        try:
            # 检查词库是否存在
            if not self.get_word_set_by_id(set_id):
                return False, "词库不存在"
            
            # 构建更新字段
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'description', 'source', 'word_count']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if fields:
                values.append(set_id)
                sql = f"UPDATE word_sets SET {', '.join(fields)} WHERE id = ?"
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                conn.close()
                
                log_info(f"更新词库成功: {set_id}")
                return True, "更新成功"
            return True, "无更新内容"
        except Exception as e:
            log_error(f"更新词库失败: {str(e)}")
            return False, str(e)
    
    def delete_word_set(self, set_id):
        """删除词库"""
        try:
            # 检查词库是否存在
            if not self.get_word_set_by_id(set_id):
                return False, "词库不存在"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先删除词库中的单词
            cursor.execute("DELETE FROM words WHERE set_id = ?", (set_id,))
            
            # 再删除词库
            cursor.execute("DELETE FROM word_sets WHERE id = ?", (set_id,))
            
            conn.commit()
            conn.close()
            
            log_info(f"删除词库成功: {set_id}")
            return True, "删除成功"
        except Exception as e:
            log_error(f"删除词库失败: {str(e)}")
            return False, str(e)
    
    # 单词管理相关方法（支持词库）
    def get_words_by_set_id(self, set_id, keyword=None, limit=None, offset=None):
        """获取指定词库的单词"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            sql = "SELECT * FROM words WHERE set_id = ?"
            params = [set_id]
            
            if keyword:
                sql += " AND word LIKE ?"
                params.append(f"%{keyword}%")
            
            sql += " ORDER BY word"
            
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    sql += " OFFSET ?"
                    params.append(offset)
            
            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            conn.close()
            return results
        except Exception as e:
            log_error(f"获取词库单词失败: {str(e)}")
            return []
    
    def get_word_by_id(self, word_id):
        """根据ID获取单词"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM words WHERE id = ?", (word_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            conn.close()
            return dict(zip(columns, row)) if row else None
        except Exception as e:
            log_error(f"获取单词信息失败: {str(e)}")
            return None
    
    def add_word_to_set(self, set_id, word, translation, phonetic='', example='', meaning_en='', tag=''):
        """向词库添加单词"""
        try:
            # 检查词库是否存在
            if not self.get_word_set_by_id(set_id):
                return False, "词库不存在"
            
            # 检查词库中是否已存在该单词
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM words WHERE set_id = ? AND word = ?", (set_id, word))
            if cursor.fetchone():
                conn.close()
                return False, "单词已存在于当前词库"
            
            # 添加单词
            cursor.execute(
                "INSERT INTO words (set_id, word, translation, phonetic, example, meaning_en, tag) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (set_id, word, translation, phonetic, example, meaning_en, tag)
            )
            
            # 更新词库单词数
            cursor.execute("UPDATE word_sets SET word_count = word_count + 1 WHERE id = ?", (set_id,))
            
            conn.commit()
            conn.close()
            
            log_info(f"添加单词成功: {word} 到词库 {set_id}")
            return True, "添加成功"
        except Exception as e:
            log_error(f"添加单词失败: {str(e)}")
            return False, str(e)
    
    def update_word(self, word_id, **kwargs):
        """更新单词信息"""
        try:
            # 检查单词是否存在
            word = self.get_word_by_id(word_id)
            if not word:
                return False, "单词不存在"
            
            # 获取数据库中实际存在的列
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(words)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # 构建更新字段，只使用实际存在的列
            fields = []
            values = []
            valid_fields = ['word', 'translation', 'phonetic', 'example', 'meaning_en', 'tag', 'familiarity', 'proficiency', 'example_translation']
            
            for key, value in kwargs.items():
                if key in valid_fields and key in existing_columns:
                    fields.append(f"{key} = ?")
                    values.append(value)
                elif key in valid_fields:
                    # 列不存在时记录日志但不抛出错误
                    log_info(f"跳过更新字段 {key}，该列在数据库中不存在")
            
            if fields:
                values.append(word_id)
                sql = f"UPDATE words SET {', '.join(fields)} WHERE id = ?"
                
                cursor.execute(sql, values)
                conn.commit()
                conn.close()
                
                log_info(f"更新单词成功: {word_id}")
                return True, "更新成功"
            else:
                conn.close()
                return True, "无更新内容或所有字段在数据库中不存在"
        except Exception as e:
            log_error(f"更新单词失败: {str(e)}")
            return False, str(e)
    
    def delete_word(self, word_id):
        """删除单词"""
        try:
            # 获取单词信息以获取set_id
            word = self.get_word_by_id(word_id)
            if not word:
                return False, "单词不存在"
            
            set_id = word['set_id']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除单词
            cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
            
            # 更新词库单词数
            cursor.execute("UPDATE word_sets SET word_count = word_count - 1 WHERE id = ?", (set_id,))
            
            conn.commit()
            conn.close()
            
            log_info(f"删除单词成功: {word_id}")
            return True, "删除成功"
        except Exception as e:
            log_error(f"删除单词失败: {str(e)}")
            return False, str(e)
    
    def _process_write_queue(self):
        """处理写入队列"""
        try:
            if not self._write_queue:
                return
            
            # 在处理队列前记录队列长度
            queue_length = len(self._write_queue)
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            while self._write_queue:
                query, params = self._write_queue.pop(0)
                cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            self._last_write_time = datetime.now()
            log_info(f"批量写入完成，共{queue_length}条记录")
            
        except Exception as e:
            log_error(f"处理写入队列失败: {str(e)}")
    
    def execute_read(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行读取操作
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row  # 返回字典格式
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
            
        except Exception as e:
            log_error(f"执行查询失败: {str(e)}")
            return []
    
    def execute_write(self, query: str, params: tuple = None, immediate: bool = False):
        """执行写操作，会加入写队列延迟执行
        
        Args:
            query: SQL查询语句
            params: 查询参数，需要是元组
            immediate: 是否立即执行，不经过队列
            
        Returns:
            写入操作是否成功
        """
        try:
            if immediate:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                cursor.close()
                conn.close()
                return True
            # 将写操作添加到队列
            with self._write_lock:
                self._write_queue.append((query, params))
            return True
        except Exception as e:
            log_error(f"写入操作加入队列失败: {query}")
            return False
            
    def execute_write_many(self, query: str, param_list: List[tuple]):
        """批量执行写操作
        
        Args:
            query: SQL查询语句
            param_list: 参数列表，每个元素对应一次执行的参数
            
        Returns:
            写入操作是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()

            cursor.executemany(query, param_list)
            conn.commit()

            cursor.close()
            conn.close()
            return True
        except Exception as e:
            log_error(f"批量写入操作失败: {query}, 错误: {str(e)}")
            return False
    
    def get_all_words(self) -> List[str]:
        """获取所有单词"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM words ORDER BY word")
            result = [row[0] for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            log_error(f"获取所有单词失败: {str(e)}")
            return []
    
    def add_word(self, word: str, translation: str) -> bool:
        """添加单词到数据库（兼容旧接口，添加到默认词库）"""
        try:
            # 获取默认词库
            default_set = self.get_word_set_by_name('默认词库')
            if not default_set:
                log_error("默认词库不存在")
                return False
            
            success, msg = self.add_word_to_set(default_set['id'], word, translation)
            return success
        except Exception as e:
            log_error(f"添加单词失败: {str(e)}")
            return False
    
    def get_word_translation(self, word: str) -> Optional[str]:
        """获取单词翻译"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT translation FROM words WHERE word = ?", (word,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            log_error(f"获取单词翻译失败: {str(e)}")
            return None
    
    def update_proficiency(self, word: str, proficiency: float):
        """更新单词熟练度"""
        self.execute_write(
            "UPDATE words SET proficiency = ?, last_practice = CURRENT_TIMESTAMP WHERE word = ?",
            (proficiency, word)
        )
    
    def add_progress_record(self, word: str, is_correct: bool, proficiency_change: float):
        """添加学习进度记录"""
        self.execute_write(
            "INSERT INTO progress (word, is_correct, proficiency_change) VALUES (?, ?, ?)",
            (word, 1 if is_correct else 0, proficiency_change)
        )
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置"""
        results = self.execute_read(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        
        if results:
            import json
            try:
                return json.loads(results[0]['value'])
            except:
                return results[0]['value']
        return default
    
    def set_setting(self, key: str, value: Any):
        """设置配置项"""
        import json
        value_str = json.dumps(value)
        
        self.execute_write(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value_str)
        )
    
    def cache_ai_response(self, prompt: str, response: str):
        """缓存AI响应"""
        prompt_hash = hash(prompt)
        
        self.execute_write(
            """INSERT OR REPLACE INTO ai_cache 
            (prompt_hash, prompt, response, usage_count) 
            VALUES (?, ?, ?, 0)""",
            (prompt_hash, prompt[:1000], response[:5000])  # 限制长度
        )
    
    def get_cached_ai_response(self, prompt: str) -> Optional[str]:
        """获取缓存的AI响应"""
        prompt_hash = hash(prompt)
        
        results = self.execute_read(
            "SELECT response FROM ai_cache WHERE prompt_hash = ?",
            (prompt_hash,)
        )
        
        if results:
            # 更新使用计数
            self.execute_write(
                "UPDATE ai_cache SET usage_count = usage_count + 1 WHERE prompt_hash = ?",
                (prompt_hash,)
            )
            return results[0]['response']
        
        return None
    
    def clean_old_cache(self, days: int = 30):
        """清理过期缓存"""
        self.execute_write(
            "DELETE FROM ai_cache WHERE cached_at < datetime('now', '-? days')",
            (days,)
        )
    
    def get_word_progress(self, word: str) -> Optional[Dict[str, Any]]:
        """获取单词的学习进度
        
        Args:
            word: 单词
            
        Returns:
            单词进度字典或None
        """
        # 查询单词的累计正确次数和总次数
        results = self.execute_read(
            """SELECT 
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                   COUNT(*) as total_count,
                   MAX(practice_date) as last_practice
               FROM progress 
               WHERE word = ?""",
            (word,)
        )
        
        if results and results[0]['total_count'] > 0:
            row = results[0]
            # 计算熟练度
            proficiency = row['correct_count'] / row['total_count']
            
            return {
                'word': word,
                'correct_count': row['correct_count'],
                'total_count': row['total_count'],
                'proficiency': proficiency,
                'last_practice': row['last_practice']
            }
        
        return None
    
    def create_dictation_tables(self):
        """创建听写相关的表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 启用外键约束
            cursor.execute('PRAGMA foreign_keys = ON')
            
            # 创建听写历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dictation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    user_input TEXT,
                    is_correct INTEGER NOT NULL DEFAULT 0,
                    similarity FLOAT DEFAULT 0.0,
                    practice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dictation_word ON dictation_history(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dictation_date ON dictation_history(practice_date)')
            
            conn.commit()
            conn.close()
            log_info("听写相关表结构创建/更新成功")
            
        except Exception as e:
            log_error(f"创建听写表结构失败: {str(e)}")
            raise
            
    def remove_word(self, word: str) -> bool:
        """从数据库中删除单词
        
        Args:
            word: 要删除的单词
            
        Returns:
            是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 开始事务
            conn.execute('BEGIN TRANSACTION')
            
            # 删除相关的进度记录
            cursor.execute("DELETE FROM progress WHERE word = ?", (word,))
            
            # 删除听写历史记录
            cursor.execute("DELETE FROM dictation_history WHERE word = ?", (word,))
            
            # 删除单词本身
            cursor.execute("DELETE FROM words WHERE word = ?", (word,))
            affected_rows = cursor.rowcount
            
            # 提交事务
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                log_info(f"删除单词成功: {word}")
                return True
            else:
                log_info(f"单词不存在: {word}")
                return False
                
        except Exception as e:
            log_error(f"删除单词失败: {str(e)}")
            return False
    
    def update_word_translation(self, word: str, translation: str) -> bool:
        """更新单词的翻译
        
        Args:
            word: 要更新的单词
            translation: 新的翻译
            
        Returns:
            是否更新成功
        """
        try:
            self.execute_write(
                "UPDATE words SET translation = ? WHERE word = ?",
                (translation, word)
            )
            
            # 检查是否有行被更新
            results = self.execute_read(
                "SELECT COUNT(*) as count FROM words WHERE word = ?",
                (word,)
            )
            
            if results and results[0]['count'] > 0:
                log_info(f"更新单词成功: {word} -> {translation}")
                return True
            else:
                log_info(f"单词不存在: {word}")
                return False
                
        except Exception as e:
            log_error(f"更新单词失败: {str(e)}")
            return False
    
    def create_exercise_sessions_table(self):
        """创建练习会话表（如果不存在）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercise_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exercise_type TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    source TEXT NOT NULL,
                    difficulty TEXT,
                    batch_size INTEGER,
                    total_words INTEGER,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    correct_words INTEGER,
                    accuracy REAL
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_type ON exercise_sessions(exercise_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_start ON exercise_sessions(start_time)')
            
            conn.commit()
            log_info("练习会话表创建成功")
        except Exception as e:
            log_error(f"创建练习会话表失败: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()