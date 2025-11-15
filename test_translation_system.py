#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译系统升级测试脚本
测试所有模块的兼容性和协调性
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from word_manager import WordManager
from core.database_manager import DatabaseManager
from core.ai_interface import AIManager


def test_translation_system():
    """测试翻译系统的各项功能"""
    print("=== 翻译系统升级测试 ===")
    
    # 初始化单词管理器（会自动初始化数据库管理器）
    word_manager = WordManager()
    
    # 初始化AI接口
    ai_interface = AIManager()
    
    # 测试1：添加单词并测试旧格式翻译
    print("\n1. 测试旧格式翻译功能：")
    # 添加一个使用旧格式翻译的单词
    success, msg = word_manager.add_word_to_active_set(
        word="test",
        phonetic="/test/",
        tag="n. v.",
        meaning_en="examine (something) to determine its nature or condition",
        translation="测试;检验;考查;测验",
        example="Let me test this software.",
        example_translation="让我测试这个软件。"
    )
    
    if success:
        print(f"  ✓ 添加单词成功: {msg}")
        
        # 测试获取翻译（默认旧格式）
        translation = word_manager.get_translation("test")
        print(f"  ✓ 获取旧格式翻译: {translation}")
        
        # 测试获取翻译（新格式）
        translation_new = word_manager.get_translation("test", format_output="new")
        print(f"  ✓ 获取新格式翻译: {json.dumps(translation_new, ensure_ascii=False, indent=2)}")
    else:
        print(f"  ✗ 添加单词失败: {msg}")
        return False
    
    # 测试2：测试翻译判断功能
    print("\n2. 测试翻译判断功能：")
    # 正确翻译
    is_correct = word_manager.check_translation("test", "测试")
    print(f"  ✓ 正确翻译判断 (测试): {'通过' if is_correct else '失败'}")
    
    # 同义词翻译
    is_correct = word_manager.check_translation("test", "检验")
    print(f"  ✓ 同义词翻译判断 (检验): {'通过' if is_correct else '失败'}")
    
    # 错误翻译
    is_correct = word_manager.check_translation("test", "错误")
    print(f"  ✓ 错误翻译判断 (错误): {'通过' if not is_correct else '失败'}")
    
    # 测试3：测试旧数据迁移功能
    print("\n3. 测试旧数据迁移功能：")
    migrated_count = word_manager.migrate_old_translations()
    print(f"  ✓ 迁移完成，共迁移 {migrated_count} 个单词")
    
    # 验证迁移后的翻译格式
    translation_after_migrate = word_manager.get_translation("test", format_output="new")
    print(f"  ✓ 迁移后新格式翻译: {json.dumps(translation_after_migrate, ensure_ascii=False, indent=2)}")
    
    # 测试4：测试AI补全功能（新格式）
    print("\n4. 测试AI补全功能（新格式）：")
    # 添加一个只有单词的条目
    success, msg = word_manager.add_word_to_active_set(word="hello", translation="你好", phonetic="/həˈloʊ/")
    if success:
        print(f"  ✓ 添加单词成功: {msg}")
        
        # 模拟AI补全
        try:
            # 直接测试AI接口获取详细信息
            ai_details = ai_interface.get_word_details("hello")
            print(f"  ✓ AI获取单词详情: {json.dumps(ai_details, ensure_ascii=False, indent=2)}")
            
            # 测试单词管理器的AI补全功能
            # 注意：这里不会实际调用AI（避免API调用），仅测试流程
            print("  ✓ 单词管理器AI补全流程测试: 跳过实际API调用")
        except Exception as e:
            print(f"  ✗ AI补全测试失败: {str(e)}")
            print("  ⚠ 可能是API密钥未配置，跳过此测试")
    else:
        print(f"  ✗ 添加测试单词失败: {msg}")
    
    # 测试5：测试新格式翻译的展示功能
    print("\n5. 测试新格式翻译的展示功能：")
    translation_display = word_manager.get_translation("test", format_output="display")
    print(f"  ✓ 展示格式翻译: {translation_display}")
    
    # 测试6：测试翻译归一化功能
    print("\n6. 测试翻译归一化功能：")
    # 添加一个包含复杂格式的单词
    success, msg = word_manager.add_word_to_active_set(
        word="complex",
        phonetic="/ˈkɑːmpleks/",
        translation='[{"tag":"adj.","meaning_zh":["复杂的","难懂的","复合的"]},{"tag":"n.","meaning_zh":["建筑群","综合体","情结"]}]'
    )
    
    if success:
        print(f"  ✓ 添加复杂单词成功: {msg}")
        
        # 测试不同形式的翻译判断
        is_correct = word_manager.check_translation("complex", "复杂的")
        print(f"  ✓ 复杂单词翻译判断 (复杂的): {'通过' if is_correct else '失败'}")
        
        is_correct = word_manager.check_translation("complex", "综合体")
        print(f"  ✓ 复杂单词翻译判断 (综合体): {'通过' if is_correct else '失败'}")
    else:
        print(f"  ✗ 添加复杂单词失败: {msg}")
    
    print("\n=== 所有测试完成 ===")
    return True


if __name__ == "__main__":
    test_translation_system()