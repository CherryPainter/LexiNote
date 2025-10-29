#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI服务测试脚本
用于验证AI功能是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_error
from core.ai_interface import AIManager
from modules.ai_service import AIService

def test_ai_interface():
    """测试核心AI接口"""
    log_info("=== 开始测试AI接口 ===")
    try:
        ai_manager = AIManager()
        log_info(f"可用模型列表: {ai_manager.available_models}")
        
        # 测试简单对话
        log_info("测试简单对话...")
        response = ai_manager._ask_sync("请简单介绍一下自己")
        log_info(f"AI响应: {response[:100]}...")
        
        # 测试翻译功能
        log_info("测试翻译功能...")
        response = ai_manager.translate_sync("Hello world", "en2zh")
        log_info(f"翻译结果: {response}")
        
        log_info("=== AI接口测试完成 ===")
        return True
    except Exception as e:
        log_error(f"AI接口测试失败: {str(e)}")
        return False

def test_ai_service():
    """测试AI服务模块"""
    log_info("=== 开始测试AI服务模块 ===")
    try:
        ai_service = AIService()
        
        # 检查AI是否可用
        is_available = ai_service.is_ai_available()
        log_info(f"AI服务可用状态: {is_available}")
        
        if is_available:
            log_info("AI服务可用，准备生成测试内容...")
        else:
            log_info("AI服务暂不可用，请检查Ollama服务状态")
        
        log_info("=== AI服务模块测试完成 ===")
        return is_available
    except Exception as e:
        log_error(f"AI服务模块测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    log_info("开始AI功能测试")
    
    # 测试核心接口
    interface_result = test_ai_interface()
    
    # 测试服务模块
    service_result = test_ai_service()
    
    # 输出总体结果
    log_info(f"=== 测试结果汇总 ===")
    log_info(f"核心AI接口: {'成功' if interface_result else '失败'}")
    log_info(f"AI服务模块: {'成功' if service_result else '失败'}")
    
    if interface_result and service_result:
        log_info("🎉 AI功能测试全部通过！")
        return 0
    else:
        log_error("❌ AI功能测试失败，请检查配置和服务状态")
        return 1

if __name__ == "__main__":
    sys.exit(main())