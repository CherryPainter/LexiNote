import json
import sys
import os
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_error, log_warning


class AIManager:
    def __init__(self, model="gemma:7b"):
        """初始化AI管理器
        
        Args:
            model: 使用的Ollama模型名称
        """
        self.model = model
        log_info(f"初始化AIManager，使用模型: {model}")
    
    def _ask(self, prompt: str) -> str:
        """向AI模型发送请求的核心方法，使用requests直接调用Ollama API
        
        Args:
            prompt: 提示词
            
        Returns:
            AI模型的响应
        """
        try:
            # 构建API请求数据
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False  # 是否以流式返回
            }
            
            # 发送请求到Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=data,
                timeout=30  # 设置超时时间
            )
            
            # 检查响应状态
            if response.status_code == 200:
                # 解析响应结果
                result = response.json().get("response", "")
                log_info(f"AI调用成功: {prompt[:50]}...")
                return result
            else:
                error_msg = f"API调用失败，状态码: {response.status_code}"
                log_error(error_msg)
                return f"AI功能暂不可用: {error_msg}"
                
        except requests.RequestException as e:
            log_error(f"网络请求失败: {str(e)}")
            return f"AI功能暂不可用: 连接Ollama服务失败，请确认服务已启动"
        except json.JSONDecodeError as e:
            log_error(f"响应解析失败: {str(e)}")
            return "AI功能暂不可用: 响应数据格式错误"
        except Exception as e:
            log_error(f"AI调用失败: {str(e)}")
            return f"AI功能暂不可用: {str(e)}"
    
    def translate(self, text: str, mode: str = "en2zh") -> str:
        """翻译文本
        
        Args:
            text: 要翻译的文本
            mode: 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)
            
        Returns:
            翻译后的文本
        """
        lang = "中文" if mode == "en2zh" else "英文"
        prompt = f"你是一名精准翻译助手，请将以下内容翻译成{lang}，不要添加额外解释：{text}"
        return self._ask(prompt)
    
    def example(self, word: str) -> str:
        """为单词生成例句
        
        Args:
            word: 要生成例句的单词
            
        Returns:
            包含例句和翻译的文本
        """
        prompt = f"请为单词 {word} 生成一个简单的英文例句，并附上中文翻译。"
        return self._ask(prompt)
    
    def evaluate(self, expected: str, user_input: str) -> dict:
        """评估听写结果
        
        Args:
            expected: 期望的正确单词
            user_input: 用户输入的单词
            
        Returns:
            包含准确率和反馈的字典
        """
        prompt = f"请比较用户输入与目标单词：\n目标：{expected}\n用户输入：{user_input}\n请计算拼写相似度（0~1），并说明错误点。"
        result = self._ask(prompt)
        
        # 解析结果，提取准确率和反馈
        try:
            # 尝试从结果中提取准确率
            import re
            accuracy_match = re.search(r'[01]\.\d+', result)
            accuracy = float(accuracy_match.group()) if accuracy_match else 0.0
            return {
                "accuracy": accuracy,
                "feedback": result
            }
        except Exception:
            return {
                "accuracy": 0.0,
                "feedback": result
            }
    
    def advise(self, user_stats: dict) -> str:
        """生成学习建议
        
        Args:
            user_stats: 用户学习统计数据
            
        Returns:
            个性化学习建议
        """
        stats_str = json.dumps(user_stats, ensure_ascii=False)
        prompt = f"请根据以下学习数据，生成一段个性化学习建议：\n{stats_str}"
        return self._ask(prompt)


# 测试用例
if __name__ == "__main__":
    ai_manager = AIManager()
    
    # 测试翻译功能
    print("翻译测试:")
    print(ai_manager.translate("Hello world", "en2zh"))
    print(ai_manager.translate("你好世界", "zh2en"))
    
    # 测试例句生成
    print("\n例句测试:")
    print(ai_manager.example("apple"))
    
    # 测试评估功能
    print("\n评估测试:")
    print(ai_manager.evaluate("apple", "aplle"))
    
    # 测试学习建议
    print("\n学习建议测试:")
    stats = {
        "total_words": 120,
        "mastered": 60,
        "review_needed": 40,
        "average_score": 0.75
    }
    print(ai_manager.advise(stats))