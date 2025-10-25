import json
import os
import random
from logger import log_info, log_error, log_wrong_word, log_exercise_start


class WordManager:
    """单词管理器，负责单词的增删改查、权重计算和练习功能"""
    
    def __init__(self):
        """初始化单词管理器"""
        self.data_dir = 'data'
        self.word_dict_file = os.path.join(self.data_dir, 'word_dict.json')
        self.word_weights_file = os.path.join(self.data_dir, 'word_weights.json')
        self.wrong_words_file = os.path.join(self.data_dir, 'wrong_words.json')
        self.progress_file = os.path.join(self.data_dir, 'progress.json')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化数据文件
        self._initialize_data_files()
        
        # 加载数据
        self.word_dict = self._load_data(self.word_dict_file)
        self.word_weights = self._load_data(self.word_weights_file)
        self.wrong_words = self._load_data(self.wrong_words_file)
        self.progress = self._load_data(self.progress_file)
    
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
        
        # 初始化进度记录
        if not os.path.exists(self.progress_file):
            initial_progress = {
                "total_learned": 0,
                "correct_rate": 0.0,
                "last_session": "",
                "total_attempts": 0,
                "total_correct": 0
            }
            self._save_data(self.progress_file, initial_progress)
            log_info("初始化进度记录文件")
    
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
    
    def add_word(self, word, translation):
        """添加新单词"""
        try:
            # 更新单词字典
            self.word_dict[word] = translation
            self._save_data(self.word_dict_file, {word: translation})
            
            # 初始化权重
            if word not in self.word_weights:
                self.word_weights[word] = 1.0
                self._save_data(self.word_weights_file, {word: 1.0})
            
            log_info(f"添加单词: {word} -> {translation}")
            return True
        except Exception as e:
            log_error(f"添加单词失败: {str(e)}")
            return False
    
    def get_word_by_weight(self):
        """基于权重随机获取单词"""
        if not self.word_dict:
            return None
        
        # 确保所有单词都有权重
        for word in self.word_dict:
            if word not in self.word_weights:
                self.word_weights[word] = 1.0
                self._save_data(self.word_weights_file, {word: 1.0})
        
        # 计算权重总和
        words = list(self.word_weights.keys())
        weights = [self.word_weights[word] for word in words]
        total_weight = sum(weights)
        
        # 基于权重随机选择
        if total_weight > 0:
            rand_value = random.uniform(0, total_weight)
            cumulative = 0
            for i, word in enumerate(words):
                cumulative += weights[i]
                if rand_value <= cumulative:
                    return word
        
        # 回退方案
        return random.choice(list(self.word_dict.keys()))
    
    def update_word_weight(self, word, is_correct):
        """更新单词权重
        规则：每次错误 +0.5，每次正确 ×0.8
        """
        try:
            if word not in self.word_weights:
                self.word_weights[word] = 1.0
            
            if is_correct:
                # 正确时权重乘以0.8
                self.word_weights[word] *= 0.8
                # 最低权重限制
                self.word_weights[word] = max(self.word_weights[word], 0.1)
            else:
                # 错误时权重加0.5
                self.word_weights[word] += 0.5
                # 记录错误单词
                if word not in self.wrong_words:
                    self.wrong_words[word] = 1
                else:
                    self.wrong_words[word] += 1
                self._save_data(self.wrong_words_file, {word: self.wrong_words[word]})
            
            # 保存权重更新
            self._save_data(self.word_weights_file, {word: self.word_weights[word]})
            
            # 更新进度
            self._update_progress(is_correct)
            
            if not is_correct:
                log_wrong_word(word, "")
            
            return True
        except Exception as e:
            log_error(f"更新单词权重失败: {str(e)}")
            return False
    
    def _update_progress(self, is_correct):
        """更新学习进度"""
        try:
            self.progress['total_attempts'] = self.progress.get('total_attempts', 0) + 1
            if is_correct:
                self.progress['total_correct'] = self.progress.get('total_correct', 0) + 1
            
            # 计算正确率
            if self.progress['total_attempts'] > 0:
                self.progress['correct_rate'] = round(
                    self.progress['total_correct'] / self.progress['total_attempts'], 2
                )
            
            # 更新最后学习时间
            from datetime import datetime
            self.progress['last_session'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 更新总学习单词数
            self.progress['total_learned'] = len(self.word_dict)
            
            self._save_data(self.progress_file, self.progress)
        except Exception as e:
            log_error(f"更新进度失败: {str(e)}")
    
    def check_spelling(self, word, user_input):
        """检查单词拼写"""
        return word.lower() == user_input.lower()
    
    def check_translation(self, expected, user_input, is_english_to_chinese=True):
        """检查翻译是否正确（模糊匹配）"""
        # 简单的模糊匹配逻辑
        expected_lower = expected.lower()
        user_input_lower = user_input.lower().strip()
        
        # 如果是英译中，检查用户输入是否包含正确翻译的关键字
        if is_english_to_chinese:
            # 这里可以实现更复杂的模糊匹配逻辑
            return expected_lower in user_input_lower
        else:
            # 中译英，忽略大小写和单复数等简单变化
            # 移除常见的单复数结尾进行匹配
            user_input_lower = user_input_lower.rstrip('s').rstrip('es')
            expected_lower = expected_lower.rstrip('s').rstrip('es')
            return user_input_lower == expected_lower
    
    def get_progress(self):
        """获取学习进度"""
        return self.progress
    
    def get_all_words(self):
        """获取所有单词"""
        return self.word_dict
    
    def get_wrong_words(self):
        """获取错误单词列表"""
        return self.wrong_words
    
    def start_exercise(self, exercise_type):
        """开始练习"""
        log_exercise_start(exercise_type)
        return True
    
    def apply_daily_decay(self):
        """应用每日权重衰减（模拟遗忘）"""
        try:
            for word in self.word_weights:
                # 轻微增加权重，模拟遗忘
                self.word_weights[word] = min(self.word_weights[word] * 1.1, 5.0)
            
            self._save_data(self.word_weights_file, self.word_weights)
            log_info("应用每日权重衰减")
            return True
        except Exception as e:
            log_error(f"应用每日衰减失败: {str(e)}")
            return False