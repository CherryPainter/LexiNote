import json
import os
import random
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor

from logger import log_info, log_error, log_warning, log_wrong_word, log_exercise_start
from .database_manager import DatabaseManager
from .cache_manager import get_cache_manager


class DictationManager:
    """优化版听写管理器，负责听写练习的核心逻辑，支持异步操作和缓存"""
    
    def __init__(self, word_manager):
        """初始化听写管理器
        
        Args:
            word_manager: 单词管理器实例
        """
        self.word_manager = word_manager
        self.db_manager = word_manager.db_manager  # 直接使用单词管理器的数据库连接
        self.current_words = []  # 当前听写的单词列表
        self.completed_words = []  # 已完成的单词
        self.current_index = 0  # 当前单词索引
        self.score = 0  # 得分
        self.start_time = None  # 开始时间
        self.duration = 0  # 持续时间
        
        # 迁移数据（如果存在旧的JSON文件）
        self._migrate_old_data()
        
    def _migrate_old_data(self):
        """迁移旧的JSON数据到数据库"""
        try:
            # 检查是否需要迁移
            # 我们只需要迁移一次，所以这里只是尝试导入，不需要额外的标志
            
            # 迁移单词数据（如果存在）
            if os.path.exists('data/word_dict.json'):
                log_info("发现旧的单词数据，开始迁移...")
                import json
                try:
                    with open('data/word_dict.json', 'r', encoding='utf-8') as f:
                        word_dict = json.load(f)
                    
                    # 批量插入单词
                    word_data = [(word, translation) for word, translation in word_dict.items()]
                    if word_data:
                        self.db_manager.execute_write_many(
                            "INSERT OR IGNORE INTO words (word, translation) VALUES (?, ?)",
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
    
    # 已移除缓存相关方法，完全使用数据库
    
    def select_word(self, source="library"):
        """选择一个单词用于单个听写模式（同步版本）
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            
        Returns:
            选中的单词字符串或None
        """
        try:
            if source == "today":
                # 获取今日学习单词
                today_words = self._get_today_learned_words()
                if today_words:
                    return random.choice(today_words)
                # 不自动回退到其它来源，让上层 UI 处理没有单词的情况
                log_info("没有今日学习的单词，返回 None 以提示用户重新选择来源")
                return None
                
            if source == "familiar":
                # 从熟词库中选择
                familiar_words = self.db_manager.execute_read(
                    """
                    SELECT word FROM words 
                    WHERE proficiency > 0.8 AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    ORDER BY RANDOM() LIMIT 1
                    """
                )
                if familiar_words:
                    return familiar_words[0]['word']
                # 不自动回退到其它来源，让上层 UI 处理没有单词的情况
                log_info("没有符合条件的熟词，返回 None 以提示用户重新选择来源")
                return None
                
            # 默认使用词库选择
            if source == "library":
                # 优先选择最近错误率高的单词
                word = self.db_manager.execute_read(
                    """
                    SELECT word FROM words 
                    WHERE proficiency < 0.5 
                    AND last_review < datetime('now', '-1 day')
                    ORDER BY 
                        RANDOM() * (1.0 - COALESCE(proficiency, 0)) DESC 
                    LIMIT 1
                    """
                )
                if word:
                    return word[0]['word']
                    
                # 如果没有合适的单词，随机选择一个很久没复习的单词
                word = self.db_manager.execute_read(
                    """
                    SELECT word FROM words 
                    WHERE last_review IS NULL 
                    OR last_review < datetime('now', '-7 days')
                    ORDER BY last_review ASC, RANDOM()
                    LIMIT 1
                    """
                )
                if word:
                    return word[0]['word']
                    
                # 最后的备选：完全随机选择
                word = self.db_manager.execute_read(
                    "SELECT word FROM words ORDER BY RANDOM() LIMIT 1"
                )
                if word:
                    return word[0]['word']
                    
                log_error(f"无法从来源 {source} 选择单词，返回 None")
            return None
            
        except Exception as e:
            log_error(f"选择单词时发生错误: {str(e)}")
            return None
    
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
    
    def build_queue(self, source="today", limit=10, filter_familiar=False):
        """构建听写队列（同步版本）
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            limit: 队列大小限制
            filter_familiar: 是否只包含熟词
            
        Returns:
            单词列表
        """
        try:
            words = []
            if source == "today":
                # 获取今日学习单词
                words = self._get_today_learned_words()
                if not words:
                    # 不自动回退到其它来源，让上层 UI 处理没有单词的情况
                    log_info("没有今日学习的单词，返回空队列以提示用户重新选择来源")
                    return []
            
            if source == "familiar" or (filter_familiar and source != "today"):
                # 从熟词库中选择，避免重复练习最近复习过的单词
                words = self.db_manager.execute_read(
                    """
                    SELECT word FROM words 
                    WHERE proficiency > 0.8 
                    AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    ORDER BY 
                        CASE 
                            WHEN last_review IS NULL THEN 1 
                            ELSE 0 
                        END DESC,
                        last_review ASC,
                        RANDOM()
                    LIMIT ?
                    """,
                    (limit,)
                )
                words = [row['word'] for row in words]
                if not words:
                    log_info("没有符合条件的熟词，返回空队列以提示用户重新选择来源")
                    return []
            
            if not words and source == "library":
                # 智能选择策略：
                # 1. 40% 最近错误率高的单词
                difficult_limit = int(limit * 0.4)
                difficult_words = self.db_manager.execute_read(
                    """
                    SELECT word FROM words 
                    WHERE proficiency < 0.5
                    AND (last_review IS NULL OR last_review < datetime('now', '-1 day'))
                    ORDER BY 
                        RANDOM() * (1.0 - COALESCE(proficiency, 0)) DESC 
                    LIMIT ?
                    """,
                    (difficult_limit,)
                )
                words.extend([row['word'] for row in difficult_words])
                
                # 2. 30% 很久没复习的单词
                old_limit = int(limit * 0.3)
                if old_limit > 0:
                    old_words = self.db_manager.execute_read(
                        """
                        SELECT word FROM words 
                        WHERE word NOT IN (SELECT word FROM (
                            SELECT DISTINCT word 
                            FROM dictation_history 
                            WHERE practice_date > datetime('now', '-7 days')
                        ))
                        ORDER BY last_review ASC, RANDOM()
                        LIMIT ?
                        """,
                        (old_limit,)
                    )
                    words.extend([row['word'] for row in old_words])
                
                # 3. 30% 完全随机选择
                remaining_limit = limit - len(words)
                if remaining_limit > 0:
                    random_words = self.db_manager.execute_read(
                        """
                        SELECT word FROM words 
                        WHERE word NOT IN (?)
                        ORDER BY RANDOM() 
                        LIMIT ?
                        """,
                        (','.join(words), remaining_limit)
                    )
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
    
    async def build_queue_async(self, source="today", limit=10, filter_familiar=False):
        """异步构建听写队列
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            limit: 队列大小限制
            filter_familiar: 是否只包含熟词
            
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
                filter_familiar
            )
        finally:
            executor.shutdown(wait=False)
    
    def _get_today_learned_words(self):
        """获取今日学习过的单词（从数据库）"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 从数据库查询今日学习的单词
            words = self.db_manager.execute_read(
                "SELECT DISTINCT word FROM dictation_history WHERE practice_date LIKE ? ORDER BY practice_date DESC",
                (f"{today}%",)
            )
            
            word_list = [row['word'] for row in words]
            
            return word_list
        except Exception as e:
            log_error(f"获取今日学习单词失败: {str(e)}")
            # 回退到word_manager的方法
            try:
                if hasattr(self.word_manager, 'get_today_learned_words'):
                    words = self.word_manager.get_today_learned_words()
                    if words:
                        log_info(f"从word_manager获取今日学习单词: {len(words)}个")
                        return words
            except Exception as fallback_error:
                log_error(f"回退方法失败: {str(fallback_error)}")
            
            # 如果所有方法都失败，返回空列表
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
            # 调用新的记录方法
            self.record_dictation_result(word, user_input, is_correct, 1.0 if is_correct else 0.0)
            
            # 更新单词权重（复用WordManager的逻辑）
            if hasattr(self.word_manager, 'update_word_weight'):
                self.word_manager.update_word_weight(word, is_correct, time_spent)
            
            # 更新熟悉度
            if hasattr(self.word_manager, 'update_word_familiarity'):
                if is_correct:
                    self.word_manager.update_word_familiarity(word, 0.1)  # 正确增加熟悉度
                else:
                    self.word_manager.update_word_familiarity(word, -0.15)  # 错误降低熟悉度
                    
            # 更新熟词库
            self._update_familiar_words(word, is_correct)
            
            # 记录错误单词
            if not is_correct:
                # 记录错误单词到日志，并通知 word_manager 增加错误计数
                log_wrong_word(word, user_input)
                try:
                    if hasattr(self.word_manager, 'add_wrong_word'):
                        self.word_manager.add_wrong_word(word)
                except Exception:
                    pass
            
        except Exception as e:
            log_error(f"记录听写结果失败: {str(e)}")
    
    def record_result(self, word, is_correct, time_spent=0):
        """记录听写结果并更新单词进度和权重（兼容旧版本）
        
        Args:
            word: 单词
            is_correct: 是否正确
            time_spent: 拼写所用时间（秒）
        """
        # 调用新版本的方法，保持向后兼容
        self.process_result(word, "", is_correct, time_spent)
            
    # 已移除重复的process_result方法
    
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
                timestamp = datetime.now().isoformat()
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
                        "INSERT INTO progress (word, is_correct, proficiency_change, practice_date) VALUES (?, ?, ?, ?)",
                        (word, is_correct_int, proficiency_change, timestamp)
                    )
                
                log_info(f"使用数据库记录听写结果: {word} - {'正确' if is_correct else '错误'}")

                # 更新单词熟练度（基于 progress 表的聚合）
                try:
                    wp = self.db_manager.get_word_progress(word)
                    if wp and 'proficiency' in wp:
                        self.db_manager.update_proficiency(word, wp['proficiency'])
                except Exception:
                    pass
                
                # 记录错误单词
                if not is_correct:
                    # 日志记录并让 word_manager 跟踪错误单词
                    log_wrong_word(word, user_input)
                    try:
                        if hasattr(self.word_manager, 'add_wrong_word'):
                            self.word_manager.add_wrong_word(word)
                    except Exception:
                        pass
                
                # 清除相关缓存
                with self._cache_lock:
                    # 清除今日单词缓存
                    today = datetime.now().strftime('%Y-%m-%d')
                    if f"today_words_{today}" in self._memory_cache:
                        del self._memory_cache[f"today_words_{today}"]
                    
                    # 清除单词进度缓存（如果存在）
                pass  # 不再使用缓存，所以不需要清除
            
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
            # 获取当前进度
            current_progress = self.db_manager.get_word_progress(word)
            
            if current_progress:
                # 更新现有进度
                correct_count = current_progress.get('correct_count', 0)
                total_count = current_progress.get('total_count', 0) + 1
                
                if is_correct:
                    correct_count += 1
                
                # 计算熟练度
                proficiency = correct_count / total_count if total_count > 0 else 0
                
                # 更新数据库
                self.db_manager.execute_write(
                    """UPDATE progress SET 
                           correct_count = ?, 
                           total_count = ?, 
                           practice_date = ? 
                       WHERE word = ?""",
                    (correct_count, total_count, datetime.now().isoformat(), word)
                )
            else:
                # 创建新的进度记录
                correct_count = 1 if is_correct else 0
                total_count = 1
                proficiency = correct_count / total_count
                
                # 插入数据库
                self.db_manager.execute_write(
                    """INSERT INTO progress (word, correct_count, total_count, practice_date) 
                       VALUES (?, ?, ?, ?)""",
                    (word, correct_count, total_count, datetime.now().isoformat())
                )
                
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
            # 计算开始日期
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 查询总练习次数
            total_practices = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM dictation_history WHERE practice_date >= ?",
                (start_date,)
            )[0]['count']
            
            # 查询正确次数
            correct_practices = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM dictation_history WHERE practice_date >= ? AND is_correct = 1",
                (start_date,)
            )[0]['count']
            
            # 查询练习的单词数
            unique_words = self.db_manager.execute_read(
                "SELECT COUNT(DISTINCT word) as count FROM dictation_history WHERE practice_date >= ?",
                (start_date,)
            )[0]['count']
            
            # 查询最常错的单词
            most_wrong_words = self.db_manager.execute_read(
                """SELECT word, 
                        SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong_count 
                   FROM dictation_history 
                   WHERE practice_date >= ? 
                   GROUP BY word 
                   ORDER BY wrong_count DESC 
                   LIMIT 5""",
                (start_date,)
            )
            
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
        # 由于不再使用固定的executor，这里只记录日志
        log_info("听写管理器资源清理完成")
    
    # 已移除_load_data方法，完全使用数据库存储
    
    # 已移除_save_data方法，完全使用数据库存储
    
    def _update_familiar_words(self, word, is_correct):
        """更新熟词库
        
        Args:
            word: 单词
            is_correct: 是否正确
        """
        # 只使用数据库操作，不再维护独立的文件存储
        try:
            # 将熟悉度直接更新到 words.proficiency 字段（基于现有熟练度）
            try:
                res = self.db_manager.execute_read(
                    "SELECT proficiency FROM words WHERE word = ?",
                    (word,)
                )
                current = res[0]['proficiency'] if res else 0.0
            except Exception:
                current = 0.0

            delta = 0.1 if is_correct else -0.15
            new_prof = max(0.0, min(1.0, current + delta))
            # 使用立即写入以尽快反映变化
            try:
                self.db_manager.update_proficiency(word, new_prof)
            except Exception:
                # 回退：直接执行SQL
                self.db_manager.execute_write(
                    "UPDATE words SET proficiency = ?, last_review = CURRENT_TIMESTAMP WHERE word = ?",
                    (new_prof, word)
                )

        except Exception as e:
            log_warning(f"更新熟词库失败: {str(e)}")
    
    def _record_to_history(self, word, result, time_spent):
        """将听写结果记录到历史记录中
        
        Args:
            word: 单词
            result: 结果（correct/misspelled）
            time_spent: 拼写所用时间（秒）
        """
        try:
            # 只使用数据库记录历史
            timestamp = datetime.now().isoformat()
            is_correct = 1 if result == "correct" else 0
            
            # 插入历史记录
            self.db_manager.execute_write(
                """INSERT INTO dictation_history (word, user_input, is_correct, similarity, practice_date) 
                   VALUES (?, ?, ?, ?, ?)""",
                (word, word, is_correct, 1.0 if is_correct else 0.0, timestamp)
            )
            
            log_info(f"使用数据库记录历史: {word} - {result}")
            
        except Exception as e:
            log_error(f"记录历史失败: {str(e)}")
    
    def summarize(self, queue=None):
        """生成听写总结报告
        
        Args:
            queue: 要总结的队列，如果为None则总结当前队列
            
        Returns:
            包含总结信息的字典
        """
        if queue is None:
            queue = self.current_queue
        
        try:
            # 从数据库获取历史记录
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 查询今日的听写历史
            records = self.db_manager.execute_read(
                """SELECT word, is_correct, practice_date 
                   FROM dictation_history 
                   WHERE practice_date LIKE ? 
                   ORDER BY practice_date ASC""",
                (f"{today}%",)
            )
            
            # 转换数据库记录为应用需要的格式
            today_records = []
            for record in records:
                today_records.append({
                    "word": record['word'],
                    "result": "correct" if record['is_correct'] == 1 else "misspelled",
                    "time_spent": 0,  # 数据库记录中可能没有时间，设置默认值
                    "timestamp": record['practice_date']
                })
        except Exception as e:
            log_error(f"从数据库获取历史记录失败: {str(e)}")
            today_records = []
        
        # 为了避免重复计数（同一单词在今日被多次记录），
        # 如果有传入 queue，则按 queue 的顺序从今日历史中挑选每个单词的首次匹配记录（未被重复使用），
        # 最多收集 len(queue) 条记录。这样 summary 的 total 不会超过 queue 的长度。
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
        
        # 计算统计信息
        total = len(queue_records)
        correct = sum(1 for r in queue_records if r.get("result") == "correct")
        accuracy = correct / total if total > 0 else 0
        missed = [r.get("word") for r in queue_records if r.get("result") != "correct"]
        
        # 尝试获取AI建议
        suggestion = "继续保持练习！"
        try:
            if hasattr(self.word_manager, 'ai_available') and self.word_manager.ai_available:
                # 计算平均响应时间（这里使用默认值，因为数据库可能没有记录）
                avg_response_time = 0
                avg_correct_time = 0
                avg_incorrect_time = 0
                
                # 准备详细的统计信息给AI
                user_stats = {
                    "total_words": total,
                    "mastered": correct,
                    "review_needed": len(missed),
                    "average_score": accuracy,
                    "average_response_time": avg_response_time,
                    "avg_correct_response_time": avg_correct_time,
                    "avg_incorrect_response_time": avg_incorrect_time,
                    "detailed_results": [{"word": r["word"], "correct": r["result"] == "correct", "time": r.get("time_spent", 0)} for r in queue_records]
                }
                if hasattr(self.word_manager, 'ai_manager'):
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