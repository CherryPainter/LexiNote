import json
import os
import random
from typing import Dict, List, Optional, Tuple, Any
from logger import log_info, log_error, log_warning, log_wrong_word, log_exercise_start
from core.ai_interface import AIManager


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
        """使用AI检查翻译是否正确"""
        # 简单的输入验证
        if not user_input or not expected:
            return False
            
        # 首先检查AI功能是否可用
        if self.ai_available and self.ai_manager:
            try:
                # 构建提示词，让AI判断翻译是否正确
                if is_english_to_chinese:
                    # 英译中判断
                    prompt = f"请判断以下翻译是否正确：\n英文单词：{expected}\n用户翻译：{user_input}\n\n请直接回答'正确'或'错误'，不要添加其他解释。"
                else:
                    # 中译英判断
                    prompt = f"请判断以下翻译是否正确：\n中文词语：{expected}\n用户翻译：{user_input}\n\n请直接回答'正确'或'错误'，不要添加其他解释。"
                
                # 调用AI接口获取判断结果
                ai_response = self.ai_manager._ask(prompt)
                
                # 处理AI响应
                if ai_response and ('正确' in ai_response or 'correct' in ai_response.lower()):
                    return True
                elif ai_response and ('错误' in ai_response or 'incorrect' in ai_response.lower()):
                    return False
            except Exception as e:
                # AI调用失败时记录日志，但不影响程序运行
                log_error(f"AI翻译判断失败: {str(e)}")
        
        # AI调用失败、不可用或无法判断时，使用备用的模糊匹配逻辑
        return self._fallback_translation_check(expected, user_input, is_english_to_chinese)
    
    def _fallback_translation_check(self, expected, user_input, is_english_to_chinese=True):
        """备用的翻译检查逻辑（当AI调用失败时使用）"""
        # 简单的模糊匹配逻辑
        expected_lower = expected.lower()
        user_input_lower = user_input.lower().strip()
        
        # 定义单词特定翻译的映射（对两种方向都适用）
        word_specific_translations = {
            'minor': ['较小的', '次要的', '轻微的', '小型的', '不太重要的', '微小的'],
            'diagram': ['图表', '图形', '图示', '图像'],
            'chart': ['图表', '图表', '曲线图', '图形'],
            'graph': ['图表', '图形', '曲线图', '图表'],
            'picture': ['图片', '照片', '图像', '图画'],
            'image': ['图像', '图片', '影像', '镜像'],
            'figure': ['数字', '图', '图表', '数据', '图像'],
            'acquisition': ['获得', '习得', '获取', '收购', '得到', '取得']
        }
        
        # 检查单词特定的翻译匹配（双向）
        for word, translations in word_specific_translations.items():
            if word == expected_lower and user_input_lower in translations:
                return True
            if user_input_lower == word and expected_lower in translations:
                return True
        
        # 如果是英译中，实现更智能的模糊匹配
        if is_english_to_chinese:
            # 检查完全匹配
            if expected_lower == user_input_lower:
                return True
            
            # 定义一些常见的近义词映射，用于更智能的匹配
            common_synonyms = {
                '小的': ['小型的', '较小的', '微小的', '细小的'],
                '大的': ['大型的', '较大的', '巨大的', '庞大的'],
                '好的': ['良好的', '优秀的', '棒的', '不错的'],
                '坏的': ['糟糕的', '不良的', '不好的', '恶劣的'],
                '新的': ['新鲜的', '新颖的', '新式的'],
                '旧的': ['老旧的', '过时的', '陈腐的'],
                '重要的': ['关键的', '主要的', '重大的'],
                '次要的': ['较小的', '轻微的', '一般的'],
                '简单的': ['简易的', '容易的', '基本的'],
                '复杂的': ['繁复的', '困难的', '综合的'],
                '图表': ['图形', '图示', '图像', '图表'],
                '图形': ['图表', '图示', '图像'],
                '图示': ['图表', '图形', '图像'],
                '图像': ['图表', '图形', '图示'],
                '获得': ['习得', '获取', '收购', '得到', '取得'],
                '习得': ['获得', '获取', '得到', '取得'],
                '获取': ['获得', '习得', '得到', '取得']
            }
            
            # 检查用户输入是否包含预期翻译的近义词
            for key, synonyms in common_synonyms.items():
                if key in expected_lower and any(synonym in user_input_lower for synonym in synonyms):
                    return True
                if key in user_input_lower and any(synonym in expected_lower for synonym in synonyms):
                    return True
            
            # 分词并检查关键词匹配
            expected_chars = list(expected_lower)
            user_chars = list(user_input_lower)
            
            # 计算匹配的字符比例
            matches = 0
            total_chars = len(expected_lower)
            
            for char in expected_chars:
                if char in user_chars:
                    matches += 1
                    user_chars.remove(char)
            
            # 降低匹配阈值到50%，提高识别率
            if total_chars > 0 and matches / total_chars >= 0.5:
                return True
                
            # 检查是否有重叠的关键词（至少2个连续字符）
            for i in range(len(expected_lower) - 1):
                two_chars = expected_lower[i:i+2]
                if two_chars in user_input_lower:
                    return True
                    
            # 检查用户输入是否包含预期翻译的所有字符（顺序不限）
            all_chars_match = True
            for char in expected_lower:
                if char not in user_input_lower:
                    all_chars_match = False
                    break
            if all_chars_match:
                return True
        else:
            # 中译英，增强匹配逻辑
            # 移除常见的单复数结尾进行匹配
            user_input_lower = user_input_lower.rstrip('s').rstrip('es')
            expected_lower = expected_lower.rstrip('s').rstrip('es')
            
            # 完全匹配检查
            if user_input_lower == expected_lower:
                return True
            
            # 反向检查单词特定翻译（用于中译英）
            for word, translations in word_specific_translations.items():
                if expected_lower in translations and user_input_lower == word:
                    return True
            
            # 中译英的模糊匹配
            # 检查常见的动词变化
            user_input_lower = user_input_lower.rstrip('ed').rstrip('ing')
            expected_lower = expected_lower.rstrip('ed').rstrip('ing')
            
            return user_input_lower == expected_lower
        
        # 所有匹配条件都不满足，返回False
        return False
    
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
    
    def translate_text(self, text, mode="en2zh"):
        """翻译文本
        
        Args:
            text: 要翻译的文本
            mode: 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)
            
        Returns:
            翻译后的文本
        """
        if not self.ai_available:
            log_warning("AI功能暂不可用")
            return "AI功能暂不可用"
        
        try:
            result = self.ai_manager.translate(text, mode)
            return result
        except Exception as e:
            log_error(f"翻译失败: {str(e)}")
            return "翻译失败"
    
    def generate_example(self, word):
        """为单词生成例句
        
        Args:
            word: 要生成例句的单词
            
        Returns:
            包含例句和翻译的文本
        """
        if not self.ai_available:
            log_warning("AI功能暂不可用")
            return "AI功能暂不可用"
        
        try:
            result = self.ai_manager.example(word)
            return result
        except Exception as e:
            log_error(f"生成例句失败: {str(e)}")
            return "生成例句失败"
    
    def evaluate_spelling(self, expected, user_input):
        """评估拼写结果
        
        Args:
            expected: 期望的正确单词
            user_input: 用户输入的单词
            
        Returns:
            包含准确率和反馈的字典
        """
        if not self.ai_available:
            # 如果AI不可用，使用简单的字符串比较
            is_correct = self.check_spelling(expected, user_input)
            return {
                "accuracy": 1.0 if is_correct else 0.0,
                "feedback": "正确" if is_correct else "错误"
            }
        
        try:
            result = self.ai_manager.evaluate(expected, user_input)
            return result
        except Exception as e:
            log_error(f"评估拼写失败: {str(e)}")
            # 回退到简单比较
            is_correct = self.check_spelling(expected, user_input)
            return {
                "accuracy": 1.0 if is_correct else 0.0,
                "feedback": "正确" if is_correct else "错误"
            }
    
    def get_study_advice(self):
        """获取个性化学习建议
        
        Returns:
            学习建议文本
        """
        if not self.ai_available:
            log_warning("AI功能暂不可用")
            return "AI功能暂不可用"
        
        try:
            # 准备用户统计数据
            user_stats = {
                "total_words": len(self.word_dict),
                "mastered": sum(1 for word, weight in self.word_weights.items() if weight < 0.5),
                "review_needed": sum(1 for word, count in self.wrong_words.items() if count > 2),
                "average_score": self.progress.get("correct_rate", 0.0)
            }
            
            result = self.ai_manager.advise(user_stats)
            return result
        except Exception as e:
            log_error(f"获取学习建议失败: {str(e)}")
            return "获取学习建议失败"
    
    def _init_ai_manager(self):
        """初始化AI管理器（延迟加载方式）"""
        try:
            self.ai_manager = AIManager()
            self.ai_available = True
        except Exception as e:
            log_error(f"初始化AI管理器失败: {str(e)}")
            self.ai_available = False
            
    def is_ai_available(self):
        """检查AI功能是否可用
        
        Returns:
            bool: AI功能是否可用
        """
        if self.ai_manager is None:
            self._init_ai_manager()
            
        if not self.ai_available:
            return False
            
        try:
            # 尝试导入requests模块
            import requests
            
            # 尝试连接Ollama API进行可用性检查
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.ai_manager.model,
                        "prompt": "test",
                        "stream": False,
                        "options": {"num_predict": 1}  # 最小化预测数量以快速响应
                    },
                    timeout=5  # 快速超时检查
                )
                return response.status_code == 200
            except requests.RequestException:
                # 如果连接失败，返回False
                return False
                
        except ImportError:
            # 如果requests模块不可用，返回False
            return False