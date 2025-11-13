#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的听写功能
"""

import os
import sys
import sqlite3
import unittest
import tempfile
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from word_manager import WordManager
from core.dictation import DictationManager
from core.settings_manager import SettingsManager
from core.database_manager import DatabaseManager


class TestDictationRefactor(unittest.TestCase):
    """测试重构后的听写功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时数据库
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        
        # 创建WordManager实例
        self.word_manager = WordManager()
        
        # 创建SettingsManager实例
        self.settings_manager = SettingsManager()
        
        # 手动创建DatabaseManager实例并初始化
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.temp_db_path
        self.db_manager._init_database()
        self.db_manager.create_dictation_tables()
        self.db_manager.create_exercise_sessions_table()
        
        # 将新的DatabaseManager实例设置给WordManager
        self.word_manager.db_manager = self.db_manager
        
        # 创建DictationManager实例
        self.dictation_manager = DictationManager(
            word_manager=self.word_manager,
            settings_manager=self.settings_manager
        )
        
        # 初始化数据库
        self._init_test_data()
    
    def tearDown(self):
        """清理测试环境"""
        # 关闭并删除临时数据库
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)
    
    def _init_test_data(self):
        """初始化测试数据"""
        # 创建默认词库
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        # 先检查默认词库是否已存在
        cursor.execute("SELECT id FROM word_sets WHERE name = '默认词库'")
        existing_set = cursor.fetchone()
        
        if existing_set:
            default_set_id = existing_set[0]
        else:
            # 创建默认词库
            cursor.execute(
                "INSERT INTO word_sets (name, description, source) VALUES (?, ?, ?)",
                ('默认词库', '默认的单词词库', 'default')
            )
            default_set_id = cursor.lastrowid
        
        # 创建测试单词
        test_words = [
            ("apple", "苹果", "ˈæpl", "I eat an apple every day.", 0.7, default_set_id),  # easy
            ("banana", "香蕉", "bəˈnɑːnə", "Bananas are yellow.", 0.8, default_set_id),     # easy
            ("cherry", "樱桃", "ˈtʃeri", "I like cherry pie.", 0.3, default_set_id),        # hard
            ("date", "日期", "deɪt", "What's the date today?", 0.2, default_set_id),       # hard
            ("elderberry", "接骨木果", "ˈeldərberi", "Elderberries are used in jam.", 0.9, default_set_id),  # easy
            ("fig", "无花果", "fɪɡ", "Figs are sweet.", 0.1, default_set_id),            # hard
            ("grape", "葡萄", "ɡreɪp", "Grapes grow on vines.", 0.4, default_set_id),     # medium
            ("honeydew", "哈密瓜", "ˈhʌniduː", "Honeydew is a type of melon.", 0.4, default_set_id),  # medium
            ("ice cream", "冰淇淋", "ˈaɪs kriːm", "I love ice cream.", 0.6, default_set_id),  # easy
            ("jackfruit", "菠萝蜜", "ˈdʒækfruːt", "Jackfruit is very large.", 0.0, default_set_id),  # hard
            ("kiwi", "猕猴桃", "ˈkiːwiː", "Kiwis are fuzzy.", 0.5, default_set_id),        # medium
            ("lemon", "柠檬", "ˈlemən", "Lemons are sour.", 0.05, default_set_id),         # hard
            ("mango", "芒果", "ˈmæŋɡoʊ", "Mangoes are tropical.", 0.75, default_set_id),   # easy
            ("nectarine", "油桃", "ˈnektəriːn", "Nectarines are smooth.", 0.35, default_set_id),  # hard
            ("orange", "橙子", "ˈɔːrɪndʒ", "Oranges are citrus fruits.", 0.65, default_set_id),  # easy
        ]
        
        # 插入测试单词
        for word_data in test_words:
            cursor.execute(
                "INSERT INTO words (word, translation, phonetic, example, proficiency, set_id) VALUES (?, ?, ?, ?, ?, ?)",
                word_data
            )
        conn.commit()
        conn.close()
    
    def test_session_management(self):
        """测试会话管理功能"""
        # 开始会话
        self.dictation_manager.start_session(
            mode="queue",
            source="library",
            batch_size=3,
            difficulty="medium"
        )
        
        # 验证会话是否正确初始化
        self.assertIsNotNone(self.dictation_manager.current_session)
        self.assertEqual(self.dictation_manager.current_session["mode"], "queue")
        self.assertEqual(self.dictation_manager.current_session["source"], "library")
        self.assertEqual(self.dictation_manager.current_session["difficulty"], "medium")
        
        # 验证队列大小
        self.assertEqual(len(self.dictation_manager.current_queue), 3)
        
        # 记录结果
        for word in self.dictation_manager.current_queue[:3]:
            self.dictation_manager.record_result(word, True, 2.5)
        
        # 结束会话
        session_stats = self.dictation_manager.end_session()
        
        # 验证会话统计信息
        self.assertIsInstance(session_stats, dict)
        self.assertIn("session_id", session_stats)
        self.assertIn("duration", session_stats)
        self.assertIn("total_words", session_stats)
        self.assertIn("correct_words", session_stats)
        self.assertIn("accuracy", session_stats)
    
    def test_difficulty_levels(self):
        """测试不同难度级别的单词选择"""
        # 测试简单难度
        self.dictation_manager.start_session(
            mode="queue",
            source="library",
            batch_size=5,
            difficulty="easy"
        )
        easy_words = self.dictation_manager.current_queue
        self.assertEqual(len(easy_words), 5)
        
        # 测试中等难度
        self.dictation_manager.start_session(
            mode="queue",
            source="library",
            batch_size=5,
            difficulty="medium"
        )
        medium_words = self.dictation_manager.current_queue
        self.assertEqual(len(medium_words), 5)
        
        # 测试困难难度
        self.dictation_manager.start_session(
            mode="queue",
            source="library",
            batch_size=5,
            difficulty="hard"
        )
        hard_words = self.dictation_manager.current_queue
        self.assertEqual(len(hard_words), 5)
    
    def test_stats_retrieval(self):
        """测试统计信息获取功能"""
        # 开始新会话
        self.dictation_manager.start_session(
            mode="queue",
            source="library",
            batch_size=2,
            difficulty="medium"
        )
        
        # 获取统计信息
        stats = self.dictation_manager.get_stats(days=7)
        
        # 验证统计信息存在且格式正确
        self.assertIsInstance(stats, dict)
        self.assertIn('total_practices', stats)
        self.assertIn('correct_practices', stats)
        self.assertIn('unique_words', stats)


if __name__ == "__main__":
    unittest.main()