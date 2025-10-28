"""单词管理器，负责单词的增删改查、权重计算和练习功能"""
import os
import json
import random
from typing import Dict, List, Optional
from logger import log_info, log_error, log_warning


class WordManager:
    """单词管理器类，提供单词管理相关功能"""

    def __init__(self):
        """初始化单词管理器"""
        self.data_dir = 'data'
        self.word_dict_file = os.path.join(self.data_dir, 'word_dict.json')
        self.word_weights_file = os.path.join(
            self.data_dir, 'word_weights.json'
        )
        self.wrong_words_file = os.path.join(self.data_dir, 'wrong_words.json')
        self.word_familiarity_file = os.path.join(
            self.data_dir, 'word_familiarity.json'
        )

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 初始化数据文件
        self._initialize_data_files()

        # 加载数据
        self.word_dict = self._load_data(self.word_dict_file)
        self.word_weights = self._load_data(self.word_weights_file)
        self.wrong_words = self._load_data(self.wrong_words_file)
        self.word_familiarity = self._load_data(self.word_familiarity_file)

        # 初始化AI管理器（延迟加载方式）
        self.ai_manager = None
        self.ai_available = False
        self._init_ai_manager()

    def _initialize_data_files(self):
        """初始化数据文件，确保文件存在并包含基本结构"""
        # 初始化单词字典
        if not os.path.exists(self.word_dict_file):
            initial_words = {
                "apple": "苹果",
                "book": "书",
                "run": "跑",
                "beautiful": "美丽的",
                "computer": "电脑",
                "learn": "学习",
                "friend": "朋友",
                "happy": "快乐的",
                "work": "工作",
                "time": "时间"
            }
            self._save_data(self.word_dict_file, initial_words)
            log_info("初始化单词字典文件")

        # 初始化单词权重
        if not os.path.exists(self.word_weights_file):
            self._save_data(self.word_weights_file, {})
            log_info("初始化单词权重文件")

        # 初始化错误单词
        if not os.path.exists(self.wrong_words_file):
            self._save_data(self.wrong_words_file, {})
            log_info("初始化错误单词文件")

        # 初始化熟悉度
        if not os.path.exists(self.word_familiarity_file):
            self._save_data(self.word_familiarity_file, {})
            log_info("初始化单词熟悉度文件")

    def _load_data(self, file_path: str) -> Dict:
        """从文件加载数据

        Args:
            file_path: 文件路径

        Returns:
            Dict: 加载的数据，如果文件不存在或读取失败返回空字典
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log_error(f"加载文件 {file_path} 失败: {str(e)}")
        return {}

    def _save_data(self, file_path: str, data: Dict):
        """保存数据到文件

        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        try:
            # 先读取现有数据，避免覆盖
            existing_data = self._load_data(file_path)
            # 合并数据
            existing_data.update(data)
            # 保存数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            log_error(f"保存文件 {file_path} 失败: {str(e)}")

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
                    test_response = self.ai_manager.example("test")
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

    def add_word(self, word: str, translation: str):
        """添加单词

        Args:
            word: 单词
            translation: 翻译
        """
        try:
            if word and translation:
                self.word_dict[word.lower()] = translation
                self._save_data(self.word_dict_file, self.word_dict)
                # 初始化权重
                if word.lower() not in self.word_weights:
                    self.word_weights[word.lower()] = 1.0
                    self._save_data(self.word_weights_file, self.word_weights)
                log_info(f"添加单词成功: {word} -> {translation}")
                return True
            return False
        except Exception as e:
            log_error(f"添加单词失败: {str(e)}")
            return False

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
            
    def remove_word(self, word: str):
        """删除单词

        Args:
            word: 单词
        """
        try:
            word_lower = word.lower()
            if word_lower in self.word_dict:
                del self.word_dict[word_lower]
                self._save_data(self.word_dict_file, self.word_dict)
                # 同时删除相关数据
                if word_lower in self.word_weights:
                    del self.word_weights[word_lower]
                    self._save_data(
                        self.word_weights_file,
                        self.word_weights
                    )
                if word_lower in self.wrong_words:
                    del self.wrong_words[word_lower]
                    self._save_data(self.wrong_words_file, self.wrong_words)
                if word_lower in self.word_familiarity:
                    del self.word_familiarity[word_lower]
                    self._save_data(
                        self.word_familiarity_file,
                        self.word_familiarity
                    )
                log_info(f"删除单词成功: {word}")
                return True
            return False
        except Exception as e:
            log_error(f"删除单词失败: {str(e)}")
            return False

    def update_word(self, word: str, translation: str):
        """更新单词

        Args:
            word: 单词
            translation: 新的翻译
        """
        try:
            word_lower = word.lower()
            if word_lower in self.word_dict:
                self.word_dict[word_lower] = translation
                self._save_data(self.word_dict_file, self.word_dict)
                log_info(f"更新单词成功: {word} -> {translation}")
                return True
            return False
        except Exception as e:
            log_error(f"更新单词失败: {str(e)}")
            return False

    def get_word_translation(self, word: str) -> Optional[str]:
        """获取单词翻译

        Args:
            word: 单词

        Returns:
            str: 单词的翻译，如果不存在返回None
        """
        return self.word_dict.get(word.lower())

    def get_all_words(self) -> List[str]:
        """获取所有单词

        Returns:
            List[str]: 单词列表
        """
        return list(self.word_dict.keys())

    def get_word_count(self) -> int:
        """获取单词数量

        Returns:
            int: 单词数量
        """
        return len(self.word_dict)

    def get_random_word(
        self, exclude_words: List[str] = None
    ) -> Optional[str]:
        """获取随机单词

        Args:
            exclude_words: 排除的单词列表

        Returns:
            str: 随机单词，如果没有可用单词返回None
        """
        available_words = [
            word for word in self.word_dict.keys()
            if exclude_words is None or word not in exclude_words
        ]
        if available_words:
            return random.choice(available_words)
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
        available_words = []
        weights = []

        for word in self.word_dict.keys():
            if exclude_words is None or word not in exclude_words:
                available_words.append(word)
                # 获取权重，如果不存在则使用默认值1.0
                weights.append(self.word_weights.get(word, 1.0))

        if available_words:
            # 根据权重随机选择单词
            return random.choices(available_words, weights=weights, k=1)[0]
        return None

    def update_word_weight(self, word: str, factor: float):
        """更新单词权重

        Args:
            word: 单词
            factor: 权重调整因子（大于1增加权重，小于1减少权重）
        """
        try:
            word_lower = word.lower()
            if word_lower in self.word_weights:
                self.word_weights[word_lower] *= factor
                # 确保权重在合理范围内
                self.word_weights[word_lower] = max(
                    0.1, min(self.word_weights[word_lower], 10.0)
                )
                self._save_data(self.word_weights_file, self.word_weights)
            else:
                # 如果权重不存在，初始化为1.0并应用因子
                self.word_weights[word_lower] = 1.0 * factor
                self._save_data(
                    self.word_weights_file,
                    self.word_weights
                )
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
            import os
            import json
            from datetime import datetime
            
            # 计算总学习单词数
            total_learned = len(self.word_dict)
            
            # 计算正确率 (简单实现：正确单词数/(正确+错误))
            wrong_count = sum(self.wrong_words.values())
            if total_learned > 0:
                # 假设每个单词至少被学习一次
                correct_rate = max(0, (total_learned - wrong_count) / total_learned)
            else:
                correct_rate = 0.0
            
            # 获取最后学习时间
            last_session = "未开始"
            stats_file = os.path.join("data", "learning_stats.json")
            if os.path.exists(stats_file):
                try:
                    with open(stats_file, 'r', encoding='utf-8') as f:
                        stats = json.load(f)
                        if stats.get('last_session'):
                            last_session = stats['last_session']
                except Exception as e:
                    log_info(f"读取学习统计失败: {str(e)}")
            
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
            import os
            import json
            from datetime import datetime
            
            # 记录练习开始日志
            log_info(f"开始{exercise_type}练习")
            
            # 更新最后学习时间
            stats_file = os.path.join("data", "learning_stats.json")
            
            # 确保data目录存在
            os.makedirs("data", exist_ok=True)
            
            # 读取现有统计信息
            stats = {}
            if os.path.exists(stats_file):
                try:
                    with open(stats_file, 'r', encoding='utf-8') as f:
                        stats = json.load(f)
                except Exception as e:
                    log_info(f"读取学习统计失败: {str(e)}")
            
            # 更新最后学习时间
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stats['last_session'] = now
            
            # 如果是首次练习，初始化统计信息
            if 'total_exercises' not in stats:
                stats['total_exercises'] = 0
            stats['total_exercises'] += 1
            
            # 保存更新后的统计信息
            try:
                with open(stats_file, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
            except Exception as e:
                log_info(f"保存学习统计失败: {str(e)}")
                
        except Exception as e:
            log_info(f"开始练习失败: {str(e)}")
    
    def get_word_by_weight(self) -> Optional[str]:
        """根据单词权重获取单词（错误次数多的单词优先）

        Returns:
            选中的单词，如果没有单词则返回None
        """
        try:
            # 如果没有单词，返回None
            if not self.word_dict:
                return None
                
            # 创建单词列表和对应的权重
            words = []
            weights = []
            
            for word in self.word_dict.keys():
                word_lower = word.lower()
                # 错误次数越多，权重越大（优先练习错误的单词）
                # 为确保至少有基础权重，使用max(1, 错误次数)作为权重
                weight = max(1, self.wrong_words.get(word_lower, 0))
                words.append(word)
                weights.append(weight)
            
            # 根据权重随机选择单词
            if words:
                selected_word = random.choices(words, weights=weights, k=1)[0]
                log_info(f"根据权重选择单词: {selected_word}")
                return selected_word
            
            return None
        except Exception as e:
            log_error(f"根据权重获取单词失败: {str(e)}")
            # 出错时返回随机单词
            return self.get_random_word()
    
    def add_wrong_word(self, word: str):
        """添加错误单词

        Args:
            word: 单词
        """
        try:
            word_lower = word.lower()
            # 记录错误次数
            if word_lower in self.wrong_words:
                self.wrong_words[word_lower] += 1
            else:
                self.wrong_words[word_lower] = 1
            self._save_data(self.wrong_words_file, self.wrong_words)
            # 增加权重
            self.update_word_weight(word_lower, 1.5)
            # 降低熟悉度
            self.update_word_familiarity(word_lower, -0.2)
            log_info(
                f"添加错误单词: {word}, "
                f"错误次数: {self.wrong_words[word_lower]}"
            )
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
        """更新单词熟悉度

        Args:
            word: 单词
            delta: 熟悉度变化量
        """
        try:
            word_lower = word.lower()
            if word_lower in self.word_familiarity:
                self.word_familiarity[word_lower] += delta
            else:
                self.word_familiarity[word_lower] = delta
            # 确保熟悉度在0-1范围内
            self.word_familiarity[word_lower] = max(
                0.0, min(self.word_familiarity[word_lower], 1.0)
            )
            self._save_data(self.word_familiarity_file, self.word_familiarity)
        except Exception as e:
            log_error(f"更新单词熟悉度失败: {str(e)}")

    def get_today_learned_words(self) -> List[str]:
        """获取今日学习的单词列表
        
        Returns:
            List[str]: 今日学习的单词列表
        """
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            today_words = set()  # 使用集合避免重复
            
            # 方法1: 从熟悉度记录中查找今日学习的单词
            for word, data in self.word_familiarity.items():
                # 如果data是字典且包含last_learned字段
                if isinstance(data, dict) and 'last_learned' in data:
                    last_learned_date = data['last_learned'].split(' ')[0] if isinstance(data['last_learned'], str) else ''
                    if last_learned_date == today:
                        today_words.add(word)
                # 如果data是字符串（可能是直接的时间戳）
                elif isinstance(data, str):
                    try:
                        learned_date = data.split(' ')[0]
                        if learned_date == today:
                            today_words.add(word)
                    except:
                        # 忽略格式错误的时间戳
                        pass
            
            # 方法2: 从word_progress.json查找今日学习的单词
            try:
                progress_file = os.path.join(self.data_dir, 'word_progress.json')
                word_progress = self._load_data(progress_file)
                
                for word, progress in word_progress.items():
                    if progress.get('learned', False):
                        last_learned = progress.get('last_learned', '')
                        if last_learned:
                            try:
                                # 尝试从不同格式的时间戳中提取日期
                                if isinstance(last_learned, str):
                                    if 'T' in last_learned:  # ISO格式
                                        learned_date = last_learned.split('T')[0]
                                    else:  # 普通格式
                                        learned_date = last_learned.split(' ')[0]
                                    
                                    if learned_date == today:
                                        today_words.add(word)
                            except:
                                # 忽略格式错误的时间戳
                                pass
            except Exception as e:
                log_warning(f"从word_progress获取今日学习单词时出错: {str(e)}")
            
            # 方法3: 如果今日学习已完成但没有找到单词，返回最近学习的几个单词
            # 这是为了处理记录不完整的情况
            if not today_words:
                try:
                    # 检查今日学习是否已完成
                    daily_learning_file = os.path.join(self.data_dir, 'daily_learning.json')
                    daily_learning = self._load_data(daily_learning_file)
                    
                    if today in daily_learning and daily_learning[today].get('completed', False):
                        log_info("今日学习已完成但未找到具体单词记录，尝试获取最近学习的单词")
                        
                        # 获取最近修改过的单词（根据权重文件，因为学习会改变权重）
                        weights_file = os.path.join(self.data_dir, 'word_weights.json')
                        weights_data = self._load_data(weights_file)
                        
                        # 如果有权重数据，返回一些单词作为备选
                        if weights_data:
                            # 取权重最高的10个单词
                            sorted_words = sorted(weights_data.items(), key=lambda x: x[1], reverse=True)
                            recent_words = [word for word, _ in sorted_words[:10]]
                            today_words.update(recent_words)
                except Exception as e:
                    log_warning(f"尝试获取备选单词时出错: {str(e)}")
            
            result = list(today_words)
            log_info(f"get_today_learned_words 返回 {len(result)} 个单词")
            return result
        except Exception as e:
            log_error(f"获取今日学习单词失败: {str(e)}")
            # 出错时返回一个安全的备选方案 - 几个常用单词
            try:
                # 返回一些单词作为备选，避免用户无法进行听写
                return list(self.word_dict.keys())[:10]  # 返回前10个单词作为备选
            except:
                return []
    
    def get_word_familiarity(self, word: str = None) -> float or dict:
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
            return {word: self.word_familiarity.get(word.lower(), 0.0) for word in self.word_dict.keys()}

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

    def get_word_example(self, word: str) -> str:
        """获取单词的例句

        Args:
            word: 要获取例句的单词

        Returns:
            str: 包含例句和翻译的文本，如果获取失败返回默认例句
        """
        try:
            # 首先检查AI功能是否可用
            if self.ai_available and self.ai_manager:
                # 调用AI接口获取例句
                example = self.ai_manager.example(word)
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

            # 提供一些简单的硬编码例句作为备用
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
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            daily_learning_file = os.path.join(self.data_dir, 'daily_learning.json')
            
            # 读取daily_learning.json文件
            daily_learning_data = self._load_data(daily_learning_file)
            
            # 检查今日记录是否存在且标记为完成
            if today in daily_learning_data and daily_learning_data[today].get('completed', False):
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
            word_lower = word.lower()
            correct_translation = self.get_word_translation(word_lower)
            
            if not correct_translation:
                log_warning(f"无法检查翻译: 单词 '{word}' 没有对应的翻译")
                return False
            
            # 简化的比较逻辑：忽略大小写和多余空格
            correct_normalized = correct_translation.strip().lower()
            user_normalized = user_translation.strip().lower()
            
            is_correct = correct_normalized == user_normalized
            
            if update_stats:
                if is_correct:
                    # 翻译正确，增加熟悉度，降低权重
                    self.update_word_familiarity(word_lower, 0.1)
                    self.update_word_weight(word_lower, 0.9)
                    log_info(f"翻译正确: {word} -> {user_translation}")
                else:
                    # 翻译错误，记录错误单词，增加权重
                    self.add_wrong_word(word_lower)
                    log_info(f"翻译错误: {word} -> 用户输入: {user_translation}, 正确翻译: {correct_translation}")
            
            return is_correct
        except Exception as e:
            log_error(f"检查翻译失败: {str(e)}")
            return False