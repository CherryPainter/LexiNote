import os
import re
from typing import Dict, List, Optional, Tuple
import threading

from logger import log_info, log_error
from .database import ComprehensionDatabase
from .ai_service import AIService


class ReadingComprehensionModule:
    """阅读理解模块"""
    
    def __init__(self):
        """初始化阅读理解模块"""
        self.db_manager = ComprehensionDatabase()
        self.ai_service = AIService()
        self._lock = threading.RLock()
        
        # 当前练习状态
        self.current_test = None
        self.user_answers = []
        self.current_question_index = 0
    
    def get_mode(self) -> str:
        """获取当前模式（在线/离线）
        
        Returns:
            str: 模式名称
        """
        return "online" if self.ai_service.is_ai_available() else "offline"
    
    def start_new_test(self, mode: str = None, level: str = "中级", 
                      length: str = "短篇", question_count: int = 5) -> Optional[Dict]:
        """开始新的阅读理解练习
        
        Args:
            mode: 模式（online/offline/None自动检测）
            level: 难度级别
            length: 文章长度
            question_count: 题目数量
            
        Returns:
            Dict: 题目信息，None表示失败
        """
        try:
            with self._lock:
                # 重置当前状态
                self.current_test = None
                self.user_answers = []
                self.current_question_index = 0
                
                # 如果未指定模式，自动检测
                if mode is None:
                    mode = self.get_mode()
                
                if mode == "online" and self.ai_service.is_ai_available():
                    # 在线模式：AI生成题目
                    log_info(f"在线模式生成阅读理解题目，难度: {level}，长度: {length}，题目数: {question_count}")
                    self.current_test = self.ai_service.generate_reading_comprehension(
                        level, length, question_count
                    )
                    
                else:
                    # 离线模式：从数据库加载
                    log_info("离线模式加载阅读理解题目")
                    
                    # 检查数据库是否有题目
                    if self.db_manager.count_reading_comprehensions() == 0:
                        log_error("离线模式下数据库中没有阅读理解题目")
                        return None
                    
                    self.current_test = self.db_manager.get_reading_comprehension()
                
                if self.current_test:
                    log_info(f"成功获取阅读理解题目，ID: {self.current_test.get('id')}")
                    # 初始化用户答案数组
                    self.user_answers = ["" for _ in self.current_test.get('questions', [])]
                    return self._prepare_test_for_display()
                else:
                    log_error("获取阅读理解题目失败")
                    return None
                    
        except Exception as e:
            log_error(f"开始新的阅读理解练习失败: {str(e)}")
            return None
    
    def _prepare_test_for_display(self) -> Dict:
        """准备用于显示的题目数据
        
        Returns:
            Dict: 格式化后的题目数据
        """
        if not self.current_test:
            return {}
        
        # 创建显示用的数据
        display_data = {
            'id': self.current_test.get('id'),
            'article': self.current_test.get('article'),
            'questions': self.current_test.get('questions', []),
            'total_questions': len(self.current_test.get('questions', []))
        }
        
        return display_data
    
    def submit_question_answer(self, question_index: int, user_answer: str) -> Tuple[bool, str, str]:
        """提交单个问题的答案
        
        Args:
            question_index: 问题索引（从0开始）
            user_answer: 用户答案
            
        Returns:
            Tuple[bool, str, str]: (是否正确, 评估结果, 解析)
        """
        try:
            with self._lock:
                if not self.current_test:
                    log_error("没有正在进行的阅读理解练习")
                    return False, "没有正在进行的练习", ""
                
                questions = self.current_test.get('questions', [])
                answers = self.current_test.get('answers', [])
                explanations = self.current_test.get('explanations', [])
                
                # 检查索引是否有效
                if question_index < 0 or question_index >= len(questions):
                    log_error(f"问题索引无效: {question_index}")
                    return False, "问题索引无效", ""
                
                correct_answer = answers[question_index]
                explanation = explanations[question_index] if question_index < len(explanations) else ""
                
                # 判断题目类型（选择题或主观题）
                question_text = questions[question_index]
                question_type = "选择题" if re.search(r'[A-D]\.', question_text) else "主观题"
                
                # 评估答案
                is_correct, evaluation = self.ai_service.evaluate_reading_answer(
                    user_answer, correct_answer, question_type
                )
                
                # 保存用户答案
                self.user_answers[question_index] = user_answer
                
                log_info(f"阅读理解第{question_index+1}题答题评估: {'正确' if is_correct else '错误'}")
                return is_correct, evaluation, explanation
                
        except Exception as e:
            log_error(f"提交阅读理解答案失败: {str(e)}")
            return False, "提交失败", ""
    
    def submit_all_answers(self, user_answers: List[str]) -> Tuple[float, List[Dict]]:
        """提交所有问题的答案
        
        Args:
            user_answers: 用户答案列表
            
        Returns:
            Tuple[float, List[Dict]]: (总分, 每题的评估结果)
        """
        try:
            with self._lock:
                if not self.current_test:
                    log_error("没有正在进行的阅读理解练习")
                    return 0.0, []
                
                questions = self.current_test.get('questions', [])
                
                if len(user_answers) != len(questions):
                    log_error("答案数量与问题数量不匹配")
                    return 0.0, []
                
                # 保存所有用户答案
                self.user_answers = user_answers
                
                # 评估每个答案
                results = []
                correct_count = 0
                
                for i, user_answer in enumerate(user_answers):
                    is_correct, evaluation, explanation = self.submit_question_answer(i, user_answer)
                    if is_correct:
                        correct_count += 1
                    
                    results.append({
                        'question_index': i,
                        'is_correct': is_correct,
                        'evaluation': evaluation,
                        'explanation': explanation
                    })
                
                # 计算总分
                total_score = (correct_count / len(questions)) * 100 if questions else 0
                
                log_info(f"阅读理解全部答题完成，得分: {total_score:.1f}/100")
                return total_score, results
                
        except Exception as e:
            log_error(f"提交所有阅读理解答案失败: {str(e)}")
            return 0.0, []
    
    def get_test_statistics(self) -> Dict:
        """获取测试统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            stats = {
                'total_tests': self.db_manager.count_reading_comprehensions(),
                'ai_available': self.ai_service.is_ai_available(),
                'current_mode': self.get_mode()
            }
            return stats
        except Exception as e:
            log_error(f"获取测试统计信息失败: {str(e)}")
            return {}
    
    def get_all_tests(self) -> List[Dict]:
        """获取所有阅读理解题目列表
        
        Returns:
            List[Dict]: 题目列表
        """
        try:
            return self.db_manager.get_all_reading_comprehensions()
        except Exception as e:
            log_error(f"获取所有阅读理解题目失败: {str(e)}")
            return []
    
    def get_test_by_id(self, test_id: int) -> Optional[Dict]:
        """根据ID获取特定题目
        
        Args:
            test_id: 题目ID
            
        Returns:
            Dict: 题目信息
        """
        try:
            test = self.db_manager.get_reading_comprehension(test_id)
            if test:
                self.current_test = test
                self.user_answers = ["" for _ in test.get('questions', [])]
                self.current_question_index = 0
                return self._prepare_test_for_display()
            return None
        except Exception as e:
            log_error(f"获取指定ID的阅读理解题目失败: {str(e)}")
            return None
    
    def delete_test(self, test_id: int) -> bool:
        """删除指定题目
        
        Args:
            test_id: 题目ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            success = self.db_manager.delete_reading_comprehension(test_id)
            # 如果删除的是当前正在做的题目，重置状态
            if success and self.current_test and self.current_test.get('id') == test_id:
                self.current_test = None
                self.user_answers = []
                self.current_question_index = 0
            return success
        except Exception as e:
            log_error(f"删除阅读理解题目失败: {str(e)}")
            return False
    
    def is_question_multiple_choice(self, question_index: int) -> bool:
        """判断问题是否为选择题
        
        Args:
            question_index: 问题索引
            
        Returns:
            bool: 是否为选择题
        """
        try:
            if not self.current_test:
                return False
            
            questions = self.current_test.get('questions', [])
            if question_index < 0 or question_index >= len(questions):
                return False
            
            question_text = questions[question_index]
            return bool(re.search(r'[A-D]\.', question_text))
            
        except Exception as e:
            log_error(f"判断题目类型失败: {str(e)}")
            return False