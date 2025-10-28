"""
学习模式核心逻辑模块

实现用户主动学习单词的功能，包括批次获取、掌握度标记、进度保存等
"""
from typing import List, Dict, Optional
from datetime import datetime
import json
import os


class LearningManager:
    """
    学习模式管理器，负责学习单词的核心逻辑
    """
    
    def __init__(self, data_manager, scheduler, audio_player, logger):
        """
        初始化学习管理器
        
        Args:
            data_manager: 数据管理器实例，用于读写JSON文件
            scheduler: 调度器实例，用于权重采样
            audio_player: 音频播放器实例，用于播放单词发音
            logger: 日志记录器实例，用于记录操作日志
        """
        self.data_manager = data_manager
        self.scheduler = scheduler
        self.audio_player = audio_player
        
        # 导入日志函数，以确保即使logger没有所需方法也能正常工作
        try:
            from logger import log_info, log_error
        except ImportError:
            # 如果导入失败，定义简单的日志函数
            def log_info(msg):
                print(f"INFO: {msg}")
            
            def log_error(msg):
                print(f"ERROR: {msg}")
        
        # 如果logger没有所需的方法，我们将使用导入的日志函数
        # 修复lambda函数参数问题
        class LoggerWrapper:
            def __init__(self, logger_obj, log_info_func, log_error_func):
                self.logger_obj = logger_obj
                self.log_info_func = log_info_func
                self.log_error_func = log_error_func
            
            def log_info(self, msg):
                if hasattr(self.logger_obj, 'log_info'):
                    # 检查logger.log_info是方法还是函数
                    if callable(getattr(self.logger_obj, 'log_info')):
                        try:
                            # 尝试作为方法调用（带self）
                            self.logger_obj.log_info(msg)
                        except TypeError:
                            # 如果失败，尝试作为函数调用（不带self）
                            getattr(self.logger_obj, 'log_info')(msg)
                else:
                    self.log_info_func(msg)
            
            def log_error(self, msg):
                if hasattr(self.logger_obj, 'log_error'):
                    # 检查logger.log_error是方法还是函数
                    if callable(getattr(self.logger_obj, 'log_error')):
                        try:
                            # 尝试作为方法调用（带self）
                            self.logger_obj.log_error(msg)
                        except TypeError:
                            # 如果失败，尝试作为函数调用（不带self）
                            getattr(self.logger_obj, 'log_error')(msg)
                else:
                    self.log_error_func(msg)
        
        self.logger = LoggerWrapper(logger, log_info, log_error)
        
        # 学习统计
        self.current_batch = []
        self.mastered_count = 0
        self.review_count = 0
        
        # 加载学习进度数据
        self.word_progress = self._load_word_progress()
    
    def _load_word_progress(self) -> Dict[str, Dict]:
        """
        加载单词学习进度数据
        
        Returns:
            Dict: 单词学习进度字典
        """
        try:
            # 使用word_manager的_load_data方法，指定完整路径
            return self.data_manager._load_data('data/word_progress.json')
        except Exception as e:
            # 使用word_manager作为logger记录错误
            self.logger.log_error(f"加载单词进度数据失败: {str(e)}")
            return {}
    
    def get_batch(self, batch_size: int = 10) -> List[str]:
        """
        获取本轮学习的单词列表
        
        Args:
            batch_size: 批次大小，默认10个单词
            
        Returns:
            List[str]: 单词列表
        """
        try:
            # 直接从word_manager获取所有单词
            word_list = self.data_manager.get_all_words()
            if not word_list:
                # 使用word_manager作为logger记录错误
                self.logger.log_error(f"获取学习批次失败: 单词列表为空")
                return []
            
            all_words = word_list  # 直接使用返回的单词列表
            
            # 如果单词总数少于批次大小，则全部返回
            if len(all_words) <= batch_size:
                self.current_batch = all_words
                return all_words
            
            # 使用scheduler（即word_manager）基于权重获取单词
            selected_words = []
            remaining_words = set(all_words)
            
            while len(selected_words) < batch_size and remaining_words:
                # 使用word_manager的get_word_by_weight方法
                next_word = self.scheduler.get_word_by_weight()
                if next_word in remaining_words:
                    selected_words.append(next_word)
                    remaining_words.remove(next_word)
                
                # 避免无限循环的保护措施
                if len(selected_words) >= len(all_words):
                    break
            
            # 如果基于权重的选择没有填满批次，从剩余单词中随机补充
            if len(selected_words) < batch_size:
                selected_words.extend(list(remaining_words)[:batch_size - len(selected_words)])
            
            self.current_batch = selected_words
            self.mastered_count = 0
            self.review_count = 0
            
            # 使用word_manager作为logger记录信息
            self.logger.log_info(f"获取学习批次成功，共{len(selected_words)}个单词")
            return selected_words
            
        except Exception as e:
            # 使用word_manager作为logger记录错误
            self.logger.log_error(f"获取学习批次失败: {str(e)}")
            # 返回空列表作为回退
            return []
    
    def mark_mastered(self, word: str):
        """
        用户标记单词为已掌握
        
        Args:
            word: 单词
        """
        try:
            # 更新学习进度
            if word not in self.word_progress:
                self.word_progress[word] = {
                    'learned': True,
                    'last_learned': datetime.now().isoformat(),
                    'mastery_score': 0.0
                }
            
            # 更新掌握度分数
            current_score = self.word_progress[word].get('mastery_score', 0.0)
            self.word_progress[word]['mastery_score'] = min(1.0, current_score + 0.25)
            self.word_progress[word]['last_learned'] = datetime.now().isoformat()
            self.word_progress[word]['learned'] = True
            
            # 使用word_manager的_update_progress方法更新权重（模拟正确回答的行为）
            # 我们需要直接操作权重文件，因为WordManager的update_word_weight方法会自动调用_update_progress
            # 所以我们直接修改权重文件
            weights = self.data_manager._load_data('data/word_weights.json')
            current_weight = weights.get(word, 1.0)
            weights[word] = max(0.1, current_weight * 0.8)
            self.data_manager._save_data('data/word_weights.json', {word: weights[word]})
            
            self.mastered_count += 1
            # 使用word_manager作为logger记录信息
            self.logger.log_info(f"标记单词 '{word}' 为已掌握，掌握度: {self.word_progress[word]['mastery_score']}")
            
        except Exception as e:
            # 使用word_manager作为logger记录错误
            self.logger.log_error(f"标记单词 '{word}' 为已掌握失败: {str(e)}")
    
    def mark_review(self, word: str):
        """
        用户标记单词需要复习
        
        Args:
            word: 单词
        """
        try:
            # 更新学习进度
            if word not in self.word_progress:
                self.word_progress[word] = {
                    'learned': True,
                    'last_learned': datetime.now().isoformat(),
                    'mastery_score': 0.0
                }
            
            # 更新掌握度分数
            current_score = self.word_progress[word].get('mastery_score', 0.0)
            self.word_progress[word]['mastery_score'] = max(0.0, current_score - 0.1)
            self.word_progress[word]['last_learned'] = datetime.now().isoformat()
            self.word_progress[word]['learned'] = True
            
            # 直接操作权重文件，增加权重
            weights = self.data_manager._load_data('data/word_weights.json')
            current_weight = weights.get(word, 1.0)
            weights[word] = min(5.0, current_weight + 0.3)
            self.data_manager._save_data('data/word_weights.json', {word: weights[word]})
            
            self.review_count += 1
            # 使用word_manager作为logger记录信息
            self.logger.log_info(f"标记单词 '{word}' 需要复习，掌握度: {self.word_progress[word]['mastery_score']}")
            
        except Exception as e:
            # 使用word_manager作为logger记录错误
            self.logger.log_error(f"标记单词 '{word}' 需要复习失败: {str(e)}")
    
    def play_pronunciation(self, word: str) -> bool:
        """
        播放单词发音
        
        Args:
            word: 要播放发音的单词
            
        Returns:
            bool: 是否播放成功
        """
        try:
            # 调用音频播放器播放单词发音
            result = self.audio_player.play_pronunciation(word)
            if result:
                self.logger.log_info(f"播放单词发音: {word}")
            else:
                self.logger.log_error(f"播放单词发音失败: {word}")
            return result
        except Exception as e:
            self.logger.log_error(f"播放单词发音异常: {word}, 错误: {str(e)}")
            return False
    
    def save_progress(self) -> bool:
        """
        保存学习进度
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 执行日衰减
            self._apply_daily_decay()
            
            # 使用word_manager的_save_data方法，指定完整路径
            self.data_manager._save_data('data/word_progress.json', self.word_progress)
            
            # 更新每日学习记录
            self._update_daily_learning()
            
            # 记录学习统计
            self.logger.log_info(
                f"保存学习进度成功，本轮学习: {len(self.current_batch)} 词，"
                f"掌握: {self.mastered_count} 词，需复习: {self.review_count} 词"
            )
            
            return True
        except Exception as e:
            # 使用word_manager作为logger记录错误
            self.logger.log_error(f"保存学习进度失败: {str(e)}")
            return False
    
    def _update_daily_learning(self):
        """
        更新每日学习记录，标记今日学习为已完成
        """
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 获取当前的每日学习记录
            daily_learning = self.data_manager._load_data('data/daily_learning.json')
            
            # 更新今日记录
            if today not in daily_learning:
                daily_learning[today] = {}
            
            # 标记为已完成
            daily_learning[today]['completed'] = True
            daily_learning[today]['completed_at'] = datetime.now().isoformat()
            daily_learning[today]['words_learned'] = self.mastered_count
            daily_learning[today]['words_to_review'] = self.review_count
            
            # 保存更新后的记录
            self.data_manager._save_data('data/daily_learning.json', daily_learning)
            
            self.logger.log_info(f"更新每日学习记录，今日学习已完成")
        except Exception as e:
            self.logger.log_error(f"更新每日学习记录失败: {str(e)}")
    
    def _apply_daily_decay(self):
        """
        执行每日衰减，模拟遗忘过程
        """
        try:
            # 使用word_manager的_load_data方法，指定完整路径
            weights = self.data_manager._load_data('data/word_weights.json')
            
            # 对所有权重进行轻微衰减
            for word in weights:
                weights[word] = min(5.0, weights[word] * 0.98)
            
            # 保存更新后的权重
            self.data_manager._save_data('data/word_weights.json', weights)
            
        except Exception as e:
            # 使用word_manager作为logger记录错误
            self.logger.log_error(f"执行每日衰减失败: {str(e)}")
    
    def get_current_stats(self) -> Dict[str, int]:
        """
        获取当前批次的学习统计信息
        
        Returns:
            Dict: 统计信息字典
        """
        return {
            'total': len(self.current_batch),
            'mastered': self.mastered_count,
            'review': self.review_count,
            'remaining': len(self.current_batch) - self.mastered_count - self.review_count
        }
    
    def get_word_definition(self, word: str) -> Optional[str]:
        """
        获取单词的中文释义
        
        Args:
            word: 单词
            
        Returns:
            Optional[str]: 单词释义，如果不存在返回None
        """
        try:
            # 使用get_word_translation方法获取单词翻译
            return self.data_manager.get_word_translation(word)
        except Exception as e:
            self.logger.log_error(f"获取单词释义失败: {word}, 错误: {str(e)}")
            return None