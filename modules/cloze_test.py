import os
import random
from typing import Dict, List, Optional, Tuple
import threading

from logger import log_info, log_error
from .database import ComprehensionDatabase
from .ai_service import AIService


class ClozeTestModule:
    """完形填空模块"""
    
    def __init__(self):
        """初始化完形填空模块"""
        self.db_manager = ComprehensionDatabase()
        self.ai_service = AIService()
        self._lock = threading.RLock()
        
        # 当前练习状态
        self.current_test = None
        self.user_answers = []
    
    def get_mode(self) -> str:
        """获取当前模式（在线/离线）
        
        Returns:
            str: 模式名称
        """
        return "online" if self.ai_service.is_ai_available() else "offline"
    
    def start_new_test(self, mode: str = None, level: str = "中级", 
                      topic: str = "通用") -> Optional[Dict]:
        """开始新的完形填空练习
        
        Args:
            mode: 模式（online/offline/None自动检测）
            level: 难度级别
            topic: 主题
            
        Returns:
            Dict: 题目信息，None表示失败
        """
        try:
            with self._lock:
                # 重置当前状态
                self.current_test = None
                self.user_answers = []
                
                # 如果未指定模式，自动检测
                if mode is None:
                    mode = self.get_mode()
                
                if mode == "online" and self.ai_service.is_ai_available():
                    # 在线模式：AI生成题目
                    log_info(f"在线模式生成完形填空题目，难度: {level}，主题: {topic}")
                    self.current_test = self.ai_service.generate_cloze_test(level, topic)
                    
                else:
                    # 离线模式：从数据库加载
                    log_info("离线模式加载完形填空题目")
                    
                    # 检查数据库是否有题目
                    if self.db_manager.count_cloze_tests() == 0:
                        log_error("离线模式下数据库中没有完形填空题目")
                        return None
                    
                    self.current_test = self.db_manager.get_cloze_test()
                
                if self.current_test:
                    log_info(f"成功获取完形填空题目，ID: {self.current_test.get('id')}")
                    return self._prepare_test_for_display()
                else:
                    log_error("获取完形填空题目失败")
                    return None
                    
        except Exception as e:
            log_error(f"开始新的完形填空练习失败: {str(e)}")
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
            'title': self.current_test.get('title'),
            'content': self.current_test.get('content'),
            'options': []
        }
        
        # 处理选项显示
        for opt in self.current_test.get('options', []):
            display_data['options'].append({
                'blank': opt['blank'],
                'options': opt['options']
            })
        
        return display_data
    
    def submit_answer(self, user_answer: str) -> Tuple[bool, str, str]:
        """提交答案
        
        Args:
            user_answer: 用户答案字符串，格式为逗号分隔
            
        Returns:
            Tuple[bool, str, str]: (是否正确, 评估结果, 解析)
        """
        try:
            with self._lock:
                if not self.current_test:
                    log_error("没有正在进行的完形填空练习")
                    return False, "没有正在进行的练习", ""
                
                correct_answer = self.current_test.get('answer', '')
                explanation = self.current_test.get('explanation', '')
                
                # 评估答案
                is_correct, evaluation = self.ai_service.evaluate_cloze_answer(
                    user_answer, correct_answer
                )
                
                # 保存用户答案
                self.user_answers = [a.strip() for a in user_answer.split(',')]
                
                log_info(f"完形填空答题评估: {'正确' if is_correct else '错误'}")
                return is_correct, evaluation, explanation
                
        except Exception as e:
            log_error(f"提交完形填空答案失败: {str(e)}")
            return False, "提交失败", ""
    
    def get_test_statistics(self) -> Dict:
        """获取测试统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            stats = {
                'total_tests': self.db_manager.count_cloze_tests(),
                'ai_available': self.ai_service.is_ai_available(),
                'current_mode': self.get_mode()
            }
            return stats
        except Exception as e:
            log_error(f"获取测试统计信息失败: {str(e)}")
            return {}
    
    def get_all_tests(self) -> List[Dict]:
        """获取所有完形填空题目列表
        
        Returns:
            List[Dict]: 题目列表
        """
        try:
            return self.db_manager.get_all_cloze_tests()
        except Exception as e:
            log_error(f"获取所有完形填空题目失败: {str(e)}")
            return []
    
    def get_test_by_id(self, test_id: int) -> Optional[Dict]:
        """根据ID获取特定题目
        
        Args:
            test_id: 题目ID
            
        Returns:
            Dict: 题目信息
        """
        try:
            test = self.db_manager.get_cloze_test(test_id)
            if test:
                self.current_test = test
                return self._prepare_test_for_display()
            return None
        except Exception as e:
            log_error(f"获取指定ID的完形填空题目失败: {str(e)}")
            return None
    
    def delete_test(self, test_id: int) -> bool:
        """删除指定题目
        
        Args:
            test_id: 题目ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            success = self.db_manager.delete_cloze_test(test_id)
            # 如果删除的是当前正在做的题目，重置状态
            if success and self.current_test and self.current_test.get('id') == test_id:
                self.current_test = None
                self.user_answers = []
            return success
        except Exception as e:
            log_error(f"删除完形填空题目失败: {str(e)}")
            return False
    
    def format_answer_for_display(self, answer: str) -> str:
        """格式化答案用于显示
        
        Args:
            answer: 原始答案字符串
            
        Returns:
            str: 格式化后的答案
        """
        try:
            answers = [a.strip() for a in answer.split(',')]
            return ' '.join([f"第{i+1}题: {ans}" for i, ans in enumerate(answers)])
        except Exception as e:
            log_error(f"格式化答案失败: {str(e)}")
            return answer