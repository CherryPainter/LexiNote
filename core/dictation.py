import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from logger import log_info, log_error, log_warning, log_wrong_word, log_exercise_start


class DictationManager:
    """听写管理器，负责听写练习的核心逻辑"""
    
    def __init__(self, word_manager):
        """初始化听写管理器
        
        Args:
            word_manager: WordManager实例，用于获取单词数据
        """
        self.word_manager = word_manager
        self.data_dir = 'data'
        
        # 数据文件路径
        self.dictation_history_file = os.path.join(self.data_dir, 'dictation_history.json')
        self.word_progress_file = os.path.join(self.data_dir, 'word_progress.json')
        self.familiar_words_file = os.path.join(self.data_dir, 'familiar_words.json')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化数据文件
        self._initialize_data_files()
        
        # 加载数据
        self.dictation_history = self._load_data(self.dictation_history_file)
        self.word_progress = self._load_data(self.word_progress_file)
        self.familiar_words = self._load_data(self.familiar_words_file)
        
        # 当前听写队列
        self.current_queue = []
        self.current_queue_index = 0
        self.current_mode = None
        self.current_source = None
        
    def _initialize_data_files(self):
        """初始化数据文件，确保文件存在并包含基本结构"""
        # 初始化听写历史
        if not os.path.exists(self.dictation_history_file):
            self._save_data(self.dictation_history_file, {})
            log_info("初始化听写历史文件")
        
        # 初始化单词进度
        if not os.path.exists(self.word_progress_file):
            initial_progress = {}
            # 为现有单词初始化进度
            for word in self.word_manager.word_dict:
                initial_progress[word] = {
                    "learned": False,
                    "weight": 1.0,
                    "last_practice": None
                }
            self._save_data(self.word_progress_file, initial_progress)
            log_info("初始化单词进度文件")
        
        # 初始化熟词库
        if not os.path.exists(self.familiar_words_file):
            self._save_data(self.familiar_words_file, {})
            log_info("初始化熟词库文件")
    
    def _load_data(self, file_path):
        """加载JSON数据文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log_error(f"加载文件 {file_path} 失败: {str(e)}")
            return {}
    
    def _save_data(self, file_path, data):
        """保存数据到JSON文件，先读取并合并旧数据"""
        try:
            # 先读取旧数据
            old_data = {}
            if os.path.exists(file_path):
                old_data = self._load_data(file_path)
            
            # 合并数据
            old_data.update(data)
            
            # 保存合并后的数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(old_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            log_error(f"保存文件 {file_path} 失败: {str(e)}")
            return False
    
    def select_word(self, source="library"):
        """选择一个单词用于单个听写模式
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            
        Returns:
            选中的单词字符串
        """
        if source == "today":
            # 获取今日学习单词
            today_words = self._get_today_learned_words()
            if today_words:
                return random.choice(today_words)
            else:
                log_info("没有今日学习的单词，将从词库中随机选择")
        elif source == "familiar":
            # 从熟词库中选择
            familiar_words = list(self.familiar_words.keys())
            if familiar_words:
                return random.choice(familiar_words)
        
        # 默认使用加权随机选择
        # 优先使用错误次数多的单词（困难单词）
        result = self.word_manager.get_word_by_weight()
        
        # 如果加权选择失败，使用随机选择
        if not result:
            result = self.word_manager.get_random_word()
        
        return result
    
    def build_queue(self, source="today", limit=10, filter_familiar=False):
        """构建听写队列
        
        Args:
            source: 单词来源，可选值："today", "library", "familiar"
            limit: 队列大小限制
            filter_familiar: 是否只包含熟词
            
        Returns:
            单词列表
        """
        words = []
        
        # 获取熟词列表
        familiar_words = []
        if hasattr(self.word_manager, 'get_familiar_words'):
            familiar_words = self.word_manager.get_familiar_words()
        else:
            familiar_words = list(self.familiar_words.keys())
        
        if source == "today":
            # 获取今日学习单词
            today_words = self._get_today_learned_words()
            words = today_words[:limit]
        elif source == "familiar":
            # 从熟词库中选择
            if hasattr(self.word_manager, 'get_familiar_words'):
                words = self.word_manager.get_familiar_words()
            else:
                words = list(self.familiar_words.keys())
            
            # 随机选择指定数量的单词
            if len(words) > limit:
                words = random.sample(words, limit)
        else:
            # 从全词库按权重选择
            all_words = list(self.word_manager.word_dict.keys())
            for _ in range(min(limit, len(all_words))):
                word = self.word_manager.get_word_by_weight()
                if word and word not in words:
                    words.append(word)
        
        # 处理过滤选项
        if filter_familiar and source != "familiar":
            # 只保留熟词
            words = [w for w in words if w in familiar_words]
        
        # 如果过滤后没有单词，使用原始单词列表
        if not words:
            if source == "today":
                words = self._get_today_learned_words()
            elif source == "library":
                words = list(self.word_manager.word_dict.keys())[:limit]
            elif source == "familiar":
                if hasattr(self.word_manager, 'get_familiar_words'):
                    words = self.word_manager.get_familiar_words()[:limit]
                else:
                    words = list(self.familiar_words.keys())[:limit]
        
        # 保存当前队列信息
        self.current_queue = words
        self.current_queue_index = 0
        self.current_source = source
        
        return words
    
    def _get_today_learned_words(self):
        """获取今日学习过的单词"""
        try:
            # 尝试直接使用word_manager中的方法，这样可以保持逻辑一致性
            if hasattr(self.word_manager, 'get_today_learned_words'):
                words = self.word_manager.get_today_learned_words()
                if words:
                    log_info(f"从word_manager获取今日学习单词: {len(words)}个")
                    return words
            
            # 备用方法：直接从word_progress中获取
            today = datetime.now().strftime('%Y-%m-%d')
            today_words = []
            
            for word, progress in self.word_progress.items():
                # 检查单词是否已学习
                if progress.get("learned", False):
                    # 检查最后练习日期或最后学习日期
                    last_date = None
                    
                    # 尝试从last_practice获取
                    if progress.get("last_practice"):
                        last_date = progress["last_practice"].split(' ')[0] if isinstance(progress["last_practice"], str) else None
                    # 尝试从last_learned获取（兼容learning.py中的记录方式）
                    elif progress.get("last_learned"):
                        last_learned = progress["last_learned"]
                        if isinstance(last_learned, str):
                            if 'T' in last_learned:  # ISO格式
                                last_date = last_learned.split('T')[0]
                            else:  # 普通格式
                                last_date = last_learned.split(' ')[0]
                    
                    if last_date == today:
                        today_words.append(word)
            
            log_info(f"从word_progress获取今日学习单词: {len(today_words)}个")
            return today_words
        except Exception as e:
            log_error(f"获取今日学习单词失败: {str(e)}")
            return []
    
    def record_result(self, word, is_correct, time_spent=0):
        """记录听写结果并更新单词进度和权重
        
        Args:
            word: 单词
            is_correct: 是否正确
            time_spent: 拼写所用时间（秒）
        """
        # 更新单词进度
        if word not in self.word_progress:
            self.word_progress[word] = {
                "learned": True,
                "weight": 1.0,
                "last_practice": None,
                "avg_response_time": 0,
                "response_times": []  # 确保初始化响应时间列表
            }
        # 检查现有单词记录是否缺少response_times键
        elif "response_times" not in self.word_progress[word]:
            self.word_progress[word]["response_times"] = []
            self.word_progress[word]["avg_response_time"] = 0
        
        # 更新进度信息
        self.word_progress[word]["last_practice"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 记录响应时间
        self.word_progress[word]["response_times"].append(time_spent)
        # 保持最近10次的记录
        if len(self.word_progress[word]["response_times"]) > 10:
            self.word_progress[word]["response_times"] = self.word_progress[word]["response_times"][-10:]
        # 更新平均响应时间
        self.word_progress[word]["avg_response_time"] = sum(self.word_progress[word]["response_times"]) / len(self.word_progress[word]["response_times"])
        
        # 更新权重（复用WordManager的逻辑，并考虑时间因素）
        self.word_manager.update_word_weight(word, is_correct, time_spent)
        
        # 更新熟悉度
        if hasattr(self.word_manager, 'update_word_familiarity'):
            if is_correct:
                self.word_manager.update_word_familiarity(word, 0.1)  # 正确增加熟悉度
            else:
                self.word_manager.update_word_familiarity(word, -0.15)  # 错误降低熟悉度
        
        # 同步更新到单词进度文件
        self.word_progress[word]["weight"] = self.word_manager.word_weights.get(word, 1.0)
        self._save_data(self.word_progress_file, {word: self.word_progress[word]})
        
        # 更新熟词库
        self._update_familiar_words(word, is_correct)
        
        # 记录到历史记录
        self._record_to_history(word, "correct" if is_correct else "misspelled", time_spent)
    
    def _update_familiar_words(self, word, is_correct):
        """更新熟词库
        
        Args:
            word: 单词
            is_correct: 是否正确
        """
        # 优先使用WordManager的熟悉度管理功能
        if hasattr(self.word_manager, 'get_familiar_words'):
            familiar_words = self.word_manager.get_familiar_words()
            if set(familiar_words) != set(self.familiar_words.keys()):
                # 同步WordManager的熟词列表
                new_familiar_words = {}
                for familiar_word in familiar_words:
                    if familiar_word not in self.familiar_words:
                        new_familiar_words[familiar_word] = {
                            "mastered": True,
                            "practice_count": 3  # 默认练习次数
                        }
                
                # 合并新的熟词数据
                if new_familiar_words:
                    self.familiar_words.update(new_familiar_words)
                    self._save_data(self.familiar_words_file, new_familiar_words)
        else:
            # 传统逻辑作为备用
            if word not in self.familiar_words:
                self.familiar_words[word] = {
                    "mastered": False,
                    "practice_count": 0
                }
            
            # 更新练习次数
            self.familiar_words[word]["practice_count"] += 1
            
            # 如果连续正确多次，标记为掌握
            if is_correct:
                # 假设连续3次正确视为掌握
                if self.familiar_words[word]["practice_count"] >= 3:
                    self.familiar_words[word]["mastered"] = True
            else:
                # 错误时重置掌握状态
                self.familiar_words[word]["mastered"] = False
            
            self._save_data(self.familiar_words_file, {word: self.familiar_words[word]})
    
    def _record_to_history(self, word, result, time_spent):
        """将听写结果记录到历史记录中
        
        Args:
            word: 单词
            result: 结果（correct/misspelled）
            time_spent: 拼写所用时间（秒）
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        if today not in self.dictation_history:
            self.dictation_history[today] = {
                "mode": self.current_mode or "single",
                "words": []
            }
        
        # 添加单词记录
        self.dictation_history[today]["words"].append({
            "word": word,
            "result": result,
            "time_spent": time_spent,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        self._save_data(self.dictation_history_file, {today: self.dictation_history[today]})
    
    def summarize(self, queue=None):
        """生成听写总结报告
        
        Args:
            queue: 要总结的队列，如果为None则总结当前队列
            
        Returns:
            包含总结信息的字典
        """
        if queue is None:
            queue = self.current_queue
        
        # 从历史记录中获取当前队列的结果
        today = datetime.now().strftime('%Y-%m-%d')
        today_records = self.dictation_history.get(today, {}).get("words", [])
        
        # 筛选当前队列的记录
        queue_records = [r for r in today_records if r["word"] in queue]
        
        # 计算统计信息
        total = len(queue)
        correct = sum(1 for r in queue_records if r["result"] == "correct")
        accuracy = correct / total if total > 0 else 0
        missed = [r["word"] for r in queue_records if r["result"] != "correct"]
        
        # 尝试获取AI建议
        suggestion = "继续保持练习！"
        try:
            if self.word_manager.ai_available:
                # 计算平均响应时间
                total_time_spent = sum(r.get("time_spent", 0) for r in queue_records)
                avg_response_time = total_time_spent / len(queue_records) if queue_records else 0
                
                # 计算正确和错误的响应时间
                correct_records = [r for r in queue_records if r["result"] == "correct"]
                incorrect_records = [r for r in queue_records if r["result"] != "correct"]
                
                avg_correct_time = sum(r.get("time_spent", 0) for r in correct_records) / len(correct_records) if correct_records else 0
                avg_incorrect_time = sum(r.get("time_spent", 0) for r in incorrect_records) / len(incorrect_records) if incorrect_records else 0
                
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
        return {
            "current": self.current_queue_index + 1,
            "total": len(self.current_queue)
        }
    
    def next_in_queue(self):
        """获取队列中的下一个单词
        
        Returns:
            下一个单词字符串，如果队列为空则返回None
        """
        if self.current_queue_index < len(self.current_queue):
            word = self.current_queue[self.current_queue_index]
            self.current_queue_index += 1
            return word
        return None
    
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
        return self.current_queue_index < len(self.current_queue)
    
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
            return [w for w in words if w in self.familiar_words]
    
    def mark_word_as_learned(self, word):
        """标记单词为已学习
        
        Args:
            word: 单词
        """
        if word not in self.word_progress:
            self.word_progress[word] = {
                "learned": True,
                "weight": 1.0,
                "last_practice": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            self.word_progress[word]["learned"] = True
            self.word_progress[word]["last_practice"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self._save_data(self.word_progress_file, {word: self.word_progress[word]})
    
    def get_familiar_words_count(self):
        """获取熟词数量
        
        Returns:
            熟词数量
        """
        return len([w for w, info in self.familiar_words.items() if info.get("mastered", False)])
    
    def get_today_progress(self):
        """获取今日听写进度
        
        Returns:
            今日听写统计信息
        """
        today = datetime.now().strftime('%Y-%m-%d')
        today_records = self.dictation_history.get(today, {}).get("words", [])
        
        total = len(today_records)
        correct = sum(1 for r in today_records if r["result"] == "correct")
        accuracy = correct / total if total > 0 else 0
        
        return {
            "total": total,
            "correct": correct,
            "accuracy": round(accuracy, 2)
        }