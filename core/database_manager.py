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
            
            # 创建单词表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    translation TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_practice TIMESTAMP,
                    last_review TIMESTAMP,
                    proficiency FLOAT DEFAULT 0.0
                )
            ''')
            
            # 创建单词索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_proficiency ON words(proficiency)')
            
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
            
            # 从JSON导入现有数据
            self._import_from_json()
            
            conn.commit()
            conn.close()
            log_info("数据库初始化成功")
            
        except Exception as e:
            log_error(f"初始化数据库失败: {str(e)}")
    
    def _import_from_json(self):
        """从旧的JSON文件导入数据到SQLite"""
        try:
            # 检查是否已经导入过
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM words")
            count = cursor.fetchone()[0]
            
            # 如果已经有数据，跳过导入
            if count > 0:
                conn.close()
                return
            
            # 导入单词数据
            word_dict_file = os.path.join(self.data_dir, 'word_dict.json')
            if os.path.exists(word_dict_file):
                import json
                with open(word_dict_file, 'r', encoding='utf-8') as f:
                    word_dict = json.load(f)
                    
                    for word, translation in word_dict.items():
                        cursor.execute(
                            "INSERT OR IGNORE INTO words (word, translation) VALUES (?, ?)",
                            (word, translation)
                        )
            
            # 导入设置数据
            settings_file = os.path.join(self.data_dir, 'settings.json')
            if os.path.exists(settings_file):
                import json
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    for key, value in settings.items():
                        cursor.execute(
                            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                            (key, json.dumps(value))
                        )
            
            conn.commit()
            log_info("数据从JSON导入成功")
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
    
    def _process_write_queue(self):
        """处理写入队列"""
        try:
            if not self._write_queue:
                return
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            while self._write_queue:
                query, params = self._write_queue.pop(0)
                cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            self._last_write_time = datetime.now()
            log_info(f"批量写入完成，共{len(self._write_queue)}条记录")
            
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
        results = self.execute_read("SELECT word FROM words")
        return [row['word'] for row in results]
    
    def add_word(self, word: str, translation: str):
        """添加单词"""
        self.execute_write(
            "INSERT OR IGNORE INTO words (word, translation) VALUES (?, ?)",
            (word, translation)
        )
    
    def get_word_translation(self, word: str) -> Optional[str]:
        """获取单词翻译"""
        results = self.execute_read(
            "SELECT translation FROM words WHERE word = ?",
            (word,)
        )
        return results[0]['translation'] if results else None
    
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
    
    def update_word(self, word: str, translation: str) -> bool:
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
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_type ON exercise_sessions(exercise_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_start ON exercise_sessions(start_time)')
            
            conn.commit()
            conn.close()
            log_info("练习会话表创建成功")
            
        except Exception as e:
            log_error(f"创建练习会话表失败: {str(e)}")