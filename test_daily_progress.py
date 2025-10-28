#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试今日学习进度检测功能
"""
import os
import json
from datetime import datetime

# 导入WordManager
from word_manager import WordManager

def test_daily_progress_system():
    """测试每日学习进度检测系统"""
    print("开始测试每日学习进度检测功能...")
    
    # 初始化WordManager
    word_manager = WordManager()
    
    # 模拟未完成学习的情况
    print("\n1. 测试未完成学习的情况:")
    # 确保daily_learning.json中没有今日的完成记录
    today = datetime.now().strftime('%Y-%m-%d')
    daily_learning_file = 'data/daily_learning.json'
    
    # 读取并修改daily_learning.json
    if os.path.exists(daily_learning_file):
        with open(daily_learning_file, 'r', encoding='utf-8') as f:
            daily_data = json.load(f)
        
        # 删除今日记录或设置为未完成
        if today in daily_data:
            daily_data[today]['completed'] = False
            with open(daily_learning_file, 'w', encoding='utf-8') as f:
                json.dump(daily_data, f, ensure_ascii=False, indent=2)
            print(f"  - 设置今日({today})学习状态为未完成")
    
    # 检查进度
    is_completed = word_manager.check_today_progress_completed()
    print(f"  - check_today_progress_completed() 返回: {is_completed}")
    print(f"  - 期望结果: False")
    
    # 模拟完成学习的情况
    print("\n2. 测试已完成学习的情况:")
    # 创建今日完成记录
    daily_data = word_manager._load_data(daily_learning_file)
    daily_data[today] = {
        'completed': True,
        'completed_at': datetime.now().isoformat(),
        'words_learned': 10,
        'words_to_review': 2
    }
    word_manager._save_data(daily_learning_file, daily_data)
    print(f"  - 设置今日({today})学习状态为已完成")
    
    # 再次检查进度
    is_completed = word_manager.check_today_progress_completed()
    print(f"  - check_today_progress_completed() 返回: {is_completed}")
    print(f"  - 期望结果: True")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_daily_progress_system()