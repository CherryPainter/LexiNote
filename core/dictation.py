import random
import asyncio
import threading
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from logger import log_info, log_error, log_warning, log_wrong_word, log_exercise_start


class DictationManager:
    """优化版听写管理器，负责听写练习的核心逻辑，支持异步操作"""
    
    def __init__(self, word_manager, settings_manager=None):
        """初始化听写管理器
        
        Args:
            word_manager: 单词管理器实例
            settings_manager: 设置管理器实例
        """
        self.word_manager = word_manager
        self.db_manager = word_manager.db_manager  # 使用单词管理器的数据库连接
        self.settings_manager = settings_manager
        self.current_words = []  # 当前听写的单词列表
        self.completed_words = []  # 已完成的单词
        self.current_queue = []  # 当前队列
        self.current_queue_index = 0  # 当前队列索引
        self.current_index = 0  # 当前单词索引
        self.score = 0  # 得分
        self.start_time = None  # 开始时间
        self.duration = 0  # 持续时间
        self.current_mode = None  # 当前模式（single/queue）
        self.current_source = None  # 当前单词来源
        
        # 当前会话信息
        self.current_session = None
        self.session_results = []
        
        # 用户设置
        self.settings = {
            'auto_play': True,
            'play_interval': 3000,
            'difficulty_level': 'medium',
            'daily_target': 20,
            'review_frequency': 3
        }
        
        # 线程安全锁
        self._cache_lock = threading.RLock()
        
        # 缓存
        self._today_words_cache = {}
        self._today_words_cache_time = None
        
        # 迁移数据（如果存在旧的JSON文件）
        self._migrate_old_data()
        
        # 初始化设置
        self._init_settings()
        
        # 初始化数据库表
        self._init_database()
        
    def _migrate_old_data(self):
        """迁移旧的JSON数据到数据库"""
        try:
            # 检查是否需要迁移
            import os
            
            # 迁移单词数据（如果存在）
            if os.path.exists('data/word_dict.json'):
                log_info("发现旧的单词数据，开始迁移...")
                import json
                try:
                    with open('data/word_dict.json', 'r', encoding='utf-8') as f:
                        word_dict = json.load(f)
                    
                    # 批量插入单词到默认词库
                    default_set_id = self.db_manager.get_word_set_by_name('默认词库')
                    if default_set_id:
                        default_set_id = default_set_id['id']
                        word_data = [(default_set_id, word, translation) for word, translation in word_dict.items()]
                        if word_data:
                            self.db_manager.execute_write_many(
                                "INSERT OR IGNORE INTO words (set_id, word, translation) VALUES (?, ?, ?)",
                                word_data
                            )
                    
                    log_info(f"成功迁移 {len(word_dict)} 个单词到数据库")
                except Exception as e:
                    log_warning(f"迁移单词数据失败: {str(e)}")
            
            # 迁移学习进度数据（如果存在）
            if os.path.exists('data/word_progress.json'):
                log_info("发现旧的学习进度数据，开始迁移...")
                try:
                    import json
                    with open('data/word_progress.json', 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    # 批量更新熟练度
                    update_data = []
                    for word, progress in progress_data.items():
                        if isinstance(progress, dict):
                            # 计算熟练度
                            correct_count = progress.get('correct', 0)
                            total_count = progress.get('total', 1)
                            proficiency = min(1.0, correct_count / total_count)
                            update_data.append((proficiency, word))
                    
                    if update_data:
                        self.db_manager.execute_write_many(
                            "UPDATE words SET proficiency = ? WHERE word = ?",
                            update_data
                        )
                    
                    log_info(f"成功迁移学习进度数据到数据库")
                except Exception as e:
                    log_warning(f"迁移学习进度数据失败: {str(e)}")
            
            log_info("数据迁移完成")
            
        except Exception as e:
            log_error(f"迁移数据时发生错误: {str(e)}")
    
    def _init_settings(self):
        """初始化用户设置"""
        try:
            # 默认设置
            default_settings = {
                'auto_play_pronunciation': True,
                'show_example_sentence': True,
                'enable_auto_mode': False,
                'auto_mode_delay': 3,
                'show_phonetic': True,
                'pronunciation_speed': 1.0,
                'difficulty_level': 'medium',  # easy, medium, hard
                'auto_play': True,  # 保持向后兼容
                'play_interval': 3000,  # 保持向后兼容
                'daily_target': 20,
                'review_frequency': 3
            }
            
            # 更新默认设置
            self.settings.update(default_settings)
            
            if self.settings_manager:
                # 从设置管理器获取设置
                self.settings['auto_play_pronunciation'] = self.settings_manager.get_setting('dictation_auto_play_pronunciation', True)
                self.settings['show_example_sentence'] = self.settings_manager.get_setting('dictation_show_example', True)
                self.settings['enable_auto_mode'] = self.settings_manager.get_setting('dictation_auto_mode', False)
                self.settings['auto_mode_delay'] = self.settings_manager.get_setting('dictation_auto_delay', 3)
                self.settings['show_phonetic'] = self.settings_manager.get_setting('dictation_show_phonetic', True)
                self.settings['pronunciation_speed'] = self.settings_manager.get_setting('dictation_pronunciation_speed', 1.0)
                self.settings['difficulty_level'] = self.settings_manager.get_setting('dictation_difficulty', 'medium')
                self.settings['auto_play'] = self.settings_manager.get_setting('dictation_auto_play', True)  # 保持向后兼容
                self.settings['play_interval'] = self.settings_manager.get_setting('dictation_play_interval', 3000)  # 保持向后兼容
                self.settings['daily_target'] = self.settings_manager.get_setting('dictation_daily_target', 20)
                self.settings['review_frequency'] = self.settings_manager.get_setting('dictation_review_frequency', 3)
        except Exception as e:
            log_error(f"初始化设置失败: {str(e)}")
    
    def _init_database(self):
        """初始化数据库表，添加必要的列"""
        try:
            # 检查并添加session_id列到dictation_history表
            conn = self.db_manager.execute_read("PRAGMA table_info(dictation_history)")
            columns = [col['name'] for col in conn]
            
            if 'session_id' not in columns:
                self.db_manager.execute_write("ALTER TABLE dictation_history ADD COLUMN session_id INTEGER REFERENCES exercise_sessions(id)")
            
            # 检查并添加列到exercise_sessions表
            conn = self.db_manager.execute_read("PRAGMA table_info(exercise_sessions)")
            columns = [col['name'] for col in conn]
            
            if 'duration' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN duration INTEGER")
            if 'total_words' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN total_words INTEGER")
            if 'correct_words' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN correct_words INTEGER")
            if 'accuracy' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN accuracy FLOAT")
            if 'source' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN source TEXT")
            if 'mode' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN mode TEXT")
            if 'difficulty' not in columns:
                self.db_manager.execute_write("ALTER TABLE exercise_sessions ADD COLUMN difficulty TEXT")
            
            # 创建dictation_settings表（如果不存在）
            self.db_manager.execute_write("""
                CREATE TABLE IF NOT EXISTS dictation_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    auto_play BOOLEAN DEFAULT 1,
                    play_interval INTEGER DEFAULT 3000,
                    difficulty_level TEXT DEFAULT 'medium',
                    daily_target INTEGER DEFAULT 20,
                    review_frequency INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
        except Exception as e:
            log_error(f"初始化数据库表失败: {str(e)}")
    
    def start_session(self, mode: str, source: str, batch_size: int = 10, difficulty: str = None):
        """开始新的练习会话
        
        Args:
            mode: 练习模式（single/queue）
            source: 单词来源（today/library/familiar）
            batch_size: 批量大小
            difficulty: 难度级别，可选值："easy", "medium", "hard"
            
        Returns:
            会话ID
        """
        try:
            # 结束当前会话（如果存在）
            if self.current_session:
                self.end_session()
            
            # 记录开始时间
            self.start_time = datetime.now()
            self.current_mode = mode
            self.current_source = source
            
            # 使用当前设置的难度级别（如果未提供）
            if difficulty is None:
                difficulty = self.settings['difficulty_level']
            
            # 插入会话记录
            session_id = self.db_manager.execute_write(
                "INSERT INTO exercise_sessions (exercise_type, start_time, mode, source, difficulty) VALUES (?, ?, ?, ?, ?)",
                ('dictation', self.start_time.isoformat(), mode, source, difficulty)
            )
            
            # 选择单词
            if mode == 'queue':
                self.current_queue = self.build_queue(source, batch_size, difficulty=difficulty)
                self.current_queue_index = 0
            else:
                self.current_words = []
                self.current_index = 0
            
            # 初始化会话信息
            self.current_session = {
                'id': session_id,
                'mode': mode,
                'source': source,
                'difficulty': difficulty,
                'start_time': self.start_time,
                'batch_size': batch_size,
                'total_words': batch_size if mode == 'queue' else 0
            }
            
            # 清空结果
            self.session_results = []
            self.score = 0
            
            log_info(f"开始新的听写会话: ID={session_id}, 模式={mode}, 来源={source}")
            
            return session_id
            
        except Exception as e:
            log_error(f"开始会话失败: {str(e)}")
            return None
    
    def end_session(self):
        """结束当前练习会话并保存统计信息
        
        Returns:
            会话统计信息字典
        """
        try:
            if not self.current_session:
                return None
            
            # 计算会话统计信息
            end_time = datetime.now()
            duration = int((end_time - self.start_time).total_seconds())
            total_words = len(self.session_results)
            correct_words = sum(1 for result in self.session_results if result['is_correct'])
            accuracy = correct_words / total_words if total_words > 0 else 0.0
            
            # 更新会话记录
            self.db_manager.execute_write(
                "UPDATE exercise_sessions SET end_time = ?, duration = ?, total_words = ?, correct_words = ?, accuracy = ?, difficulty = ? WHERE id = ?",
                (end_time.isoformat(), duration, total_words, correct_words, accuracy, 
                 self.current_session.get('difficulty', 'medium'), self.current_session['id'])
            )
            
            # 记录日志
            log_info(f"会话结束: ID={self.current_session['id']}, 时长={duration}秒, 单词数={total_words}, 正确率={accuracy:.2f}")
            
            # 保存统计信息以便返回
            stats = {
                'session_id': self.current_session['id'],
                'duration': duration,
                'total_words': total_words,
                'correct_words': correct_words,
                'accuracy': accuracy
            }
            
            # 重置会话信息
            self.current_session = None
            self.session_results = []
            self.start_time = None
            self.duration = duration
            
            return stats
        except Exception as e:
            log_error(f"结束会话失败: {str(e)}")
            return None
    
    def get_current_session(self):
        """获取当前会话信息
        
        Returns:
            当前会话信息字典
        """
        return self.current_session
    
    def get_stats(self, days: int = 7):
        """获取详细的统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取当前激活词库ID
            active_set_id = self.word_manager.active_word_set_id if hasattr(self.word_manager, 'active_word_set_id') else None
            
            # 计算开始日期
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 构建基础查询
            base_query = "practice_date >= ?"
            params = [start_date]
            
            # 如果有激活词库，添加词库过滤
            if active_set_id:
                base_query += " AND word IN (SELECT word FROM words WHERE set_id = ?)"
                params.append(active_set_id)
            
            # 查询总练习次数
            total_query = f"SELECT COUNT(*) as count FROM dictation_history WHERE {base_query}"
            total_practices = self.db_manager.execute_read(total_query, params)[0]['count']
            
            # 查询正确次数
            correct_query = f"SELECT COUNT(*) as count FROM dictation_history WHERE {base_query} AND is_correct = 1"
            correct_practices = self.db_manager.execute_read(correct_query, params)[0]['count']
            
            # 查询练习的单词数
            unique_query = f"SELECT COUNT(DISTINCT word) as count FROM dictation_history WHERE {base_query}"
            unique_words = self.db_manager.execute_read(unique_query, params)[0]['count']
            
            # 查询最常错的单词
            wrong_words_query = f"""
            SELECT word, 
                    SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong_count 
               FROM dictation_history 
               WHERE {base_query} 
               GROUP BY word 
               ORDER BY wrong_count DESC 
               LIMIT 5
            """
            most_wrong_words = self.db_manager.execute_read(wrong_words_query, params)
            
            # 查询每日统计
            daily_stats_query = f"""
            SELECT DATE(practice_date) as date, 
                    COUNT(*) as total, 
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct 
               FROM dictation_history 
               WHERE {base_query} 
               GROUP BY DATE(practice_date)
               ORDER BY date
            """
            daily_stats = self.db_manager.execute_read(daily_stats_query, params)
            
            # 查询会话统计
            session_stats_query = f"""
            SELECT id, mode, source, start_time, duration, total_words, accuracy 
               FROM exercise_sessions 
               WHERE start_time >= ? AND exercise_type = 'dictation' 
               ORDER BY start_time DESC 
               LIMIT 10
            """
            session_stats = self.db_manager.execute_read(session_stats_query, [start_date])
            
            # 计算每日目标完成情况
            today = datetime.now().strftime('%Y-%m-%d')
            today_query = "SELECT COUNT(*) as count FROM dictation_history WHERE DATE(practice_date) = ?"
            today_practices = self.db_manager.execute_read(today_query, [today])[0]['count']
            daily_target = self.settings['daily_target']
            target_progress = min(100, (today_practices / daily_target) * 100) if daily_target > 0 else 0
            
            return {
                'total_practices': total_practices,
                'correct_practices': correct_practices,
                'accuracy': correct_practices / total_practices if total_practices > 0 else 0.0,
                'unique_words': unique_words,
                'most_wrong_words': most_wrong_words,
                'daily_stats': daily_stats,
                'session_stats': session_stats,
                'today_practices': today_practices,
                'daily_target': daily_target,
                'target_progress': target_progress
            }
            
        except Exception as e:
            log_error(f"获取统计信息失败: {str(e)}")
            return {}
    
    def get_daily_progress(self):
        """获取今日学习进度
        
        Returns:
            今日学习进度字典
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 查询今日练习次数
            total_query = "SELECT COUNT(*) as count FROM dictation_history WHERE DATE(practice_date) = ?"
            total_practices = self.db_manager.execute_read(total_query, [today])[0]['count']
            
            # 查询今日正确次数
            correct_query = "SELECT COUNT(*) as count FROM dictation_history WHERE DATE(practice_date) = ? AND is_correct = 1"
            correct_practices = self.db_manager.execute_read(correct_query, [today])[0]['count']
            
            # 查询今日学习的单词数
            unique_query = "SELECT COUNT(DISTINCT word) as count FROM dictation_history WHERE DATE(practice_date) = ?"
            unique_words = self.db_manager.execute_read(unique_query, [today])[0]['count']
            
            daily_target = self.settings['daily_target']
            target_progress = min(100, (total_practices / daily_target) * 100) if daily_target > 0 else 0
            
            return {
                'today': today,
                'total_practices': total_practices,
                'correct_practices': correct_practices,
                'accuracy': correct_practices / total_practices if total_practices > 0 else 0.0,
                'unique_words': unique_words,
                'daily_target': daily_target,
                'target_progress': target_progress
            }
            
        except Exception as e:
            log_error(f"获取今日进度失败: {str(e)}")
            return {}
    
    def record_result(self, word: str, user_input: str, is_correct: bool, similarity: float = 0.0):
        """记录听写结果（增强版）
        
        Args:
            word: 单词
            user_input: 用户输入
            is_correct: 是否正确
            similarity: 相似度（0-1）
        """
        try:
            # 优先使用数据库
            if self.db_manager:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                is_correct_int = 1 if is_correct else 0
                
                # 如果未提供相似度，简单比较计算
                if similarity == 0.0 and user_input and word:
                    similarity = 1.0 if user_input == word else 0.0
                
                # 获取会话ID
                session_id = self.current_session['id'] if self.current_session else None
                
                # 1. 插入听写历史记录
                self.db_manager.execute_write(
                    """INSERT INTO dictation_history (word, user_input, is_correct, similarity, practice_date, session_id) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (word, user_input, is_correct_int, similarity, timestamp, session_id)
                )
                
                # 2. 记录到 progress 表（按行记录 is_correct），之后通过聚合查询计算熟练度
                proficiency_change = 0.1 if is_correct else -0.15
                try:
                    self.db_manager.add_progress_record(word, is_correct, proficiency_change)
                except Exception:
                    # 如果add_progress_record不可用，则回退为直接插入单条记录
                    self.db_manager.execute_write(
                        "INSERT INTO progress (word, is_correct, proficiency_change, practice_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                        (word, is_correct_int, proficiency_change)
                    )
                
                # 更新单词熟练度
                try:
                    # 尝试使用数据库管理器的方法
                    wp = self.db_manager.get_word_progress(word)
                    if wp and 'proficiency' in wp:
                        self.db_manager.update_proficiency(word, wp['proficiency'])
                    else:
                        # 如果无法获取聚合数据，直接更新
                        current_proficiency = 0.0
                        try:
                            # 获取当前熟练度
                            res = self.db_manager.execute_read(
                                "SELECT proficiency FROM words WHERE word = ?",
                                (word,)
                            )
                            if res:
                                current_proficiency = res[0]['proficiency'] if res[0]['proficiency'] is not None else 0.0
                        except Exception:
                            pass
                        
                        # 计算新熟练度
                        new_proficiency = max(0.0, min(1.0, current_proficiency + proficiency_change))
                        
                        # 更新单词熟练度和最后复习时间
                        self.db_manager.execute_write(
                            "UPDATE words SET proficiency = ?, last_review = CURRENT_TIMESTAMP WHERE word = ?",
                            (new_proficiency, word)
                        )
                except Exception as e:
                    log_error(f"更新单词熟练度失败: {str(e)}")
                
                # 3. 添加到会话结果
                result = {
                    'word': word,
                    'user_input': user_input,
                    'is_correct': is_correct,
                    'similarity': similarity,
                    'timestamp': timestamp
                }
                self.session_results.append(result)
                
                # 4. 更新得分
                if is_correct:
                    self.score += 1
                
                log_info(f"记录听写结果: {word} - {'正确' if is_correct else '错误'}")
            
        except Exception as e:
            log_error(f"记录听写结果失败: {str(e)}")
    
    def select_word(self, source="library"):
        """选择一个单词用于单个听写模式（同步版本），优先返回带本地例句的单词
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            
        Returns:
            选中的单词字符串或None
        """
        try:
            # 记录练习开始
            log_exercise_start(f"听写练习开始，来源: {source}", 1)
            
            # 获取当前激活词库ID
            active_set_id = self.word_manager.active_word_set_id if hasattr(self.word_manager, 'active_word_set_id') else None
            
            if source == "today":
                # 优先选择有例句的今日单词
                today_words_with_example = self._get_today_learned_words(with_example=True)
                if today_words_with_example:
                    selected = random.choice(today_words_with_example)
                    log_info(f"从今日学习单词(带例句)中选择: {selected}")
                    return selected
                
                # 没有带例句的今日单词，尝试普通今日单词
                today_words = self._get_today_learned_words()
                if today_words:
                    selected = random.choice(today_words)
                    log_info(f"从今日学习单词中选择: {selected}")
                    # 异步获取并保存例句
                    self._fetch_and_save_example_async(selected)
                    return selected
                log_info("没有今日学习的单词，返回 None")
                return None
                
            if source == "familiar":
                # 优先从有例句的熟词库中选择
                query = """
                SELECT word FROM words 
                WHERE proficiency > 0.8 
                AND example IS NOT NULL AND example != ''
                AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                ORDER BY RANDOM() LIMIT 1
                """
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                
                familiar_words = self.db_manager.execute_read(query, params)
                if familiar_words:
                    selected = familiar_words[0]['word']
                    log_info(f"从熟词库(带例句)中选择: {selected}")
                    return selected
                
                # 回退到没有例句的熟词
                familiar_words = self.db_manager.execute_read(
                    """
                    SELECT word FROM words 
                    WHERE proficiency > 0.8 
                    AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    ORDER BY RANDOM() LIMIT 1
                    """
                )
                if familiar_words:
                    selected = familiar_words[0]['word']
                    log_info(f"从熟词库中选择: {selected}")
                    # 异步获取并保存例句
                    self._fetch_and_save_example_async(selected)
                    return selected
                
                log_info("没有符合条件的熟词，返回 None")
                return None
                
            # 默认使用词库选择
            if source == "library":
                # 优先从当前激活词库选择带例句的单词
                # 优先选择有例句且最近错误率高的单词
                query = """
                SELECT word FROM words 
                WHERE proficiency < 0.5 
                AND example IS NOT NULL AND example != ''
                AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                """
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                    
                query += " ORDER BY RANDOM() * (1.0 - COALESCE(proficiency, 0)) DESC LIMIT 1"
                
                word = self.db_manager.execute_read(query, params)
                if word:
                    selected = word[0]['word']
                    log_info(f"从词库中选择带例句的困难单词: {selected}")
                    return selected
                    
                # 如果没有合适的带例句单词，尝试普通困难单词
                query = """
                SELECT word FROM words 
                WHERE proficiency < 0.5 
                AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                """
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                    
                query += " ORDER BY RANDOM() * (1.0 - COALESCE(proficiency, 0)) DESC LIMIT 1"
                
                word = self.db_manager.execute_read(query, params)
                if word:
                    selected = word[0]['word']
                    log_info(f"从词库中选择困难单词: {selected}")
                    # 异步获取并保存例句
                    self._fetch_and_save_example_async(selected)
                    return selected
                    
                # 如果没有困难单词，尝试很久没复习且有例句的单词
                query = """
                SELECT word FROM words 
                WHERE (last_review IS NULL 
                OR last_review < datetime('now', '-7 days'))
                AND example IS NOT NULL AND example != ''
                """
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                    
                query += " ORDER BY last_review ASC, RANDOM() LIMIT 1"
                
                word = self.db_manager.execute_read(query, params)
                if word:
                    selected = word[0]['word']
                    log_info(f"从词库中选择带例句的未复习单词: {selected}")
                    return selected
                    
                # 如果没有带例句的未复习单词，尝试普通未复习单词
                query = """
                SELECT word FROM words 
                WHERE (last_review IS NULL 
                OR last_review < datetime('now', '-7 days'))
                """
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                    
                query += " ORDER BY last_review ASC, RANDOM() LIMIT 1"
                
                word = self.db_manager.execute_read(query, params)
                if word:
                    selected = word[0]['word']
                    log_info(f"从词库中选择未复习单词: {selected}")
                    # 异步获取并保存例句
                    self._fetch_and_save_example_async(selected)
                    return selected
                    
                # 最后的备选：完全随机选择带例句的单词
                query = "SELECT word FROM words WHERE example IS NOT NULL AND example != ''"
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                    
                query += " ORDER BY RANDOM() LIMIT 1"
                
                word = self.db_manager.execute_read(query, params)
                if word:
                    selected = word[0]['word']
                    log_info(f"从词库中随机选择带例句单词: {selected}")
                    return selected
                    
                # 最后的备选：完全随机选择
                query = "SELECT word FROM words"
                params = []
                
                if active_set_id:
                    query += " WHERE set_id = ?"
                    params.append(active_set_id)
                    
                query += " ORDER BY RANDOM() LIMIT 1"
                
                word = self.db_manager.execute_read(query, params)
                if word:
                    selected = word[0]['word']
                    log_info(f"从词库中随机选择: {selected}")
                    # 异步获取并保存例句
                    self._fetch_and_save_example_async(selected)
                    return selected
                    
                log_error(f"无法从来源 {source} 选择单词，返回 None")
            return None
            
        except Exception as e:
            log_error(f"选择单词时发生错误: {str(e)}")
            return None
            
    def _fetch_and_save_example_async(self, word):
        """异步获取并保存单词例句
        
        Args:
            word: 单词
        """
        def _fetch_task():
            try:
                # 检查AI功能是否可用
                if hasattr(self.word_manager, 'ai_available') and self.word_manager.ai_available:
                    if hasattr(self.word_manager, 'ai_manager') and hasattr(self.word_manager.ai_manager, 'get_example_sentence'):
                        # 调用AI获取例句
                        example = self.word_manager.ai_manager.get_example_sentence(word)
                        if example:
                            # 保存到数据库
                            self.save_word_example(word, example)
                            log_info(f"为单词 {word} 异步获取并保存例句")
            except Exception as e:
                log_error(f"异步获取例句失败: {str(e)}")
        
        # 在新线程中执行，避免阻塞
        thread = threading.Thread(target=_fetch_task, daemon=True)
        thread.start()
    
    async def select_word_async(self, source="library"):
        """异步选择一个单词用于单个听写模式
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            
        Returns:
            选中的单词字符串
        """
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            return await loop.run_in_executor(
                executor,
                self.select_word,
                source
            )
        finally:
            executor.shutdown(wait=False)
    
    async def fetch_and_save_example_async(self, word):
        """基于asyncio的异步方法，获取并保存单词例句
        
        Args:
            word: 单词
            
        Returns:
            bool: 是否成功获取并保存例句
        """
        try:
            # 检查AI功能是否可用
            if hasattr(self.word_manager, 'ai_available') and self.word_manager.ai_available:
                # 在线程池中执行AI调用，避免阻塞事件循环
                loop = asyncio.get_event_loop()
                executor = ThreadPoolExecutor(max_workers=1)
                
                try:
                    # 使用AI获取例句
                    if hasattr(self.word_manager, 'ai_manager'):
                        ai_manager = self.word_manager.ai_manager
                        
                        # 尝试不同的方法名获取例句
                        example = None
                        if hasattr(ai_manager, 'get_example_sentence'):
                            example = await loop.run_in_executor(
                                executor,
                                ai_manager.get_example_sentence,
                                word
                            )
                        elif hasattr(ai_manager, 'get_word_example'):
                            example = await loop.run_in_executor(
                                executor,
                                ai_manager.get_word_example,
                                word
                            )
                        
                        # 如果获取到例句，保存到数据库
                        if example:
                            # 保存例句到数据库也在线程池中执行
                            save_result = await loop.run_in_executor(
                                executor,
                                self.save_word_example,
                                word,
                                example
                            )
                            if save_result:
                                log_info(f"通过AI异步获取并保存例句成功: {word}")
                                return True
                            else:
                                log_warning(f"例句保存失败: {word}")
                        else:
                            log_warning(f"AI未能获取例句: {word}")
                finally:
                    executor.shutdown(wait=False)
            return False
        except Exception as e:
            log_error(f"基于asyncio的异步获取例句失败: {str(e)}")
            return False
    
    def build_queue(self, source="today", limit=10, filter_familiar=False, difficulty=None):
        """构建听写队列（同步版本）
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            limit: 队列大小限制
            filter_familiar: 是否只包含熟词
            difficulty: 难度级别，可选值："easy", "medium", "hard"
            
        Returns:
            单词列表
        """
        try:
            # 记录练习开始
            log_exercise_start("queue", limit)
            
            words = []
            # 获取当前激活词库ID
            active_set_id = self.word_manager.active_word_set_id if hasattr(self.word_manager, 'active_word_set_id') else None
            
            if source == "today":
                # 获取今日学习单词
                words = self._get_today_learned_words()
                if not words:
                    log_info("没有今日学习的单词，返回空队列")
                    return []
                
                # 限制数量并打乱顺序
                words = words[:limit]
                random.shuffle(words)
            
            elif source == "familiar" or (filter_familiar and source != "today"):
                # 从熟词库中选择
                query = """
                SELECT word FROM words 
                WHERE proficiency > 0.8 
                AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                """
                params = []
                
                if active_set_id:
                    query += " AND set_id = ?"
                    params.append(active_set_id)
                
                query += (" ORDER BY "
                    " CASE "
                    " WHEN last_review IS NULL THEN 1 "
                    " ELSE 0 "
                    " END DESC,"
                    " last_review ASC,"
                    " RANDOM()"
                    " LIMIT ?")
                params.append(limit)
                
                results = self.db_manager.execute_read(query, params)
                words = [row['word'] for row in results]
                
                if not words:
                    log_info("没有符合条件的熟词，返回空队列")
                    return []
            
            elif source == "library":
                # 获取难度设置，默认使用当前设置
                if difficulty is None:
                    difficulty = self.settings['difficulty_level']
                
                # 根据难度调整选择策略
                if difficulty == "easy":
                    # 简单模式：主要选择熟练程度较高的单词
                    query = """
                    SELECT word FROM words 
                    WHERE proficiency >= 0.6
                    AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    """
                    params = []
                    
                    if active_set_id:
                        query += " AND set_id = ?"
                        params.append(active_set_id)
                    
                    query += (" ORDER BY "
                        " RANDOM() * COALESCE(proficiency, 0) DESC "
                        " LIMIT ?")
                    params.append(limit)
                    
                    results = self.db_manager.execute_read(query, params)
                    words = [row['word'] for row in results]
                    
                elif difficulty == "hard":
                    # 困难模式：主要选择熟练程度较低的单词和易错单词
                    query = """
                    SELECT word FROM words 
                    WHERE proficiency < 0.4
                    AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    """
                    params = []
                    
                    if active_set_id:
                        query += " AND set_id = ?"
                        params.append(active_set_id)
                    
                    query += (" ORDER BY "
                        " RANDOM() * (1.0 - COALESCE(proficiency, 0)) DESC "
                        " LIMIT ?")
                    params.append(limit)
                    
                    results = self.db_manager.execute_read(query, params)
                    words = [row['word'] for row in results]
                    
                    # 如果不够，添加最近错误的单词
                    if len(words) < limit:
                        remaining = limit - len(words)
                        wrong_query = """
                        SELECT word FROM dictation_history 
                        WHERE is_correct = 0 
                        AND practice_date > datetime('now', '-30 days')
                        GROUP BY word 
                        ORDER BY COUNT(*) DESC, practice_date DESC 
                        LIMIT ?
                        """
                        wrong_results = self.db_manager.execute_read(wrong_query, [remaining])
                        wrong_words = [row['word'] for row in wrong_results]
                        words.extend(wrong_words)
                
                else:  # medium 模式（默认）
                    # 智能选择策略：
                    # 1. 40% 最近错误率高的单词
                    difficult_limit = int(limit * 0.4)
                    query = """
                    SELECT word FROM words 
                    WHERE proficiency < 0.5
                    AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    """
                    params = []
                    
                    if active_set_id:
                        query += " AND set_id = ?"
                        params.append(active_set_id)
                    
                    query += (" ORDER BY "
                        " RANDOM() * (1.0 - COALESCE(proficiency, 0)) DESC "
                        " LIMIT ?")
                    params.append(difficult_limit)
                    
                    difficult_words = self.db_manager.execute_read(query, params)
                    words.extend([row['word'] for row in difficult_words])
                    
                    # 2. 30% 很久没复习的单词
                    old_limit = int(limit * 0.3)
                    if old_limit > 0:
                        subquery = """
                        SELECT DISTINCT word 
                        FROM dictation_history 
                        WHERE practice_date > datetime('now', '-7 days')
                        """
                        
                        if words:
                            subquery += f" OR word IN ({','.join(['?'] * len(words))})"
                            subquery_params = words.copy()
                        else:
                            subquery_params = []
                        
                        query = """
                        SELECT word FROM words 
                        WHERE word NOT IN (SELECT word FROM dictation_history WHERE practice_date > datetime('now', '-7 days'))
                        """
                        params = []
                        
                        if active_set_id:
                            query += " AND set_id = ?"
                            params.append(active_set_id)
                        
                        query += " ORDER BY last_review ASC, RANDOM() LIMIT ?"
                        params.append(old_limit)
                        
                        old_words = self.db_manager.execute_read(query, params)
                        words.extend([row['word'] for row in old_words])
                    
                    # 3. 剩余位置随机选择
                    remaining_limit = limit - len(words)
                    if remaining_limit > 0:
                        query = "SELECT word FROM words"
                        params = []
                        
                        if active_set_id:
                            query += " WHERE set_id = ?"
                            params.append(active_set_id)
                        
                        if words:
                            if active_set_id:
                                query += " AND"
                            else:
                                query += " WHERE"
                            query += f" word NOT IN ({','.join(['?'] * len(words))})"
                            params.extend(words)
                        
                        query += " ORDER BY RANDOM() LIMIT ?"
                        params.append(remaining_limit)
                        
                        random_words = self.db_manager.execute_read(query, params)
                        words.extend([row['word'] for row in random_words])
            
            # 确保不重复并限制数量
            words = list(dict.fromkeys(words))[:limit]
            random.shuffle(words)
            
            # 更新队列状态
            self.current_queue = words
            self.current_queue_index = 0
            self.current_source = source
            
            log_info(f"构建听写队列成功，包含 {len(words)} 个单词")
            return words
            
        except Exception as e:
            log_error(f"构建听写队列失败: {str(e)}")
            return []
    
    async def build_queue_async(self, source="today", limit=10, filter_familiar=False, difficulty=None):
        """异步构建听写队列
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            limit: 队列大小限制
            filter_familiar: 是否只包含熟词
            difficulty: 难度级别，可选值："easy", "medium", "hard"
            
        Returns:
            单词列表
        """
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            return await loop.run_in_executor(
                executor,
                self.build_queue,
                source,
                limit,
                filter_familiar,
                difficulty
            )
        finally:
            executor.shutdown(wait=False)
    

        
    def _get_today_learned_words(self, with_example=False):
        """获取今日学习的单词
        
        Args:
            with_example: 是否只返回有例句的单词
            
        Returns:
            单词列表
        """
        try:
            # 缓存键
            cache_key = f"today_words_{with_example}"
            
            # 检查缓存是否有效（缓存有效期为60秒）
            now = datetime.now()
            if (self._today_words_cache_time and 
                (now - self._today_words_cache_time).total_seconds() < 60 and 
                cache_key in self._today_words_cache):
                log_debug(f"使用缓存的今日学习单词: {len(self._today_words_cache[cache_key])}个")
                return self._today_words_cache[cache_key]
            
            today = now.strftime('%Y-%m-%d')
            query = """
            SELECT DISTINCT w.word 
            FROM words w
            JOIN progress p ON w.word = p.word 
            WHERE p.practice_date >= ?
            """
            params = [today]
            
            # 如果需要只返回有例句的单词
            if with_example:
                query += " AND w.example IS NOT NULL AND w.example != ''"
            
            # 添加词库过滤
            active_set_id = self.word_manager.active_word_set_id if hasattr(self.word_manager, 'active_word_set_id') else None
            if active_set_id:
                query += " AND w.set_id = ?"
                params.append(active_set_id)
            
            results = self.db_manager.execute_read(query, params)
            word_list = [row['word'] for row in results]
            
            # 如果没有找到，尝试从听写历史中获取
            if not word_list:
                base_query = "SELECT DISTINCT word FROM dictation_history WHERE practice_date LIKE ?"
                query_params = [f"{today}%"]
                
                if with_example:
                    # 使用JOIN确保单词有例句
                    base_query = """
                    SELECT DISTINCT dh.word 
                    FROM dictation_history dh
                    JOIN words w ON dh.word = w.word
                    WHERE dh.practice_date LIKE ? 
                    AND w.example IS NOT NULL AND w.example != ''
                    """
                
                results = self.db_manager.execute_read(base_query, query_params)
                word_list = [row['word'] for row in results]
            
            # 最后尝试从word_manager获取
            if not word_list:
                try:
                    if hasattr(self.word_manager, 'get_today_learned_words'):
                        words = self.word_manager.get_today_learned_words()
                        if words:
                            log_info(f"从word_manager获取今日学习单词: {len(words)}个")
                            
                            # 如果需要带例句，过滤结果
                            if with_example:
                                words_with_examples = []
                                for word in words:
                                    example = self.get_word_example(word)
                                    if example:
                                        words_with_examples.append(word)
                                word_list = words_with_examples
                            else:
                                word_list = words
                except Exception as fallback_error:
                    log_error(f"从word_manager获取单词失败: {str(fallback_error)}")
            
            # 更新缓存
            self._today_words_cache[cache_key] = word_list
            self._today_words_cache_time = now
            
            log_debug(f"更新今日学习单词缓存，键: {cache_key}, 数量: {len(word_list)}")
            
            return word_list
            
        except Exception as e:
            log_error(f"获取今日学习单词失败: {str(e)}")
            return []
    
    def process_result(self, word, user_input, is_correct, time_spent=0):
        """处理听写结果（同步版本）
        
        Args:
            word: 单词
            user_input: 用户输入
            is_correct: 是否正确
            time_spent: 拼写所用时间（秒）
        """
        try:
            # 记录练习结果
            log_info(f"处理听写结果: {word} - {'正确' if is_correct else '错误'}，用时: {time_spent}秒")
            
            # 优先本地资源判断用户输入（精确匹配）
            if not is_correct:
                # 也可以考虑模糊匹配，但默认使用精确匹配
                is_correct = user_input.strip().lower() == word.strip().lower()
            
            # 计算相似度
            similarity = 1.0 if is_correct else 0.0
            
            # 调用记录方法
            self.record_dictation_result(word, user_input, is_correct, similarity)
            
            # 更新单词权重（复用WordManager的逻辑）
            if hasattr(self.word_manager, 'update_word_weight'):
                try:
                    self.word_manager.update_word_weight(word, is_correct, time_spent)
                except Exception as e:
                    log_error(f"更新单词权重失败: {str(e)}")
            
            # 更新熟悉度
            if hasattr(self.word_manager, 'update_word_familiarity'):
                try:
                    if is_correct:
                        self.word_manager.update_word_familiarity(word, 0.1)  # 正确增加熟悉度
                    else:
                        self.word_manager.update_word_familiarity(word, -0.15)  # 错误降低熟悉度
                except Exception as e:
                    log_error(f"更新单词熟悉度失败: {str(e)}")
            
            # 记录错误单词
            if not is_correct:
                # 记录错误单词到日志，并通知 word_manager 增加错误计数
                log_wrong_word(word, user_input)
                try:
                    if hasattr(self.word_manager, 'add_wrong_word'):
                        self.word_manager.add_wrong_word(word)
                except Exception as e:
                    log_error(f"添加错误单词记录失败: {str(e)}")
                    
            # 更新完成的单词列表（增强版，包含更多信息用于AI判断）
            self.completed_words.append({
                'word': word,
                'user_input': user_input,
                'is_correct': is_correct,
                'time_spent': time_spent,
                'timestamp': datetime.now().isoformat()
            })
            
            # 同时更新session_results列表，用于end_session计算统计信息
            self.session_results.append({
                'word': word,
                'user_input': user_input,
                'is_correct': is_correct,
                'similarity': similarity,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            log_error(f"处理听写结果失败: {str(e)}")
    
    def record_result(self, word, is_correct, time_spent=0):
        """记录听写结果（公开API方法，保持兼容性）
        
        Args:
            word: 单词
            is_correct: 是否正确
            time_spent: 花费时间(秒)
        """
        # 兼容旧的调用方式，将必要参数传递给process_result
        user_input = word if is_correct else ""
        self.process_result(word, user_input, is_correct, time_spent)
    
    def record_dictation_result(self, word: str, user_input: str, is_correct: bool, similarity: float = 0.0):
        """记录听写结果（同步版本）
        
        Args:
            word: 单词
            user_input: 用户输入
            is_correct: 是否正确
            similarity: 相似度（0-1）
        """
        try:
            # 优先使用数据库
            if self.db_manager:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                is_correct_int = 1 if is_correct else 0
                
                # 如果未提供相似度，简单比较计算
                if similarity == 0.0 and user_input and word:
                    similarity = 1.0 if user_input == word else 0.0
                
                # 1. 插入听写历史记录
                self.db_manager.execute_write(
                    """INSERT INTO dictation_history (word, user_input, is_correct, similarity, practice_date) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (word, user_input, is_correct_int, similarity, timestamp)
                )
                
                # 2. 记录到 progress 表（按行记录 is_correct），之后通过聚合查询计算熟练度
                proficiency_change = 0.1 if is_correct else -0.15
                try:
                    self.db_manager.add_progress_record(word, is_correct, proficiency_change)
                except Exception:
                    # 如果add_progress_record不可用，则回退为直接插入单条记录
                    self.db_manager.execute_write(
                        "INSERT INTO progress (word, is_correct, proficiency_change, practice_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                        (word, is_correct_int, proficiency_change)
                    )
                
                # 更新单词熟练度
                try:
                    # 尝试使用数据库管理器的方法
                    wp = self.db_manager.get_word_progress(word)
                    if wp and 'proficiency' in wp:
                        self.db_manager.update_proficiency(word, wp['proficiency'])
                    else:
                        # 如果无法获取聚合数据，直接更新
                        current_proficiency = 0.0
                        try:
                            # 获取当前熟练度
                            res = self.db_manager.execute_read(
                                "SELECT proficiency FROM words WHERE word = ?",
                                (word,)
                            )
                            if res:
                                current_proficiency = res[0]['proficiency'] if res[0]['proficiency'] is not None else 0.0
                        except Exception:
                            pass
                        
                        # 计算新熟练度
                        new_proficiency = max(0.0, min(1.0, current_proficiency + proficiency_change))
                        
                        # 更新单词熟练度和最后复习时间
                        self.db_manager.execute_write(
                            "UPDATE words SET proficiency = ?, last_review = CURRENT_TIMESTAMP WHERE word = ?",
                            (new_proficiency, word)
                        )
                except Exception as e:
                    log_error(f"更新单词熟练度失败: {str(e)}")
                
                log_info(f"记录听写结果: {word} - {'正确' if is_correct else '错误'}")
            
        except Exception as e:
            log_error(f"记录听写结果失败: {str(e)}")
    
    async def record_dictation_result_async(self, word: str, user_input: str, is_correct: bool, similarity: float = 0.0):
        """异步记录听写结果
        
        Args:
            word: 单词
            user_input: 用户输入
            is_correct: 是否正确
            similarity: 相似度（0-1）
        """
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            await loop.run_in_executor(
                executor,
                self.record_dictation_result,
                word,
                user_input,
                is_correct,
                similarity
            )
        finally:
            executor.shutdown(wait=False)
    
    def _update_word_progress(self, word: str, is_correct: bool):
        """更新单词学习进度
        
        Args:
            word: 单词
            is_correct: 是否正确
        """
        try:
            # 直接使用 record_dictation_result 方法，避免重复逻辑
            self.record_dictation_result(word, word if is_correct else "", is_correct)
        except Exception as e:
            log_error(f"更新单词进度失败: {str(e)}")
    
    def get_dictation_stats(self, days: int = 7):
        """获取听写统计信息（同步版本）
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            # 获取当前激活词库ID
            active_set_id = self.word_manager.active_word_set_id if hasattr(self.word_manager, 'active_word_set_id') else None
            
            # 计算开始日期
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 构建基础查询
            base_query = "practice_date >= ?"
            params = [start_date]
            
            # 如果有激活词库，添加词库过滤
            if active_set_id:
                base_query += " AND word IN (SELECT word FROM words WHERE set_id = ?)"
                params.append(active_set_id)
            
            # 查询总练习次数
            total_query = f"SELECT COUNT(*) as count FROM dictation_history WHERE {base_query}"
            total_practices = self.db_manager.execute_read(total_query, params)[0]['count']
            
            # 查询正确次数
            correct_query = f"SELECT COUNT(*) as count FROM dictation_history WHERE {base_query} AND is_correct = 1"
            correct_practices = self.db_manager.execute_read(correct_query, params)[0]['count']
            
            # 查询练习的单词数
            unique_query = f"SELECT COUNT(DISTINCT word) as count FROM dictation_history WHERE {base_query}"
            unique_words = self.db_manager.execute_read(unique_query, params)[0]['count']
            
            # 查询最常错的单词
            wrong_words_query = f"""
            SELECT word, 
                    SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong_count 
               FROM dictation_history 
               WHERE {base_query} 
               GROUP BY word 
               ORDER BY wrong_count DESC 
               LIMIT 5
            """
            most_wrong_words = self.db_manager.execute_read(wrong_words_query, params)
            
            stats = {
                'total_practices': total_practices,
                'correct_practices': correct_practices,
                'accuracy': correct_practices / total_practices if total_practices > 0 else 0,
                'unique_words': unique_words,
                'most_wrong_words': [{'word': row['word'], 'count': row['wrong_count']} for row in most_wrong_words]
            }
            
            return stats
            
        except Exception as e:
            log_error(f"获取听写统计失败: {str(e)}")
            # 回退到基本统计
            return {
                'total_practices': 0,
                'correct_practices': 0,
                'accuracy': 0,
                'unique_words': 0,
                'most_wrong_words': []
            }
    
    async def get_dictation_stats_async(self, days: int = 7):
        """异步获取听写统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            return await loop.run_in_executor(
                executor,
                self.get_dictation_stats,
                days
            )
        finally:
            executor.shutdown(wait=False)
    
    def cleanup(self):
        """清理资源"""
        # 清理完成的单词列表
        self.completed_words.clear()
        self.current_words.clear()
        log_info("听写管理器资源清理完成")
    
    def summarize(self, queue=None, callback=None):
        """生成听写总结报告
        
        Args:
            queue: 要总结的队列，如果为None则总结当前队列
            callback: 用于处理流式输出的回调函数，接收参数：(suggestion_chunk: str, done: bool)
            
        Returns:
            包含总结信息的字典
        """
        if queue is None:
            queue = self.current_queue
        
        try:
            # 优先使用内存中的完成记录
            if hasattr(self, 'completed_words') and self.completed_words:
                queue_records = self.completed_words
            else:
                # 从数据库获取历史记录
                today = datetime.now().strftime('%Y-%m-%d')
                
                # 构建查询条件
                query = """
                SELECT word, user_input, is_correct, practice_date 
                   FROM dictation_history 
                   WHERE practice_date LIKE ? 
                   ORDER BY practice_date ASC"""
                params = [f"{today}%"]
                
                # 如果有激活词库，添加词库过滤
                active_set_id = self.word_manager.active_word_set_id if hasattr(self.word_manager, 'active_word_set_id') else None
                if active_set_id:
                    query = """
                    SELECT dh.word, dh.user_input, dh.is_correct, dh.practice_date 
                       FROM dictation_history dh
                       JOIN words w ON dh.word = w.word
                       WHERE dh.practice_date LIKE ? AND w.set_id = ?
                       ORDER BY dh.practice_date ASC"""
                    params.append(active_set_id)
                
                records = self.db_manager.execute_read(query, params)
                
                # 转换数据库记录为应用需要的格式
                today_records = []
                for record in records:
                    today_records.append({
                        "word": record['word'],
                        "user_input": record.get('user_input', ''),
                        "result": "correct" if record['is_correct'] == 1 else "misspelled",
                        "time_spent": 0,  # 数据库记录中可能没有时间，设置默认值
                        "timestamp": record['practice_date']
                    })
                
                # 为了避免重复计数（同一单词在今日被多次记录），
                # 如果有传入 queue，则按 queue 的顺序从今日历史中挑选每个单词的首次匹配记录（未被重复使用）
                queue_records = []
                if queue:
                    used = set()
                    for rec in today_records:
                        w = rec.get("word")
                        if w in queue and w not in used:
                            queue_records.append(rec)
                            used.add(w)
                            if len(queue_records) >= len(queue):
                                break
                else:
                    # 如果没有传入 queue，则使用所有今日记录
                    queue_records = list(today_records)
        except Exception as e:
            log_error(f"获取总结数据失败: {str(e)}")
            queue_records = []
        
        # 计算统计信息
        total = len(queue_records)
        correct = sum(1 for r in queue_records if r.get("result") == "correct" or r.get("is_correct", False))
        accuracy = correct / total if total > 0 else 0
        missed = [r.get("word") for r in queue_records if r.get("result") != "correct" and not r.get("is_correct", False)]
        
        # 尝试获取AI建议
        suggestion = "继续保持练习！"
        try:
            # 检查是否启用了AI总结功能
            ai_summary_enabled = True
            if hasattr(self, 'settings_manager') and self.settings_manager:
                ai_summary_enabled = self.settings_manager.get_setting("ai_summary_enabled", True)
            
            if ai_summary_enabled and hasattr(self.word_manager, 'ai_available') and self.word_manager.ai_available:
                # 计算平均响应时间（这里使用默认值，因为数据库可能没有记录）
                avg_response_time = 0
                if queue_records:
                    valid_times = [r.get('time_spent', 0) for r in queue_records if r.get('time_spent', 0) > 0]
                    if valid_times:
                        avg_response_time = sum(valid_times) / len(valid_times)
                
                # 准备详细的统计信息给AI
                user_stats = {
                    "total_words": total,
                    "mastered": correct,
                    "review_needed": len(missed),
                    "average_score": accuracy,
                    "average_response_time": avg_response_time,
                    "detailed_results": [{"word": r.get("word", ""), 
                                         "correct": r.get("result") == "correct" or r.get("is_correct", False), 
                                         "time": r.get("time_spent", 0),
                                         "user_input": r.get("user_input", "")} 
                                        for r in queue_records]
                }
                if hasattr(self.word_manager, 'ai_manager') and hasattr(self.word_manager.ai_manager, 'advise'):
                    if hasattr(self.word_manager.ai_manager, 'advise_stream') and callback:
                        # 使用真正的流式输出API
                        suggestion = ""
                        for chunk in self.word_manager.ai_manager.advise_stream(user_stats):
                            callback(chunk, False)
                            suggestion += chunk
                        callback("", True)  # 发送空字符串和done=True表示结束
                    elif callback:
                        # 如果没有真正的流式API，但有回调函数，使用逐字输出模拟流式效果
                        full_suggestion = self.word_manager.ai_manager.advise(user_stats)
                        # 逐字发送建议，实现真正的流式显示效果
                        for i, char in enumerate(full_suggestion):
                            callback(char, i == len(full_suggestion) - 1)
                        suggestion = full_suggestion
                    else:
                        # 正常获取AI建议
                        suggestion = self.word_manager.ai_manager.advise(user_stats)
        except Exception as e:
            log_error(f"获取AI建议失败: {str(e)}")
        
        # 获取难词列表
        difficult_words = []
        if hasattr(self.word_manager, 'get_difficult_words'):
            try:
                difficult_words = self.word_manager.get_difficult_words(limit=5)
            except Exception as e:
                log_error(f"获取难词列表失败: {str(e)}")
        
        return {
            "total": total,
            "correct": correct,
            "accuracy": round(accuracy, 2),
            "missed": missed,
            "suggestion": suggestion,
            "difficult_words": difficult_words
        }
    
    def get_queue_progress(self):
        """获取当前队列的进度信息
        
        Returns:
            包含当前索引和队列长度的字典
        """
        # current_queue_index 在 next_in_queue() 中会在返回单词后自增，
        # 因此此处直接使用 current_queue_index 表示已完成/当前项的计数。
        # 使用 min/max 保证数值在合理范围内。
        current = max(0, min(self.current_queue_index, len(self.current_queue)))
        return {
            "current": current,
            "total": len(self.current_queue)
        }
    
    def get_queue_results_json(self):
        """将队列听写结果合成为JSON字符串，用于AI判断
        
        Returns:
            JSON字符串，包含所有完成的单词和用户答案
        """
        try:
            # 构建完整的结果数据
            results_data = {
                "type": "dictation_queue_results",
                "timestamp": datetime.now().isoformat(),
                "total_words": len(self.completed_words),
                "results": self.completed_words
            }
            
            # 转换为JSON字符串
            return json.dumps(results_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            log_error(f"生成队列结果JSON失败: {str(e)}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def get_word_example(self, word):
        """获取单词的例句（使用统一的词库管理接口）
        
        Args:
            word: 单词
            
        Returns:
            例句字符串或None
        """
        try:
            # 使用统一的WordManager接口获取例句（会自动处理数据库查询和AI补全）
            return self.word_manager.get_word_example(word, async_mode=False)
            
        except Exception as e:
            log_error(f"获取单词例句失败: {str(e)}")
            return None
    
    def save_word_example(self, word, example):
        """保存单词例句到数据库，数据库里已有非空例句则不存储
        
        Args:
            word: 单词
            example: 例句
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if not example:
                return False
            
            # 先检查数据库中是否已有非空例句
            existing_example = self.get_word_example(word)
            if existing_example and existing_example.strip():
                log_info(f"数据库中已存在例句，不重复存储: {word}")
                return True  # 虽然没有更新，但从逻辑上认为操作成功
            
            # 数据库中没有例句或例句为空，进行保存
            self.db_manager.execute_write(
                "UPDATE words SET example = ? WHERE word = ?",
                (example, word)
            )
            log_info(f"例句保存成功: {word}")
            return True
            
        except Exception as e:
            log_error(f"保存单词例句失败: {str(e)}")
            return False
    
    def analyze_queue_results_with_ai(self):
        """使用AI分析队列听写结果
        
        Returns:
            AI分析结果字符串
        """
        try:
            if not self.completed_words:
                return "没有可分析的听写结果"
            
            # 生成JSON数据
            results_json = self.get_queue_results_json()
            
            # 检查AI功能是否可用
            if hasattr(self.word_manager, 'ai_available') and self.word_manager.ai_available:
                if hasattr(self.word_manager, 'ai_manager') and hasattr(self.word_manager.ai_manager, 'analyze_dictation_results'):
                    # 调用AI分析方法
                    analysis = self.word_manager.ai_manager.analyze_dictation_results(results_json)
                    log_info("队列听写结果AI分析完成")
                    return analysis
                else:
                    log_warning("AI管理器不可用或缺少分析方法")
            else:
                log_warning("AI功能不可用")
                
            # 生成简单的本地分析
            correct_count = sum(1 for item in self.completed_words if item['is_correct'])
            total_count = len(self.completed_words)
            accuracy = correct_count / total_count if total_count > 0 else 0
            
            analysis = f"听写完成！正确率: {accuracy:.1%} ({correct_count}/{total_count})"
            if not all(item['is_correct'] for item in self.completed_words):
                wrong_words = [item['word'] for item in self.completed_words if not item['is_correct']]
                analysis += f"\n需要复习的单词: {', '.join(wrong_words)}"
            
            return analysis
            
        except Exception as e:
            log_error(f"AI分析队列结果失败: {str(e)}")
            return f"分析失败: {str(e)}"
    
    def next_in_queue(self):
        """获取队列中的下一个单词
        
        Returns:
            下一个单词字符串，如果队列为空或已到达队列末尾则返回None
        """
        # 确保队列存在且索引有效
        if not self.current_queue or self.current_queue_index >= len(self.current_queue):
            return None
        
        word = self.current_queue[self.current_queue_index]
        self.current_queue_index += 1
        return word
    
    def skip_current_word(self, word, time_spent=0):
        """跳过当前单词，记录为错误并更新索引

        Args:
            word: 要跳过的单词
            time_spent: 跳过所用时间（秒）

        Returns:
            bool: 是否成功处理
        """
        # 记录为错误
        self.record_result(word, False, time_spent)

        # 增加索引（注意：这里不增加索引，索引增加将在下一次获取单词时完成）
        # 因为我们已经在调用此方法前获取了当前单词
        return True
    
    def has_next_in_queue(self):
        """检查队列中是否还有单词
        
        Returns:
            是否还有下一个单词
        """
        return self.current_queue and self.current_queue_index < len(self.current_queue)
    
    def filter_familiar_words(self, words):
        """过滤出熟词
        
        Args:
            words: 单词列表
            
        Returns:
            熟词列表
        """
        # 优先从WordManager获取熟词列表
        if hasattr(self.word_manager, 'get_familiar_words'):
            familiar_words = self.word_manager.get_familiar_words()
            return [w for w in words if w in familiar_words]
        else:
            # 从数据库获取熟词（熟练度高的单词）
            try:
                familiar_words = self.db_manager.execute_read(
                    "SELECT word FROM words WHERE proficiency > 0.8",
                    ()
                )
                familiar_word_list = [row['word'] for row in familiar_words]
                return [w for w in words if w in familiar_word_list]
            except Exception as e:
                log_error(f"从数据库获取熟词失败: {str(e)}")
                return []
    
    def mark_word_as_learned(self, word):
        """标记单词为已学习
        
        Args:
            word: 单词
        """
        try:
            # 使用数据库更新单词学习状态
            self.db_manager.execute_write(
                """UPDATE progress 
                   SET learned = 1, 
                       last_practice = ? 
                   WHERE word = ?""",
                (datetime.now().isoformat(), word)
            )
            
            # 如果记录不存在，创建新记录
            row_count = self.db_manager.last_row_count()
            if row_count == 0:
                self.db_manager.execute_write(
                    """INSERT INTO progress (word, learned) 
                       VALUES (?, 1)""",
                    (word,)
                )
                
        except Exception as e:
            log_error(f"标记单词为已学习失败: {str(e)}")
    
    def get_familiar_words_count(self):
        """获取熟词数量
        
        Returns:
            熟词数量
        """
        try:
            # 从数据库获取熟练度高的单词数量
            result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM words WHERE proficiency > 0.8",
                ()
            )
            return result[0]['count'] if result else 0
        except Exception as e:
            log_error(f"获取熟词数量失败: {str(e)}")
            return 0
    
    def get_today_progress(self):
        """获取今日听写进度
        
        Returns:
            今日听写统计信息
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 从数据库获取今日的听写统计
            # 总练习次数
            total_result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM dictation_history WHERE practice_date LIKE ?",
                (f"{today}%",)
            )
            total = total_result[0]['count'] if total_result else 0
            
            # 正确次数
            correct_result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM dictation_history WHERE practice_date LIKE ? AND is_correct = 1",
                (f"{today}%",)
            )
            correct = correct_result[0]['count'] if correct_result else 0
            
            # 计算准确率
            accuracy = correct / total if total > 0 else 0
            
            return {
                "total": total,
                "correct": correct,
                "accuracy": round(accuracy, 2)
            }
        except Exception as e:
            log_error(f"获取今日听写进度失败: {str(e)}")
            return {
                "total": 0,
                "correct": 0,
                "accuracy": 0.0
            }