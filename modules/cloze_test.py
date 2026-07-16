from typing import Dict, List, Optional, Tuple, Any
import threading

from logger import log_info, log_error
from .database import ComprehensionDatabase
from .ai_service import AIService
from word_manager import WordManager


class ClozeTestModule:
    """完形填空模块"""

    def __init__(self, word_manager: WordManager):
        """初始化完形填空模块

        Args:
            word_manager: 外部传入的WordManager实例，避免重复创建
        """
        self.db_manager = ComprehensionDatabase()
        # 使用外部传入的WordManager实例，避免重复创建
        self.word_manager = word_manager
        # 将word_manager传递给AIService，避免重复测试AI连接
        self.ai_service = AIService(word_manager=word_manager)
        self._lock = threading.RLock()

        # 当前练习状态
        self.current_test: Optional[dict] = None
        self.user_answers: list = []
        self._current_mode: Optional[str] = None  # 保存当前实际使用的模式

    def get_mode(self) -> str:
        """获取当前模式（在线/离线）

        Returns:
            str: 模式名称
        """
        # 如果有明确设置的模式，则返回该模式
        if self._current_mode is not None:
            return self._current_mode
        # 否则根据WordManager中的AI可用性判断
        return "online" if self.word_manager.ai_available else "offline"

    def start_new_test(self, mode: str = None, level: str = "高中",
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
                # 保存当前题目的ID（如果有），用于离线模式下避免重复
                current_test_id = self.current_test.get('id') if self.current_test else None

                # 重置当前状态
                self.current_test = None
                self.user_answers = []

                # 如果未指定模式，自动检测
                if mode is None:
                    mode = "online" if self.word_manager.ai_available else "offline"

                # 保存当前实际使用的模式
                self._current_mode = mode

                if mode == "online" and self.word_manager.ai_available:
                    # 在线模式：AI生成题目
                    log_info(f"在线模式生成完形填空题目，难度: {level}，主题: {topic}")
                    self.current_test = self.ai_service.generate_cloze_test(level, topic)

                else:
                    # 离线模式：从数据库加载
                    log_info("离线模式加载完形填空题目")

                    # 检查数据库是否有题目
                    test_count = self.db_manager.count_cloze_tests()
                    if test_count == 0:
                        log_error("离线模式下数据库中没有完形填空题目")
                        return None

                    # 如果数据库中只有一个题目，就直接获取，无法避免重复
                    if test_count == 1:
                        self.current_test = self.db_manager.get_cloze_test()
                    else:
                        # 否则，排除当前题目的ID，获取不同的随机题目
                        self.current_test = self.db_manager.get_cloze_test(exclude_id=current_test_id)

                if self.current_test:
                    # 兼容AI/DB返回的字段名：有些返回使用 'answers'，数据库使用 'answer'
                    if 'answer' not in self.current_test and 'answers' in self.current_test:
                        self.current_test['answer'] = self.current_test.get('answers')

                    # 兼容选项格式：将可能的 'text' 字段解析为 'options' 列表
                    options: list = self.current_test.get('options') or []
                    if len(options) > 0:
                        normalized = []
                        for opt in options:
                            if isinstance(opt, dict):
                                # 如果AI 返回的选项使用 'text' 字段存储分号分隔的选项
                                if 'options' not in opt and 'text' in opt:
                                    try:
                                        opts = opt.get('text', '').split(';')
                                    except Exception:
                                        opts = []
                                    normalized.append({
                                        'blank': opt.get('blank'),
                                        'options': [o.strip() for o in opts if o.strip()]
                                    })
                                else:
                                    normalized.append(opt)
                            else:
                                # 非 dict 的项，直接跳过或尝试解析
                                continue
                        self.current_test['options'] = normalized

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
        display_data: dict[str, Any] = {
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
                'ai_available': self.word_manager.ai_available,
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
