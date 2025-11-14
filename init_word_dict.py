#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化脚本：将默认词库数据导入到数据库中

此脚本会：
1. 检查数据库中是否已有单词数据
2. 如果没有数据，则从word_dict.json文件导入单词到默认词库
3. 无需修改源项目代码，可在程序启动前运行
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import log_info, log_error, log_warning
from core.database_manager import DatabaseManager
from modules.word_importer import import_words_from_json

def init_word_database():
    """初始化单词数据库"""
    log_info("开始初始化单词数据库")
    
    try:
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 检查数据库中是否已有单词
        all_words = db_manager.get_all_words()
        if all_words and len(all_words) > 0:
            log_info(f"数据库中已有 {len(all_words)} 个单词，跳过导入")
            return True
        
        log_info("数据库中没有单词数据，准备从JSON文件导入")
        
        # 获取默认词库ID
        default_set = db_manager.get_word_set_by_name('默认词库')
        if not default_set:
            log_error("默认词库不存在，请先初始化数据库")
            return False
        
        default_set_id = default_set['id']
        
        # 构建word_dict.json文件路径
        word_dict_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'word_dict.json')
        
        # 检查文件是否存在
        if not os.path.exists(word_dict_path):
            log_error(f"词库文件不存在: {word_dict_path}")
            return False
        
        # 导入单词
        log_info(f"开始从 {word_dict_path} 导入单词到默认词库")
        result = import_words_from_json(word_dict_path, default_set_id)
        
        if result['success']:
            log_info(f"单词导入完成: 总计 {result['total']} 个，成功导入 {result['imported']} 个，跳过 {result['skipped']} 个")
            
            # 更新默认词库的单词计数
            cursor = db_manager.execute_read("SELECT COUNT(*) FROM words WHERE set_id = ?", (default_set_id,))
            word_count = cursor.fetchone()[0] if cursor else 0
            
            if word_count > 0:
                db_manager.execute_write(
                    "UPDATE word_sets SET word_count = ? WHERE id = ?",
                    (word_count, default_set_id)
                )
                log_info(f"默认词库单词计数已更新为: {word_count}")
            
            return True
        else:
            log_error(f"单词导入失败: {', '.join(result.get('errors', []))}")
            return False
            
    except Exception as e:
        log_error(f"初始化单词数据库时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_word_database()
    if success:
        log_info("单词数据库初始化成功")
        sys.exit(0)
    else:
        log_error("单词数据库初始化失败")
        sys.exit(1)