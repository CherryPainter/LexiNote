import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import threading

from logger import log_info, log_error
from .database import ComprehensionDatabase


class PortalManager:
    """题库门户管理器，负责管理离线题库"""

    def __init__(self):
        """初始化门户管理器"""
        self.db_manager = ComprehensionDatabase()
        self._lock = threading.RLock()

    def get_cloze_tests_summary(self) -> List[Dict]:
        """获取完形填空题目列表摘要

        Returns:
            List[Dict]: 题目摘要列表
        """
        try:
            tests = self.db_manager.get_all_cloze_tests()

            # 格式化日期
            for test in tests:
                if 'date_created' in test and test['date_created']:
                    try:
                        # 假设日期是ISO格式字符串或datetime对象
                        if isinstance(test['date_created'], str):
                            dt = datetime.fromisoformat(test['date_created'])
                        else:
                            dt = test['date_created']
                        test['formatted_date'] = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        test['formatted_date'] = str(test['date_created'])

            return tests

        except Exception as e:
            log_error(f"获取完形填空题目列表失败: {str(e)}")
            return []

    def get_reading_comprehensions_summary(self) -> List[Dict]:
        """获取阅读理解题目列表摘要

        Returns:
            List[Dict]: 题目摘要列表
        """
        try:
            tests = self.db_manager.get_all_reading_comprehensions()

            # 格式化日期
            for test in tests:
                if 'date_created' in test and test['date_created']:
                    try:
                        if isinstance(test['date_created'], str):
                            dt = datetime.fromisoformat(test['date_created'])
                        else:
                            dt = test['date_created']
                        test['formatted_date'] = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        test['formatted_date'] = str(test['date_created'])

            return tests

        except Exception as e:
            log_error(f"获取阅读理解题目列表失败: {str(e)}")
            return []

    def delete_cloze_test(self, test_id: int) -> bool:
        """删除完形填空题目

        Args:
            test_id: 题目ID

        Returns:
            bool: 是否删除成功
        """
        try:
            success = self.db_manager.delete_cloze_test(test_id)
            if success:
                log_info(f"从门户删除完形填空题目成功，ID: {test_id}")
            return success
        except Exception as e:
            log_error(f"从门户删除完形填空题目失败: {str(e)}")
            return False

    def delete_reading_comprehension(self, test_id: int) -> bool:
        """删除阅读理解题目

        Args:
            test_id: 题目ID

        Returns:
            bool: 是否删除成功
        """
        try:
            success = self.db_manager.delete_reading_comprehension(test_id)
            if success:
                log_info(f"从门户删除阅读理解题目成功，ID: {test_id}")
            return success
        except Exception as e:
            log_error(f"从门户删除阅读理解题目失败: {str(e)}")
            return False

    def export_cloze_tests(self, export_format: str = "json",
                          output_path: Optional[str] = None) -> Optional[str]:
        """导出完形填空题目

        Args:
            export_format: 导出格式（json/csv）
            output_path: 输出路径，None则使用默认路径

        Returns:
            str: 导出文件路径，None表示失败
        """
        try:
            # 获取所有题目
            all_tests = []
            tests_summary = self.db_manager.get_all_cloze_tests()

            for test_summary in tests_summary:
                test = self.db_manager.get_cloze_test(test_summary['id'])
                if test:
                    all_tests.append(test)

            # 设置输出路径
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = os.path.join('data', 'exports')
                os.makedirs(output_dir, exist_ok=True)

                if export_format == "json":
                    output_path = os.path.join(output_dir, f'cloze_tests_{timestamp}.json')
                else:
                    output_path = os.path.join(output_dir, f'cloze_tests_{timestamp}.csv')

            # 导出数据
            if export_format == "json":
                # 导出为JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_tests, f, ensure_ascii=False, indent=2, default=str)
            else:
                # 导出为CSV
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'title', 'content', 'options', 'answer', 'explanation', 'source', 'date_created']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for test in all_tests:
                        # 将选项转换为字符串
                        test_copy = test.copy()
                        test_copy['options'] = json.dumps(test_copy['options'], ensure_ascii=False)
                        writer.writerow(test_copy)

            log_info(f"成功导出{len(all_tests)}个完形填空题目到: {output_path}")
            return output_path

        except Exception as e:
            log_error(f"导出完形填空题目失败: {str(e)}")
            return None

    def export_reading_comprehensions(self, export_format: str = "json",
                                      output_path: Optional[str] = None) -> Optional[str]:
        """导出阅读理解题目

        Args:
            export_format: 导出格式（json/csv）
            output_path: 输出路径，None则使用默认路径

        Returns:
            str: 导出文件路径，None表示失败
        """
        try:
            # 获取所有题目
            all_tests = []
            tests_summary = self.db_manager.get_all_reading_comprehensions()

            for test_summary in tests_summary:
                test = self.db_manager.get_reading_comprehension(test_summary['id'])
                if test:
                    all_tests.append(test)

            # 设置输出路径
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = os.path.join('data', 'exports')
                os.makedirs(output_dir, exist_ok=True)

                if export_format == "json":
                    output_path = os.path.join(output_dir, f'reading_comprehensions_{timestamp}.json')
                else:
                    output_path = os.path.join(output_dir, f'reading_comprehensions_{timestamp}.csv')

            # 导出数据
            if export_format == "json":
                # 导出为JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_tests, f, ensure_ascii=False, indent=2, default=str)
            else:
                # 导出为CSV
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'article', 'questions', 'answers', 'explanations', 'source', 'date_created']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for test in all_tests:
                        # 将列表转换为字符串
                        test_copy = test.copy()
                        test_copy['questions'] = json.dumps(test_copy['questions'], ensure_ascii=False)
                        test_copy['answers'] = json.dumps(test_copy['answers'], ensure_ascii=False)
                        test_copy['explanations'] = json.dumps(test_copy['explanations'], ensure_ascii=False)
                        writer.writerow(test_copy)

            log_info(f"成功导出{len(all_tests)}个阅读理解题目到: {output_path}")
            return output_path

        except Exception as e:
            log_error(f"导出阅读理解题目失败: {str(e)}")
            return None

    def get_database_statistics(self) -> Dict:
        """获取数据库统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            stats = {
                'cloze_tests_count': self.db_manager.count_cloze_tests(),
                'reading_comprehensions_count': self.db_manager.count_reading_comprehensions(),
                'total_tests': self.db_manager.count_cloze_tests() + self.db_manager.count_reading_comprehensions()
            }
            return stats
        except Exception as e:
            log_error(f"获取数据库统计信息失败: {str(e)}")
            return {
                'cloze_tests_count': 0,
                'reading_comprehensions_count': 0,
                'total_tests': 0
            }
