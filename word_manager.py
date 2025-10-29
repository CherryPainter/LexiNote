"""单词管理器，负责单词的增删改查、权重计算和练习功能"""
import os
import random
import functools
import threading
from typing import Dict, List, Optional, Union
from datetime import datetime

from logger import log_info, log_error, log_warning
from core.database_manager import DatabaseManager


class WordManager:
    """优化版单词管理器类，提供单词管理相关功能，支持异步操作和缓存"""

    def __init__(self):
        """初始化单词管理器"""
        self.data_dir = 'data'
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 使用数据库管理器
        self.db_manager = DatabaseManager()
        
        # 内存缓存
        self._word_cache = {}  # 单词翻译缓存
        self._weight_cache = {}  # 权重缓存
        self._cache_lock = threading.RLock()  # 缓存锁
        
        # 初始化错误单词字典
        self.wrong_words = {}

        # 单词熟悉度映射（在内存中缓存，避免频繁查询数据库）
        self.word_familiarity = {}
        
        # 初始化AI管理器（延迟加载方式）
        self.ai_manager = None
        self.ai_available = False
        self._init_ai_manager()
        
        # 预热缓存
        self._warmup_cache()
        # 加载单词熟悉度到内存缓存
        self._load_word_familiarity()
    
    def _warmup_cache(self):
        """预热缓存，加载常用数据到内存"""
        try:
            # 加载所有单词到缓存
            all_words = self.db_manager.get_all_words()
            for word in all_words[:100]:  # 限制加载数量，避免内存占用过大
                translation = self.db_manager.get_word_translation(word)
                if translation:
                    with self._cache_lock:
                        self._word_cache[word] = translation
            log_info(f"缓存预热完成，加载了{len(self._word_cache)}个单词")
        except Exception as e:
            log_error(f"缓存预热失败: {str(e)}")

    def _init_ai_manager(self):
        """初始化AI管理器（延迟加载）"""
        try:
            from core.ai_interface import AIManager
            self.ai_manager = AIManager()
            # 直接检查AI可用性，不再调用不存在的is_ai_available方法
            self.ai_available = self._test_ai_connection()
        except ImportError:
            log_warning("AI接口模块未找到，部分功能可能受限")
            self.ai_available = False
        except Exception as e:
            log_error(f"初始化AI管理器失败: {str(e)}")
            self.ai_available = False
    
    def _test_ai_connection(self) -> bool:
        """测试AI连接是否可用
        
        Returns:
            bool: AI连接是否可用
        """
        try:
            # 简单测试AI连接，发送一个简短的请求
            if self.ai_manager:
                # 使用try-except捕获可能的错误，避免在初始化过程中抛出异常
                try:
                    test_response = self.ai_manager.example_sync("test")
                    # 检查响应是否包含错误信息
                    if test_response and "AI功能暂不可用" not in test_response:
                        log_info("AI功能测试成功，服务可用")
                        return True
                    else:
                        log_info(f"AI功能测试失败: {test_response}")
                        return False
                except Exception as e:
                    log_warning(f"测试AI连接失败: {str(e)}")
                    return False
            return False
        except Exception as e:
            log_warning(f"检查AI可用性时发生错误: {str(e)}")
            return False
    
    def _load_data(self, file_path: str) -> dict:
        """加载数据文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 加载的数据，如果文件不存在则返回空字典
        """
        import json
        try:
            # 确保数据目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                log_info(f"数据文件不存在，创建空文件: {file_path}")
                # 创建空文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                return {}
            
            # 加载文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(f"加载数据文件失败: {file_path}, 错误: {str(e)}")
            return {}
    
    def _save_data(self, file_path: str, data: dict):
        """保存数据到文件
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        import json
        try:
            # 确保数据目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 保存数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            log_info(f"数据保存成功: {file_path}")
        except Exception as e:
            log_error(f"保存数据文件失败: {file_path}, 错误: {str(e)}")
    
    @functools.lru_cache(maxsize=1000)
    def get_translation(self, word: str) -> Optional[str]:
        """获取单词翻译（带缓存）
        
        Args:
            word: 单词
            
        Returns:
            翻译结果
        """
        # 先查内存缓存
        with self._cache_lock:
            if word in self._word_cache:
                return self._word_cache[word]
        
        # 查数据库
        translation = self.db_manager.get_word_translation(word)
        
        # 更新缓存
        if translation:
            with self._cache_lock:
                self._word_cache[word] = translation
        
        return translation
    
    def add_word(self, word: str, translation: str) -> bool:
        """添加单词
        
        Args:
            word: 单词
            translation: 翻译
            
        Returns:
            是否添加成功
        """
        try:
            # 添加到数据库
            self.db_manager.add_word(word, translation)
            
            # 更新缓存
            with self._cache_lock:
                self._word_cache[word] = translation
            
            log_info(f"添加单词成功: {word} -> {translation}")
            return True
        except Exception as e:
            log_error(f"添加单词失败: {str(e)}")
            return False
    
    def get_all_words(self) -> List[str]:
        """获取所有单词
        
        Returns:
            单词列表
        """
        return self.db_manager.get_all_words()
    
    # get_word_by_weight 已在文件后部提供更完整实现，早期占位实现已移除
    
    def update_word_proficiency(self, word: str, is_correct: bool):
        """更新单词熟练度
        
        Args:
            word: 单词
            is_correct: 是否正确
        """
        try:
            # 获取当前熟练度
            results = self.db_manager.execute_read(
                "SELECT proficiency FROM words WHERE word = ?",
                (word,)
            )
            
            current_proficiency = results[0]['proficiency'] if results else 0.0
            
            # 更新熟练度
            # 正确增加0.1，错误减少0.15
            proficiency_change = 0.1 if is_correct else -0.15
            new_proficiency = max(0.0, min(1.0, current_proficiency + proficiency_change))
            
            # 更新数据库
            self.db_manager.update_proficiency(word, new_proficiency)
            self.db_manager.add_progress_record(word, is_correct, proficiency_change)
            
            # 清除相关缓存
            with self._cache_lock:
                if word in self._weight_cache:
                    del self._weight_cache[word]
            
            log_info(f"更新单词熟练度: {word} -> {new_proficiency}")
            
        except Exception as e:
            log_error(f"更新单词熟练度失败: {str(e)}")
    
    def get_familiar_words(self) -> List[str]:
        """获取熟悉的单词（熟练度>0.8）
        
        Returns:
            熟悉单词列表
        """
        try:
            results = self.db_manager.execute_read(
                "SELECT word FROM words WHERE proficiency > 0.8"
            )
            return [row['word'] for row in results]
        except Exception as e:
            log_error(f"获取熟悉单词失败: {str(e)}")
            return []
    
    # 早期的 get_difficult_words 实现已移除，使用文件后部更通用的 get_difficult_words
    
    def get_learning_stats(self) -> Dict:
        """获取学习统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 总单词数
            total_words = len(self.get_all_words())
            
            # 今日练习次数
            today = datetime.now().strftime('%Y-%m-%d')
            today_practices = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM progress WHERE practice_date LIKE ?",
                (f"{today}%",)
            )[0]['count']
            
            # 今日正确次数
            today_correct = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM progress WHERE practice_date LIKE ? AND is_correct = 1",
                (f"{today}%",)
            )[0]['count']
            
            # 平均熟练度
            avg_proficiency = self.db_manager.execute_read(
                "SELECT AVG(proficiency) as avg FROM words"
            )[0]['avg'] or 0.0
            
            return {
                "total_words": total_words,
                "today_practices": today_practices,
                "today_correct": today_correct,
                "today_accuracy": today_correct / today_practices if today_practices > 0 else 0.0,
                "avg_proficiency": float(avg_proficiency)
            }
            
        except Exception as e:
            log_error(f"获取学习统计失败: {str(e)}")
            return {
                "total_words": 0,
                "today_practices": 0,
                "today_correct": 0,
                "today_accuracy": 0.0,
                "avg_proficiency": 0.0
            }
    
    def clear_cache(self):
        """清除内存缓存"""
        with self._cache_lock:
            self._word_cache.clear()
            self._weight_cache.clear()
        self.get_translation.cache_clear()  # 清除lru_cache
        log_info("内存缓存已清除")

    def _load_word_familiarity(self):
        """从数据库加载所有单词的熟练度到内存缓存"""
        try:
            rows = self.db_manager.execute_read("SELECT word, proficiency FROM words")
            with self._cache_lock:
                self.word_familiarity = {row['word']: row.get('proficiency', 0.0) for row in rows}
            log_info(f"加载单词熟悉度: {len(self.word_familiarity)} 条")
        except Exception as e:
            log_error(f"加载单词熟悉度失败: {str(e)}")

    def check_spelling(self, correct_word: str, user_input: str) -> bool:
        """检查拼写是否正确
        
        Args:
            correct_word: 正确的单词
            user_input: 用户输入的单词
            
        Returns:
            bool: 拼写是否正确（不区分大小写）
        """
        try:
            # 不区分大小写的比较
            return correct_word.lower() == user_input.lower().strip()
        except Exception as e:
            log_error(f"检查拼写时出错: {str(e)}")
            return False
            
    def remove_word(self, word: str) -> bool:
        """删除单词

        Args:
            word: 单词
            
        Returns:
            是否删除成功
        """
        try:
            # 从数据库删除
            result = self.db_manager.remove_word(word)
            
            # 从缓存删除
            with self._cache_lock:
                if word in self._word_cache:
                    del self._word_cache[word]
                if word in self._weight_cache:
                    del self._weight_cache[word]
            
            if result:
                log_info(f"删除单词成功: {word}")
            return result
        except Exception as e:
            log_error(f"删除单词失败: {str(e)}")
            return False

    def update_word(self, word: str, translation: str) -> bool:
        """更新单词

        Args:
            word: 单词
            translation: 新的翻译
            
        Returns:
            是否更新成功
        """
        try:
            # 更新数据库
            result = self.db_manager.update_word(word, translation)
            
            # 更新缓存
            if result:
                with self._cache_lock:
                    self._word_cache[word] = translation
                log_info(f"更新单词成功: {word} -> {translation}")
            return result
        except Exception as e:
            log_error(f"更新单词失败: {str(e)}")
            return False
    
    def batch_import_words(self, json_file_path: str) -> Dict:
        """批量导入单词
        
        Args:
            json_file_path: JSON文件路径，文件格式应为 {"word1": "translation1", "word2": "translation2", ...}
            
        Returns:
            Dict: 导入结果统计信息，包含success, total, imported, skipped, errors等字段
        """
        try:
            # 动态导入单词导入器以避免循环依赖
            from modules.word_importer import import_words_from_json
            
            # 调用导入功能
            result = import_words_from_json(json_file_path)
            
            # 如果导入成功，更新缓存
            if result.get("success", False) and result.get("imported", 0) > 0:
                # 重新预热缓存以包含新导入的单词
                self._warmup_cache()
            
            return result
        except ImportError:
            log_error("无法导入单词导入模块")
            return {
                "success": False,
                "total": 0,
                "imported": 0,
                "skipped": 0,
                "errors": ["单词导入模块未找到"]
            }
        except Exception as e:
            log_error(f"批量导入单词时发生错误: {str(e)}")
            return {
                "success": False,
                "total": 0,
                "imported": 0,
                "skipped": 0,
                "errors": [str(e)]
            }

    def get_word_translation(self, word: str) -> Optional[str]:
        """获取单词翻译

        Args:
            word: 单词

        Returns:
            str: 单词的翻译，如果不存在返回None
        """
        return self.get_translation(word)

    def get_word_count(self) -> int:
        """获取单词数量

        Returns:
            int: 单词数量
        """
        try:
            return len(self.get_all_words())
        except Exception as e:
            log_error(f"获取单词数量失败: {str(e)}")
            return 0

    def get_random_word(
        self, exclude_words: List[str] = None
    ) -> Optional[str]:
        """获取随机单词

        Args:
            exclude_words: 排除的单词列表

        Returns:
            str: 随机单词，如果没有可用单词返回None
        """
        try:
            all_words = self.get_all_words()
            if exclude_words:
                available_words = [word for word in all_words if word not in exclude_words]
            else:
                available_words = all_words
            
            if available_words:
                return random.choice(available_words)
            return None
        except Exception as e:
            log_error(f"获取随机单词失败: {str(e)}")
            return None

    def get_weighted_random_word(
        self, exclude_words: List[str] = None
    ) -> Optional[str]:
        """根据权重获取随机单词

        Args:
            exclude_words: 排除的单词列表

        Returns:
            str: 随机单词，如果没有可用单词返回None
        """
        try:
            # 使用数据库中的熟练度作为权重
            words = self.db_manager.execute_read(
                "SELECT word, proficiency FROM words ORDER BY proficiency ASC"
            )
            
            # 过滤排除的单词
            if exclude_words:
                words = [word for word in words if word['word'] not in exclude_words]
            
            if not words:
                return None
            
            # 使用权重选择（熟练度越低，权重越高）
            total_weight = sum((1.0 - word['proficiency']) for word in words)
            if total_weight == 0:
                return random.choice(words)['word']
            
            # 加权随机选择
            r = random.uniform(0, total_weight)
            cumulative = 0
            
            for word in words:
                cumulative += (1.0 - word['proficiency'])
                if r <= cumulative:
                    return word['word']
            
            return words[0]['word']
        except Exception as e:
            log_error(f"获取加权随机单词失败: {str(e)}")
            return self.get_random_word(exclude_words)

    def update_word_weight(self, word: str, is_correct: bool, time_spent: float = 0):
        """更新单词权重，考虑正确与否和响应时间

        Args:
            word: 单词
            is_correct: 是否拼写正确
            time_spent: 拼写所用时间（秒）
        """
        try:
            # 调用数据库更新方法，考虑时间因素调整熟练度变化量
            proficiency_change = 0.1
            
            if is_correct:
                # 正确拼写时增加熟练度
                if time_spent > 10:
                    proficiency_change = 0.05  # 响应很慢，增加较少
                elif time_spent > 5:
                    proficiency_change = 0.08  # 响应较慢，增加中等
                elif time_spent < 2:
                    proficiency_change = 0.15  # 响应很快，增加较多
            else:
                # 错误拼写时减少熟练度
                proficiency_change = -0.15
                if time_spent < 3:
                    proficiency_change = -0.2  # 快速错误，减少更多
                elif time_spent > 8:
                    proficiency_change = -0.1  # 思考后错误，减少较少
            
            # 获取当前熟练度
            results = self.db_manager.execute_read(
                "SELECT proficiency FROM words WHERE word = ?",
                (word,)
            )
            
            current_proficiency = results[0]['proficiency'] if results else 0.0
            new_proficiency = max(0.0, min(1.0, current_proficiency + proficiency_change))
            
            # 更新数据库
            self.db_manager.update_proficiency(word, new_proficiency)
            
            log_info(f"更新单词权重: {word}, 熟练度从 {current_proficiency} 调整为 {new_proficiency}")
            
        except Exception as e:
            log_error(f"更新单词权重失败: {str(e)}")

    def get_progress(self) -> dict:
        """获取学习进度信息

        Returns:
            包含学习进度信息的字典，包括:
            - total_learned: 总学习单词数
            - correct_rate: 正确率
            - last_session: 最后学习时间
        """
        try:
            # 计算总学习单词数
            total_learned = self.get_word_count()
            
            # 计算正确率
            stats = self.get_learning_stats()
            total_attempts = stats.get('today_practices', 0)
            if total_attempts > 0:
                correct_rate = stats.get('today_accuracy', 0.0)
            else:
                # 如果没有今日练习记录，查询历史数据
                try:
                    result = self.db_manager.execute_read(
                        "SELECT COUNT(*) as total, SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct FROM progress"
                    )[0]
                    if result['total'] > 0:
                        correct_rate = result['correct'] / result['total']
                    else:
                        correct_rate = 0.0
                except Exception:
                    correct_rate = 0.0
            
            # 获取最后学习时间
            last_session = "未开始"
            try:
                result = self.db_manager.execute_read(
                    "SELECT MAX(practice_date) as last_date FROM progress"
                )[0]
                if result['last_date']:
                    last_session = result['last_date']
            except Exception as e:
                log_info(f"获取最后学习时间失败: {str(e)}")
            
            return {
                'total_learned': total_learned,
                'correct_rate': correct_rate,
                'last_session': last_session
            }
        except Exception as e:
            log_info(f"获取学习进度失败: {str(e)}")
            # 返回默认值
            return {
                'total_learned': 0,
                'correct_rate': 0.0,
                'last_session': "未开始"
            }
    
    def start_exercise(self, exercise_type: str) -> None:
        """开始练习，记录练习开始信息

        Args:
            exercise_type: 练习类型，如"听写"
        """
        try:
            from datetime import datetime
            
            # 记录练习开始日志
            log_info(f"开始{exercise_type}练习")
            
            # 在数据库中记录练习会话
            timestamp = datetime.now().isoformat()
            try:
                self.db_manager.execute_write(
                    "INSERT INTO exercise_sessions (exercise_type, start_time) VALUES (?, ?)",
                    (exercise_type, timestamp)
                )
            except Exception as db_error:
                log_info(f"记录练习会话失败: {str(db_error)}")
        except Exception as e:
            log_info(f"开始练习失败: {str(e)}")
    
    def get_word_by_weight(self) -> Optional[str]:
        """根据单词权重获取单词（错误次数多的单词优先）

        Returns:
            选中的单词，如果没有单词则返回None
        """
        try:
            # 查询熟练度较低的单词
            words = self.db_manager.execute_read(
                "SELECT word, proficiency FROM words ORDER BY proficiency ASC LIMIT 20"
            )
            
            if not words:
                return None
            
            # 使用权重选择
            # 熟练度越低，权重越高
            total_weight = sum((1.0 - word['proficiency']) for word in words)
            if total_weight == 0:
                # 如果所有单词熟练度都很高，随机选择
                return random.choice(words)['word']
            
            # 加权随机选择
            r = random.uniform(0, total_weight)
            cumulative = 0
            
            for word in words:
                cumulative += (1.0 - word['proficiency'])
                if r <= cumulative:
                    return word['word']
            
            return words[0]['word']
            
        except Exception as e:
            log_error(f"根据权重获取单词失败: {str(e)}")
            return self.get_random_word()
    
    def add_wrong_word(self, word: str):
        """添加错误单词

        Args:
            word: 单词
        """
        try:
            word_lower = word.lower()
            # 错误拼写，更新权重，没有时间统计使用默认值
            self.update_word_weight(word_lower, False, 0)
            # 降低熟悉度（通过更新熟练度实现）
            self.update_word_proficiency(word_lower, False)
            log_info(f"添加错误单词: {word}")
        except Exception as e:
            log_error(f"添加错误单词失败: {str(e)}")

    def get_wrong_words(self) -> Dict[str, int]:
        """获取所有错误单词及其错误次数

        Returns:
            Dict[str, int]: 错误单词字典，键为单词，值为错误次数
        """
        return self.wrong_words

    def get_difficult_words(self, threshold: int = 3, limit: int = None) -> List[str]:
        """获取困难单词（错误次数超过阈值的单词）

        Args:
            threshold: 错误次数阈值
            limit: 返回单词数量限制，如果为None则返回所有符合条件的单词

        Returns:
            List[str]: 困难单词列表
        """
        difficult_words = [
            word for word, count in self.wrong_words.items()
            if count >= threshold
        ]
        # 如果指定了limit，限制返回数量
        if limit is not None:
            difficult_words = difficult_words[:limit]
        return difficult_words

    def update_word_familiarity(self, word: str, delta: float):
        """更新单词熟悉度（已废弃，使用update_word_proficiency替代）

        Args:
            word: 单词
            delta: 熟悉度变化量
        """
        try:
            # 调用新的update_word_proficiency方法，使用参数转换
            is_correct = delta > 0  # 正增量表示正确，负增量表示错误
            self.update_word_proficiency(word, is_correct)
        except Exception as e:
            log_error(f"更新单词熟悉度失败: {str(e)}")

    def get_today_learned_words(self) -> List[str]:
        """获取今日学习的单词列表
        
        Returns:
            List[str]: 今日学习的单词列表
        """
        try:
            # 从数据库查询今日学习记录
            today = datetime.now().strftime("%Y-%m-%d")
            results = self.db_manager.execute_read(
                """
                SELECT DISTINCT word 
                FROM progress 
                WHERE practice_date >= ?
                """,
                (today + " 00:00:00",)
            )
            
            today_words = [row['word'] for row in results]
            log_info(f"get_today_learned_words 返回 {len(today_words)} 个单词")
            return today_words
        except Exception as e:
            log_error(f"获取今日学习单词失败: {str(e)}")
            return []
    
    def get_word_familiarity(self, word: str = None) -> Union[float, Dict[str, float]]:
        """获取单词熟悉度
        
        Args:
            word: 单词，不提供则返回所有单词的熟悉度
            
        Returns:
            单个单词返回熟悉度值(0-1)，所有单词返回字典{word: familiarity}
        """
        if word is not None:
            return self.word_familiarity.get(word.lower(), 0.0)
        else:
            # 返回所有单词的熟悉度
            # 使用数据库获取所有单词并返回熟悉度映射
            try:
                all_words = self.db_manager.get_all_words()
                return {word: self.word_familiarity.get(word.lower(), 0.0) for word in all_words}
            except Exception as e:
                log_error(f"获取单词熟悉度映射失败: {str(e)}")
                return {}

    def _get_default_example(self, word: str) -> str:
        """获取单词的默认例句（用于AI调用失败时的备用）

        Args:
            word: 要获取例句的单词

        Returns:
            str: 包含例句和翻译的文本
        """
        # 硬编码的基本例句
        basic_examples = {
            "apple": (
                "I eat an apple every day. "
                "(我每天吃一个苹果。)"
            ),
            "book": (
                "This is a good book. "
                "(这是一本好书。)"
            ),
            "run": (
                "I like to run in the morning. "
                "(我喜欢在早上跑步。)"
            ),
            "beautiful": (
                "She is very beautiful. "
                "(她非常美丽。)"
            ),
            "computer": (
                "I use the computer to work. "
                "(我用电脑工作。)"
            ),
            "learn": (
                "We need to learn English every day. "
                "(我们需要每天学习英语。)"
            ),
            "friend": (
                "He is my best friend. "
                "(我最好的朋友。)"
            ),
            "happy": (
                "I feel very happy today. "
                "(我今天感到很开心。)"
            ),
            "work": (
                "I go to work at 9 o'clock. "
                "(我9点钟去上班。)"
            ),
            "time": (
                "Time flies. "
                "(时光飞逝。)"
            )
        }

        # 如果有基本例句，返回它
        if word.lower() in basic_examples:
            return basic_examples[word.lower()]

        # 获取单词翻译
        translation = self.get_word_translation(word)
        if translation:
            # 返回带翻译的默认例句
            return f"This is an example sentence with the word '{word}'. " \
                   f"(这是一个包含 '{word}' 的例句，意思是：{translation}。)"
        else:
            # 返回带占位翻译的默认例句
            return f"This is an example sentence with the word '{word}'. " \
                   f"(这是一个包含 '{word}' 的例句，暂无翻译。)"

    def get_unfamiliar_words(self, threshold: float = 0.3) -> List[str]:
        """获取不熟悉的单词

        Args:
            threshold: 熟悉度阈值

        Returns:
            List[str]: 不熟悉的单词列表
        """
        return [
            word for word, familiarity in self.word_familiarity.items()
            if familiarity < threshold
        ]

    def get_word_example(self, word: str, async_mode=False, callback=None) -> str:
        """获取单词的例句

        Args:
            word: 要获取例句的单词
            async_mode: 是否以异步方式获取（不阻塞UI线程）
            callback: 异步模式下的回调函数，接收参数：(example: str)

        Returns:
            str: 同步模式下返回包含例句和翻译的文本，如果获取失败返回默认例句
                 异步模式下返回None，结果通过callback返回
        """
        try:
            # 首先检查AI功能是否可用
            if self.ai_available and self.ai_manager:
                if async_mode:
                    # 异步模式 - 在新线程中执行
                    def fetch_example():
                        try:
                            example = self.ai_manager.example_sync(word)
                            if (example and "AI功能暂不可用" not in example and
                                    "生成例句失败" not in example):
                                # 检查返回的例句是否包含翻译
                                if "(" not in example and ")" not in example:
                                    # 如果没有翻译，添加一个基本翻译格式
                                    translation = self.get_word_translation(word) or "(未知翻译)"
                                    example = f"{example} (这是一个包含 '{word}' 的例句，意思是：{translation})"
                                log_info(f"获取例句成功: {word}")
                                if callback:
                                    callback(example)
                        except Exception as e:
                            log_error(f"异步获取例句失败: {str(e)}")
                            if callback:
                                callback(self._get_default_example(word))
                    
                    # 创建并启动线程
                    thread = threading.Thread(target=fetch_example, daemon=True)
                    thread.start()
                    return None
                else:
                    # 同步模式 - 直接调用
                    example = self.ai_manager.example_sync(word)
                    if (example and "AI功能暂不可用" not in example and
                            "生成例句失败" not in example):
                        # 检查返回的例句是否包含翻译
                        if "(" not in example and ")" not in example:
                            # 如果没有翻译，添加一个基本翻译格式
                            translation = self.get_word_translation(word) or "(未知翻译)"
                            example = f"{example} (这是一个包含 '{word}' 的例句，意思是：{translation})"
                        log_info(f"获取例句成功: {word}")
                        return example
                    else:
                        log_warning(f"获取例句失败: {word}, AI返回: {example}")
            else:
                log_warning("获取例句失败: AI功能不可用")
                
        except Exception as e:
            log_error(f"获取例句时发生异常: {str(e)}")
            if async_mode and callback:
                callback(self._get_default_example(word))
                return None

            # 获取默认例句
            return self._get_default_example(word)
        except Exception as e:
            log_error(f"获取例句异常: {str(e)}")
            # 返回带占位翻译的默认例句
            translation = self.get_word_translation(word) or "暂无翻译"
            return f"This is an example sentence with the word '{word}'. " \
                   f"(这是一个包含 '{word}' 的例句，意思是：{translation}。)"
            
    def get_example_sentence(self, word: str) -> str:
        """获取单词的例句（兼容性方法，调用get_word_example）
        
        Args:
            word: 单词
            
        Returns:
            str: 包含例句和翻译的文本，如果获取失败返回默认例句
        """
        return self.get_word_example(word)

    def is_ai_available(self) -> bool:
        """检查AI功能是否可用

        Returns:
            bool: AI功能是否可用
        """
        if not self.ai_manager:
            self._init_ai_manager()

        if not self.ai_available:
            return False

        try:
            import requests

            # 尝试连接Ollama API进行可用性检查
            try:
                requests.get("http://localhost:11434", timeout=2)
                return True
            except requests.exceptions.RequestException:
                # 如果连接失败，可能是Ollama未启动
                log_warning("无法连接到Ollama服务，AI功能不可用")
                return False
        except ImportError:
            # 如果requests模块未安装，也认为AI功能不可用
            log_warning("requests模块未安装，AI功能不可用")
            return False
        except Exception as e:
            log_error(f"检查AI可用性时出错: {str(e)}")
            return False

    def get_words_by_criteria(self, criteria: Dict) -> List[str]:
        """根据条件获取单词

        Args:
            criteria: 条件字典，支持以下键：
                - 'unfamiliar': 布尔值，表示是否只获取不熟悉的单词
                - 'difficult': 布尔值，表示是否只获取困难单词
                - 'min_length': 整数，表示单词的最小长度
                - 'max_length': 整数，表示单词的最大长度

        Returns:
            List[str]: 符合条件的单词列表
        """
        words = self.get_all_words()

        # 按条件过滤单词
        if criteria.get('unfamiliar', False):
            unfamiliar_words = self.get_unfamiliar_words()
            words = [word for word in words if word in unfamiliar_words]

        if criteria.get('difficult', False):
            difficult_words = self.get_difficult_words()
            words = [word for word in words if word in difficult_words]

        min_length = criteria.get('min_length')
        if min_length is not None:
            words = [word for word in words if len(word) >= min_length]

        max_length = criteria.get('max_length')
        if max_length is not None:
            words = [word for word in words if len(word) <= max_length]

        return words
    
    def check_today_progress_completed(self) -> bool:
        """
        检查单词学习模块是否标记为完成状态
        
        Returns:
            True/False: 今日学习是否已完成
        """
        try:
            # 从数据库查询今日是否完成学习
            today = datetime.now().strftime("%Y-%m-%d")
            result = self.db_manager.execute_read(
                """
                SELECT COUNT(*) as count 
                FROM exercise_sessions 
                WHERE exercise_type = 'completed' AND start_time LIKE ?
                """,
                (f"{today}%",)
            )
            
            if result and result[0]['count'] > 0:
                log_info("今日学习进度已完成")
                return True
            
            log_info("今日学习进度未完成")
            return False
        except Exception as e:
            log_error(f"检查今日学习进度失败: {str(e)}")
            return False
    
    def check_translation(self, word: str, user_translation: str, update_stats: bool = True) -> bool:
        """检查用户翻译是否正确
        
        Args:
            word: 单词
            user_translation: 用户输入的翻译
            update_stats: 是否更新统计信息
            
        Returns:
            bool: 翻译是否正确
        """
        try:
            import re

            def normalize(s: str) -> str:
                if s is None:
                    return ""
                s = s.strip().lower()
                # 移除括号内说明
                s = re.sub(r"\([^)]*\)", "", s)
                s = re.sub(r"（[^）]*）", "", s)
                # 替换常见分隔符为统一分隔符
                for sep in [";", "；", ",", "、", "/", "|"]:
                    s = s.replace(sep, ";")
                # 去掉标点符号（中英文）和多余空格
                import string as _string
                punct = re.escape(_string.punctuation) + "，。！？；：“”‘’、（）【】—…·、、·"
                s = re.sub(f"[{punct}]", "", s)
                s = re.sub(r"\s+", " ", s).strip()
                return s

            word_lower = word.lower()
            correct_translation = self.get_word_translation(word_lower)

            if not correct_translation:
                log_warning(f"无法检查翻译: 单词 '{word}' 没有对应的翻译")
                return False

            # If AI is available, prefer AI evaluation (more robust for synonyms/phrases)
            try:
                if self.ai_available and self.ai_manager:
                    try:
                        eval_result = self.ai_manager.evaluate_sync(correct_translation, user_translation)
                        if isinstance(eval_result, dict):
                            ai_is_correct = bool(eval_result.get('is_correct'))
                            similarity = float(eval_result.get('similarity', 0)) if eval_result.get('similarity') is not None else 0.0
                            # Accept when AI says correct, or similarity is high (>=0.8)
                            if ai_is_correct or similarity >= 0.8:
                                if update_stats:
                                    self.update_word_proficiency(word_lower, True)
                                    self.update_word_weight(word_lower, True, 0)
                                    log_info(f"AI判断翻译正确: {word} -> {user_translation}, similarity={similarity}")
                                return True
                            else:
                                if update_stats:
                                    self.update_word_proficiency(word_lower, False)
                                    self.update_word_weight(word_lower, False, 0)
                                    log_info(f"AI判断翻译错误: {word} -> 用户输入: {user_translation}, AI_similarity={similarity}")
                                return False
                    except Exception as ai_e:
                        log_warning(f"调用AI评估翻译失败，回退本地判断: {str(ai_e)}")

            except Exception:
                # 保守处理：若任何AI交互错误，不影响后续本地判断
                pass

            user_normalized = normalize(user_translation)

            # 将正确翻译按常见分隔符拆分为多个候选
            candidates_raw = re.split(r"[;,；、/|]", correct_translation)
            candidates = [normalize(c) for c in candidates_raw if c and c.strip()]

            # 如果没有分拆出候选，则把整个翻译作为单候选
            if not candidates:
                candidates = [normalize(correct_translation)]

            # 精确匹配或包含匹配（用户输入可能是简短形式）
            is_correct = False
            for cand in candidates:
                if not cand:
                    continue
                if user_normalized == cand:
                    is_correct = True
                    break
                # 容错：用户输入包含候选或候选包含用户输入（如只输入关键词）
                if user_normalized and (user_normalized in cand or cand in user_normalized):
                    is_correct = True
                    break

            if update_stats:
                if is_correct:
                    # 翻译正确，更新熟练度
                    self.update_word_proficiency(word_lower, True)
                    self.update_word_weight(word_lower, True, 0)
                    log_info(f"翻译正确: {word} -> {user_translation}")
                else:
                    # 翻译错误，更新熟练度
                    self.update_word_proficiency(word_lower, False)
                    self.update_word_weight(word_lower, False, 0)
                    log_info(f"翻译错误: {word} -> 用户输入: {user_translation}, 正确翻译: {correct_translation}")

            return is_correct
        except Exception as e:
            log_error(f"检查翻译失败: {str(e)}")
            return False