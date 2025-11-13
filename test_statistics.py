#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统计模块
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from statistics import StatisticsManager
from core.database_manager import DatabaseManager


def test_statistics_manager():
    """测试统计管理器"""
    print("测试统计模块开始...")
    
    try:
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 创建统计管理器实例
        stats_manager = StatisticsManager(db_manager)
        
        print("\n1. 测试基本统计功能:")
        total_words = stats_manager.get_total_word_count()
        print(f"   总单词数: {total_words}")
        
        learned_words = stats_manager.get_learned_word_count()
        print(f"   已学习单词数: {learned_words}")
        
        total_practices = stats_manager.get_total_practice_count()
        print(f"   总练习次数: {total_practices}")
        
        total_correct = stats_manager.get_total_correct_count()
        print(f"   总正确次数: {total_correct}")
        
        overall_accuracy = stats_manager.get_overall_accuracy()
        print(f"   总体正确率: {overall_accuracy:.2f}")
        
        print("\n2. 测试每日统计功能:")
        today_stats = stats_manager.get_daily_stats()
        print(f"   今日统计: {today_stats}")
        
        print("\n3. 测试每周统计功能:")
        weekly_stats = stats_manager.get_weekly_stats()
        print(f"   最近7天统计: {weekly_stats}")
        
        print("\n4. 测试熟练度分布统计:")
        proficiency_stats = stats_manager.get_proficiency_stats()
        print(f"   熟练度分布: {proficiency_stats}")
        
        print("\n5. 测试词库统计功能:")
        word_set_stats = stats_manager.get_word_set_stats()
        print(f"   词库统计: {word_set_stats}")
        
        print("\n6. 测试最近进度记录:")
        recent_progress = stats_manager.get_recent_progress(5)
        print(f"   最近5条进度记录: {recent_progress}")
        
        print("\n7. 测试综合统计功能:")
        summary_stats = stats_manager.get_summary_stats()
        print(f"   综合统计: {summary_stats}")
        
        print("\n测试统计模块完成!")
        return True
        
    except Exception as e:
        print(f"测试统计模块失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_statistics_manager()