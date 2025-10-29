import logging
import sys
from modules.ai_service import AIService

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lexinote')


def test_reading_comprehension():
    """
    测试阅读理解题目生成功能
    """
    logger.info("=== 开始测试阅读理解题目生成 ===")
    
    # 初始化AI服务
    ai_service = AIService()
    
    # 检查AI服务是否可用
    if not ai_service.ai_available:
        logger.error("错误: AI服务不可用，请检查Ollama服务是否正常运行")
        return False
    
    logger.info("AI服务连接正常")
    
    try:
        # 生成简单的阅读理解题目（使用短篇和较少问题，加快测试速度）
        logger.info("开始生成阅读理解题目...")
        result = ai_service.generate_reading_comprehension(
            level="初级",
            length="短篇",
            question_count=3
        )
        
        if result:
            logger.info(f"✅ 成功生成阅读理解题目，ID: {result['id']}")
            logger.info(f"文章长度: {len(result['article'])} 字符")
            logger.info(f"问题数量: {len(result['questions'])}")
            
            # 打印部分内容用于验证
            logger.info("\n文章前100个字符:")
            logger.info(result['article'][:100] + "...")
            
            logger.info("\n问题示例:")
            for i, question in enumerate(result['questions'][:2]):
                logger.info(f"{i+1}. {question}")
                logger.info(f"   答案: {result['answers'][i]}")
                logger.info(f"   解析: {result['explanations'][i]}")
            
            return True
        else:
            logger.error("❌ 生成阅读理解题目失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_reading_comprehension()
    
    if success:
        logger.info("\n🎉 测试成功完成！阅读理解功能已修复")
        sys.exit(0)
    else:
        logger.error("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)