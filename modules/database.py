import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading

from logger import log_info, log_error


class ComprehensionDatabase:
    """理解类练习数据库管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化数据库管理器"""
        with self._lock:
            if not hasattr(self, '_initialized'):
                self.data_dir = 'data'
                self.db_path = os.path.join(self.data_dir, 'lexinote.db')
                
                # 创建数据目录
                os.makedirs(self.data_dir, exist_ok=True)
                
                # 初始化数据库表
                self._init_tables()
                
                self._initialized = True
    
    def _init_tables(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建完形填空表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cloze_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    options TEXT NOT NULL,  -- JSON格式存储选项
                    answer TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    source TEXT NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建阅读理解表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_comprehensions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article TEXT NOT NULL,
                    questions TEXT NOT NULL,  -- JSON格式存储题目列表
                    answers TEXT NOT NULL,    -- JSON格式存储答案列表
                    explanations TEXT NOT NULL,  -- JSON格式存储解析列表
                    source TEXT NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建删除日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS delete_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    module_type TEXT NOT NULL,  -- 'cloze' 或 'reading'
                    question_data TEXT NOT NULL,  -- JSON格式存储被删除的数据
                    delete_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            log_info("理解类练习数据库表初始化完成")
            
        except Exception as e:
            log_error(f"初始化理解类练习数据库表失败: {str(e)}")
    
    def add_cloze_test(self, title: str, content: str, options: List[Dict], 
                      answer: str, explanation: str, source: str = 'AI生成') -> int:
        """添加完形填空题目
        
        Args:
            title: 题目标题
            content: 完形填空原文
            options: 选项列表
            answer: 正确答案
            explanation: 题目解析
            source: 来源
            
        Returns:
            int: 新添加题目的ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 将选项列表转换为JSON字符串
            options_json = json.dumps(options, ensure_ascii=False)
            
            cursor.execute(
                '''INSERT INTO cloze_tests (title, content, options, answer, explanation, source) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (title, content, options_json, answer, explanation, source)
            )
            
            test_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            log_info(f"添加完形填空题目成功，ID: {test_id}")
            return test_id
            
        except Exception as e:
            log_error(f"添加完形填空题目失败: {str(e)}")
            return -1
    
    def get_cloze_test(self, test_id: Optional[int] = None) -> Optional[Dict]:
        """获取完形填空题目
        
        Args:
            test_id: 题目ID，None则随机获取
            
        Returns:
            Dict: 题目信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if test_id is None:
                # 随机获取一个题目
                cursor.execute('SELECT * FROM cloze_tests ORDER BY RANDOM() LIMIT 1')
            else:
                cursor.execute('SELECT * FROM cloze_tests WHERE id = ?', (test_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'options': json.loads(row[3]),
                    'answer': row[4],
                    'explanation': row[5],
                    'source': row[6],
                    'date_created': row[7]
                }
            return None
            
        except Exception as e:
            log_error(f"获取完形填空题目失败: {str(e)}")
            return None
    
    def get_all_cloze_tests(self) -> List[Dict]:
        """获取所有完形填空题目列表
        
        Returns:
            List[Dict]: 题目信息列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, title, source, date_created FROM cloze_tests ORDER BY date_created DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'id': row[0],
                'title': row[1],
                'source': row[2],
                'date_created': row[3]
            } for row in rows]
            
        except Exception as e:
            log_error(f"获取所有完形填空题目失败: {str(e)}")
            return []
    
    def add_reading_comprehension(self, article: str, questions: List[str], 
                                 answers: List[str], explanations: List[str], 
                                 source: str = 'AI生成') -> int:
        """添加阅读理解题目
        
        Args:
            article: 阅读原文
            questions: 题目列表
            answers: 答案列表
            explanations: 解析列表
            source: 来源
            
        Returns:
            int: 新添加题目的ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 将列表转换为JSON字符串
            questions_json = json.dumps(questions, ensure_ascii=False)
            answers_json = json.dumps(answers, ensure_ascii=False)
            explanations_json = json.dumps(explanations, ensure_ascii=False)
            
            cursor.execute(
                '''INSERT INTO reading_comprehensions (article, questions, answers, explanations, source) 
                   VALUES (?, ?, ?, ?, ?)''',
                (article, questions_json, answers_json, explanations_json, source)
            )
            
            test_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            log_info(f"添加阅读理解题目成功，ID: {test_id}")
            return test_id
            
        except Exception as e:
            log_error(f"添加阅读理解题目失败: {str(e)}")
            return -1
    
    def get_reading_comprehension(self, test_id: Optional[int] = None) -> Optional[Dict]:
        """获取阅读理解题目
        
        Args:
            test_id: 题目ID，None则随机获取
            
        Returns:
            Dict: 题目信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if test_id is None:
                # 随机获取一个题目
                cursor.execute('SELECT * FROM reading_comprehensions ORDER BY RANDOM() LIMIT 1')
            else:
                cursor.execute('SELECT * FROM reading_comprehensions WHERE id = ?', (test_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'article': row[1],
                    'questions': json.loads(row[2]),
                    'answers': json.loads(row[3]),
                    'explanations': json.loads(row[4]),
                    'source': row[5],
                    'date_created': row[6]
                }
            return None
            
        except Exception as e:
            log_error(f"获取阅读理解题目失败: {str(e)}")
            return None
    
    def get_all_reading_comprehensions(self) -> List[Dict]:
        """获取所有阅读理解题目列表
        
        Returns:
            List[Dict]: 题目信息列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, source, date_created FROM reading_comprehensions ORDER BY date_created DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'id': row[0],
                'source': row[1],
                'date_created': row[2]
            } for row in rows]
            
        except Exception as e:
            log_error(f"获取所有阅读理解题目失败: {str(e)}")
            return []
    
    def _log_deletion(self, conn, question_id: int, module_type: str, question_data: Dict):
        """记录删除操作到日志表
        
        Args:
            conn: 数据库连接
            question_id: 题目ID
            module_type: 模块类型 ('cloze' 或 'reading')
            question_data: 被删除的题目数据
        """
        try:
            cursor = conn.cursor()
            data_json = json.dumps(question_data, ensure_ascii=False)
            cursor.execute(
                '''INSERT INTO delete_logs (question_id, module_type, question_data)
                   VALUES (?, ?, ?)''',
                (question_id, module_type, data_json)
            )
            log_info(f"记录删除日志成功，ID: {question_id}, 类型: {module_type}")
        except Exception as e:
            log_error(f"记录删除日志失败: {str(e)}")
    
    def delete_cloze_test(self, test_id: int) -> bool:
        """删除完形填空题目
        
        Args:
            test_id: 题目ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先获取要删除的数据用于日志记录
            cursor.execute('SELECT * FROM cloze_tests WHERE id = ?', (test_id,))
            row = cursor.fetchone()
            
            if row:
                # 构建题目数据字典
                question_data = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'options': json.loads(row[3]) if row[3] else [],
                    'answer': row[4],
                    'explanation': row[5],
                    'source': row[6],
                    'date_created': row[7]
                }
                
                # 执行删除
                cursor.execute('DELETE FROM cloze_tests WHERE id = ?', (test_id,))
                affected_rows = cursor.rowcount
                
                if affected_rows > 0:
                    # 记录删除日志
                    self._log_deletion(conn, test_id, 'cloze', question_data)
                    conn.commit()
                    conn.close()
                    log_info(f"删除完形填空题目成功，ID: {test_id}")
                    return True
                
            conn.close()
            return False
            
        except Exception as e:
            log_error(f"删除完形填空题目失败: {str(e)}")
            return False
    
    def delete_reading_comprehension(self, test_id: int) -> bool:
        """删除阅读理解题目
        
        Args:
            test_id: 题目ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先获取要删除的数据用于日志记录
            cursor.execute('SELECT * FROM reading_comprehensions WHERE id = ?', (test_id,))
            row = cursor.fetchone()
            
            if row:
                # 构建题目数据字典
                question_data = {
                    'id': row[0],
                    'article': row[1],
                    'questions': json.loads(row[2]) if row[2] else [],
                    'answers': json.loads(row[3]) if row[3] else [],
                    'explanations': json.loads(row[4]) if row[4] else [],
                    'source': row[5],
                    'date_created': row[6]
                }
                
                # 执行删除
                cursor.execute('DELETE FROM reading_comprehensions WHERE id = ?', (test_id,))
                affected_rows = cursor.rowcount
                
                if affected_rows > 0:
                    # 记录删除日志
                    self._log_deletion(conn, test_id, 'reading', question_data)
                    conn.commit()
                    conn.close()
                    log_info(f"删除阅读理解题目成功，ID: {test_id}")
                    return True
            
            conn.close()
            return False
            
        except Exception as e:
            log_error(f"删除阅读理解题目失败: {str(e)}")
            return False
    
    def count_cloze_tests(self) -> int:
        """统计完形填空题目数量
        
        Returns:
            int: 题目数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM cloze_tests')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            log_error(f"统计完形填空题目数量失败: {str(e)}")
            return 0
    
    def count_reading_comprehensions(self) -> int:
        """统计阅读理解题目数量
        
        Returns:
            int: 题目数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM reading_comprehensions')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            log_error(f"统计阅读理解题目数量失败: {str(e)}")
            return 0