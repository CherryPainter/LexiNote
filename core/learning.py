"""
学习模式核心逻辑模块

实现用户主动学习单词的功能，包括批次获取、掌握度标记、进度保存等
采用模块化设计，将不同职责分离到不同类中
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import random


class ForgettingCurve:
    """
    遗忘曲线算法实现，用于计算单词的复习优先级
    
    使用改进的艾宾浩斯遗忘曲线模型
    """
    
    def __init__(self, base_weight: float = 1.0):
        """
        初始化遗忘曲线算法
        
        Args:
            base_weight: 基础权重值
        """
        self.base_weight = base_weight
        # 遗忘曲线参数
        self.forget_rate = 0.02  # 基础遗忘率
        self.mastery_factor = 0.8  # 掌握度影响因子
        self.max_weight = 5.0  # 最大权重
        self.min_weight = 0.1  # 最小权重
    
    def calculate_weight(self, mastery_score: float, last_reviewed: Optional[datetime] = None) -> float:
        """
        根据掌握度和最后复习时间计算单词权重
        
        Args:
            mastery_score: 掌握度分数 (0.0-1.0)
            last_reviewed: 最后复习时间
            
        Returns:
            float: 计算得到的单词权重
        """
        if not last_reviewed:
            return self.max_weight
        
        # 计算时间间隔（天）
        time_interval = (datetime.now() - last_reviewed).days
        
        # 基础权重
        base_weight = self.base_weight
        
        # 应用遗忘曲线
        # 公式: weight = base_weight * (1 - mastery_score * mastery_factor) * (1 + time_interval * forget_rate)
        weight = base_weight * (1 - mastery_score * self.mastery_factor) * (1 + time_interval * self.forget_rate)
        
        # 限制权重范围
        return max(self.min_weight, min(self.max_weight, weight))
    
    def update_mastery_score(self, current_score: float, was_correct: bool) -> float:
        """
        根据学习结果更新掌握度分数
        
        Args:
            current_score: 当前掌握度分数
            was_correct: 是否正确回答
            
        Returns:
            float: 更新后的掌握度分数
        """
        if was_correct:
            # 正确回答，增加掌握度
            new_score = current_score + 0.15
        else:
            # 错误回答，降低掌握度
            new_score = current_score - 0.1
        
        # 限制掌握度范围在0-1之间
        return max(0.0, min(1.0, new_score))


class WordSelector:
    """
    单词选择器，负责从词库中选择适合学习的单词
    """
    
    def __init__(self, word_manager):
        """
        初始化单词选择器
        
        Args:
            word_manager: 单词管理器实例，用于获取单词数据
        """
        self.word_manager = word_manager
    
    def select_words(self, batch_size: int = 10, set_id: Optional[int] = None) -> List[Dict]:
        """
        从指定词库选择单词批次
        
        Args:
            batch_size: 批次大小
            set_id: 词库ID，默认使用当前激活词库
            
        Returns:
            List[Dict]: 选择的单词列表
        """
        try:
            if set_id:
                words = self.word_manager.get_words_by_set_id(set_id)
            else:
                words = self.word_manager.get_words_from_active_set()
            
            if not words:
                return []
            
            # 如果单词数量不足批次大小，返回所有单词
            if len(words) <= batch_size:
                return words
            
            # 优先选择掌握度低的单词，但保留一定随机性
            weighted_words = []
            for word in words:
                # 计算选择权重
                mastery_score = word.get('mastery_score', 0.0)
                weight = 1.0 - mastery_score  # 掌握度越低，权重越高
                weighted_words.append((word, weight))
            
            # 基于权重选择单词
            selected = random.choices(
                [w[0] for w in weighted_words],
                weights=[w[1] for w in weighted_words],
                k=batch_size
            )
            
            return selected
            
        except Exception as e:
            from logger import log_error
            log_error(f"选择单词失败: {str(e)}")
            # 回退到随机选择
            if set_id:
                words = self.word_manager.get_words_by_set_id(set_id)
            else:
                words = self.word_manager.get_words_from_active_set()
            
            if not words:
                return []
            
            return random.sample(words, min(batch_size, len(words)))


class LearningProgress:
    """
    学习进度管理器，负责跟踪和保存学习进度
    """
    
    def __init__(self, data_dir: str = 'data'):
        """
        初始化学习进度管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.progress_file = os.path.join(data_dir, 'word_progress.json')
        self.daily_file = os.path.join(data_dir, 'daily_learning.json')
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 加载进度数据
        self.word_progress = self._load_progress()
        self.daily_progress = self._load_daily_progress()
    
    def _load_progress(self) -> Dict[str, Dict]:
        """
        加载单词学习进度
        
        Returns:
            Dict[str, Dict]: 单词学习进度字典
        """
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            from logger import log_error
            log_error(f"加载学习进度失败: {str(e)}")
            return {}
    
    def _load_daily_progress(self) -> Dict[str, Dict]:
        """
        加载每日学习进度
        
        Returns:
            Dict[str, Dict]: 每日学习进度字典
        """
        try:
            if os.path.exists(self.daily_file):
                with open(self.daily_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            from logger import log_error
            log_error(f"加载每日进度失败: {str(e)}")
            return {}
    
    def get_word_progress(self, word: str) -> Dict:
        """
        获取单个单词的学习进度
        
        Args:
            word: 单词
            
        Returns:
            Dict: 单词学习进度
        """
        if word not in self.word_progress:
            self.word_progress[word] = {
                'learned': False,
                'last_learned': None,
                'mastery_score': 0.0,
                'review_count': 0,
                'correct_count': 0
            }
        return self.word_progress[word]
    
    def update_word_progress(self, word: str, was_correct: bool):
        """
        更新单词学习进度
        
        Args:
            word: 单词
            was_correct: 是否正确回答
        """
        # 获取当前进度
        progress = self.get_word_progress(word)
        
        # 更新进度
        progress['learned'] = True
        progress['last_learned'] = datetime.now().isoformat()
        progress['review_count'] += 1
        
        if was_correct:
            progress['correct_count'] += 1
        
        # 更新掌握度分数
        curve = ForgettingCurve()
        current_score = progress['mastery_score']
        progress['mastery_score'] = curve.update_mastery_score(current_score, was_correct)
        
        # 保存更新
        self._save_progress()
    
    def _save_progress(self):
        """
        保存学习进度到文件
        """
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.word_progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            from logger import log_error
            log_error(f"保存学习进度失败: {str(e)}")
    
    def get_today_progress(self) -> Dict:
        """
        获取今日学习进度
        
        Returns:
            Dict: 今日学习进度
        """
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.daily_progress:
            self.daily_progress[today] = {
                'current_batch': [],
                'current_index': 0,
                'batch_size': 0,
                'mastered_words': [],
                'review_words': [],
                'progress': {
                    'total': 0,
                    'mastered': 0,
                    'review': 0
                },
                'last_updated': datetime.now().isoformat(),
                'completed': False
            }
        return self.daily_progress[today]
    
    def update_daily_progress(self, current_batch: List, current_index: int, 
                             mastered_count: int, review_count: int, 
                             finished: bool = False):
        """
        更新每日学习进度
        
        Args:
            current_batch: 当前学习批次
            current_index: 当前单词索引
            mastered_count: 已掌握单词数量
            review_count: 需复习单词数量
            finished: 是否完成学习
        """
        today = datetime.now().strftime('%Y-%m-%d')
        today_progress = self.get_today_progress()
        
        today_progress.update({
            'current_batch': current_batch,
            'current_index': current_index,
            'batch_size': len(current_batch),
            'progress': {
                'total': len(current_batch),
                'mastered': mastered_count,
                'review': review_count
            },
            'last_updated': datetime.now().isoformat()
        })
        
        if finished:
            today_progress.update({
                'completed': True,
                'completed_at': datetime.now().isoformat()
            })
        
        # 保存每日进度
        self._save_daily_progress()
    
    def _save_daily_progress(self):
        """
        保存每日学习进度到文件
        """
        try:
            with open(self.daily_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            from logger import log_error
            log_error(f"保存每日进度失败: {str(e)}")


class LearningScheduler:
    """
    学习调度器，负责管理学习流程和学习计划
    """
    
    def __init__(self, word_selector: WordSelector, progress_manager: LearningProgress):
        """
        初始化学习调度器
        
        Args:
            word_selector: 单词选择器实例
            progress_manager: 学习进度管理器实例
        """
        self.word_selector = word_selector
        self.progress_manager = progress_manager
    
    def get_next_learning_batch(self, batch_size: int = 10, set_id: Optional[int] = None) -> List[Dict]:
        """
        获取下一个学习批次
        
        Args:
            batch_size: 批次大小
            set_id: 词库ID
            
        Returns:
            List[Dict]: 学习单词列表
        """
        # 选择单词
        words = self.word_selector.select_words(batch_size, set_id)
        
        # 为每个单词添加学习进度信息
        for word in words:
            word_text = word['word']
            progress = self.progress_manager.get_word_progress(word_text)
            word['mastery_score'] = progress['mastery_score']
            
            if progress['last_learned']:
                word['last_learned'] = datetime.fromisoformat(progress['last_learned'])
            else:
                word['last_learned'] = None
        
        return words


class LearningManager:
    """
    学习模式管理器，作为学习功能的核心协调器
    整合各个学习相关模块，提供统一的API接口
    """
    
    def __init__(self, word_manager, audio_player):
        """
        初始化学习管理器
        
        Args:
            word_manager: 单词管理器实例
            audio_player: 音频播放器实例
        """
        self.word_manager = word_manager
        self.audio_player = audio_player
        
        # 初始化日志
        try:
            from logger import log_info, log_error
            self.log_info = log_info
            self.log_error = log_error
        except ImportError:
            # 如果导入失败，定义简单的日志函数
            self.log_info = lambda msg: print(f"INFO: {msg}")
            self.log_error = lambda msg: print(f"ERROR: {msg}")
        
        # 初始化学习组件
        self.word_selector = WordSelector(word_manager)
        self.progress_manager = LearningProgress()
        self.scheduler = LearningScheduler(self.word_selector, self.progress_manager)
        
        # 学习状态
        self.current_batch = []
        self.current_index = -1  # 当前单词索引，初始为-1表示未开始
        self.mastered_count = 0
        self.review_count = 0
    
    def _load_word_progress(self) -> Dict[str, Dict]:
        """
        加载单词学习进度
        
        Returns:
            Dict[str, Dict]: 单词学习进度字典
        """
        self.log_info("_load_word_progress方法已更新，使用LearningProgress类")
        return self.progress_manager.word_progress

    def get_batch(self, batch_size: int = 10) -> List[Dict]:
        """
        获取学习单词批次
        
        Args:
            batch_size: 批次大小，默认10个单词
            
        Returns:
            List[Dict]: 单词列表
        """
        try:
            # 使用调度器获取学习批次
            self.current_batch = self.scheduler.get_next_learning_batch(batch_size)
            
            if not self.current_batch:
                self.log_error("当前激活词库中没有单词")
                return []
            
            # 初始化学习状态
            self.current_index = 0
            self.mastered_count = 0
            self.review_count = 0
            
            # 记录日志
            self.log_info(f"获取学习单词批次: {len(self.current_batch)} 个单词")
            
            return self.current_batch
        except Exception as e:
            self.log_error(f"获取学习单词批次失败: {str(e)}")
            return []

    def mark_mastered(self, word: str):
        """
        用户标记单词为已掌握
        
        Args:
            word: 单词
        """
        try:
            # 更新单词进度（掌握度增加）
            self.progress_manager.update_word_progress(word, True)
            
            # 更新统计信息
            self.mastered_count += 1
            
            # 更新每日进度
            self.progress_manager.update_daily_progress(
                self.current_batch,
                self.current_index,
                self.mastered_count,
                self.review_count
            )
            
            # 记录日志
            progress = self.progress_manager.get_word_progress(word)
            self.log_info(f"标记单词 '{word}' 为已掌握，掌握度: {progress['mastery_score']}")
            
        except Exception as e:
            self.log_error(f"标记单词 '{word}' 为已掌握失败: {str(e)}")

    def mark_review(self, word: str):
        """
        用户标记单词需要复习
        
        Args:
            word: 单词
        """
        try:
            # 更新单词进度（掌握度降低）
            self.progress_manager.update_word_progress(word, False)
            
            # 更新统计信息
            self.review_count += 1
            
            # 更新每日进度
            self.progress_manager.update_daily_progress(
                self.current_batch,
                self.current_index,
                self.mastered_count,
                self.review_count
            )
            
            # 记录日志
            progress = self.progress_manager.get_word_progress(word)
            self.log_info(f"标记单词 '{word}' 需要复习，掌握度: {progress['mastery_score']}")
            
        except Exception as e:
            self.log_error(f"标记单词 '{word}' 需要复习失败: {str(e)}")

    def save_progress(self, finished=False) -> bool:
        """
        保存学习进度
        
        Args:
            finished: 是否完成本批次学习
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 更新每日进度
            self.progress_manager.update_daily_progress(
                self.current_batch,
                self.current_index,
                self.mastered_count,
                self.review_count,
                finished=finished
            )
            
            # 记录学习统计
            self.log_info(
                f"保存学习进度成功，本轮学习: {len(self.current_batch)} 词，"
                f"掌握: {self.mastered_count} 词，需复习: {self.review_count} 词"
            )
            
            return True
        except Exception as e:
            self.log_error(f"保存学习进度失败: {str(e)}")
            return False

    def _update_daily_learning(self, finished=False):
        """
        更新每日学习记录（已废弃）
        
        Args:
            finished: 是否完成本批次学习
        """
        self.log_info("_update_daily_learning方法已废弃，使用LearningProgress.update_daily_progress替代")

    def _apply_daily_decay(self):
        """
        执行每日衰减（已废弃）
        
        此功能已整合到LearningProgress和ForgettingCurve类中
        """
        self.log_info("_apply_daily_decay方法已废弃，使用ForgettingCurve自动计算权重")

    def load_daily_progress(self) -> bool:
        """
        加载今日的学习进度，如果有的话
        
        Returns:
            bool: 是否成功加载了进度
        """
        try:
            today_progress = self.progress_manager.get_today_progress()
            
            if today_progress['current_batch'] and not today_progress['completed']:
                self.current_batch = today_progress['current_batch']
                self.current_index = today_progress['current_index']
                self.mastered_count = today_progress['progress']['mastered']
                self.review_count = today_progress['progress']['review']
                
                self.log_info(f"已加载今日保存的学习批次")
                return True
            
            return False
        except Exception as e:
            self.log_error(f"加载今日进度失败: {str(e)}")
            return False

    def get_word_definition(self, word: str) -> Optional[str]:
        """
        获取单词的中文释义
        
        Args:
            word: 单词
            
        Returns:
            Optional[str]: 单词释义，如果不存在返回None
        """
        try:
            # 使用word_manager获取单词释义
            return self.word_manager.get_word_translation(word)
        except Exception as e:
            self.log_error(f"获取单词释义失败: {word}, 错误: {str(e)}")
            return None

    # 新增方法
    def load_saved_batch(self) -> bool:
        """
        加载已保存的学习批次
        
        Returns:
            bool: 是否成功加载
        """
        return self.load_daily_progress()

    def next_word(self) -> Optional[Dict]:
        """
        切换到下一个单词
        
        Returns:
            Optional[Dict]: 下一个单词信息，None表示已完成所有单词
        """
        if self.current_index < len(self.current_batch) - 1:
            self.current_index += 1
            
            # 更新每日进度
            self.progress_manager.update_daily_progress(
                self.current_batch,
                self.current_index,
                self.mastered_count,
                self.review_count
            )
            
            return self.current_batch[self.current_index]
        else:
            # 学习完成
            self.progress_manager.update_daily_progress(
                self.current_batch,
                self.current_index,
                self.mastered_count,
                self.review_count,
                finished=True
            )
            
            self.log_info("学习批次已完成")
            return None

    def start_new_batch(self, batch_size: int = 10, set_id: Optional[int] = None) -> bool:
        """
        开始新的学习批次
        
        Args:
            batch_size: 批次大小
            set_id: 词库ID，默认使用当前激活词库
            
        Returns:
            bool: 是否成功开始新批次
        """
        try:
            # 获取新的学习批次
            self.current_batch = self.scheduler.get_next_learning_batch(batch_size, set_id)
            
            if not self.current_batch:
                self.log_error("无法获取新的学习批次")
                return False
            
            # 初始化学习状态
            self.current_index = 0
            self.mastered_count = 0
            self.review_count = 0
            
            # 更新每日进度
            self.progress_manager.update_daily_progress(
                self.current_batch,
                self.current_index,
                self.mastered_count,
                self.review_count
            )
            
            self.log_info(f"已开始新的学习批次，共 {len(self.current_batch)} 个单词")
            return True
        except Exception as e:
            self.log_error(f"开始新的学习批次失败: {str(e)}")
            return False

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
                self.log_info(f"播放单词发音: {word}")
            else:
                self.log_error(f"播放单词发音失败: {word}")
            return result
        except Exception as e:
            self.log_error(f"播放单词发音异常: {word}, 错误: {str(e)}")
            return False

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