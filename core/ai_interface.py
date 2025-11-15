import json
import sys
import os
import requests
import asyncio
import threading
import functools
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_error, log_warning
from .database_manager import DatabaseManager


class AIManager:
    """优化版AI管理器，加入缓存、异步和请求合并功能"""
    
    # 单例模式实现
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(AIManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model="gemma3n:latest"):
        """初始化AI管理器（只在第一次创建实例时执行）
        
        Args:
            model: 使用的Ollama模型名称
        """
        # 确保初始化只执行一次
        if not AIManager._initialized:
            self.model = model
            self.db_manager = DatabaseManager()
            self._executor = ThreadPoolExecutor(max_workers=2)
            self._semaphore = asyncio.Semaphore(2)  # 限制并发请求数
            self._active_requests = {}  # 正在进行的请求，用于合并重复请求
            self._request_lock = threading.Lock()
            
            # 创建缓存目录
            self.cache_dir = os.path.join('cache', 'ai_text')
            os.makedirs(self.cache_dir, exist_ok=True)
            
            log_info(f"初始化AIManager，使用模型: {model}")
            
            # 验证模型是否可用
            self.available_models = self._get_available_models()
            if self.model not in self.available_models:
                log_warning(f"指定的模型 {model} 可能不可用，可用模型: {', '.join(self.available_models) if self.available_models else '无'}")
            
            # 标记为已初始化
            AIManager._initialized = True
    
    def _get_available_models(self) -> list:
        """获取可用的Ollama模型列表
        
        Returns:
            可用模型名称列表
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            log_warning(f"获取可用模型列表失败: {str(e)}")
        return []
    
    def _ask_sync(self, prompt: str, callback=None) -> str:
        """同步向AI模型发送请求
        
        Args:
            prompt: 提示词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            AI模型的完整响应
        """
        try:
            # 检查服务状态
            try:
                # 使用 /api/tags 作为健康检查端点
                health_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if health_response.status_code != 200:
                    log_error(f"Ollama服务响应异常: {health_response.status_code}")
                    return "AI功能暂不可用: Ollama服务运行异常，请稍后再试"
            except requests.RequestException as e:
                log_error(f"Ollama服务连接失败: {str(e)}")
                return "AI功能暂不可用: Ollama服务未启动或不可访问，请确认服务已运行"
            
            # 构建API请求数据
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": True if callback else False
            }
            
            # 发送请求到Ollama API，增加超时时间
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=data,
                timeout=60,  # 增加超时时间到60秒
                stream=True if callback else False
            )
            
            # 检查响应状态
            if response.status_code == 200:
                complete_response = ""
                
                if callback:
                    # 流式处理响应
                    for line in response.iter_lines():
                        if line:
                            chunk_data = json.loads(line)
                            chunk = chunk_data.get("response", "")
                            done = chunk_data.get("done", False)
                            complete_response += chunk
                            if callback:
                                callback(chunk, done)
                else:
                    # 非流式处理
                    result = response.json().get("response", "")
                    complete_response = result
                
                log_info(f"AI调用成功: {prompt[:50]}...")
                
                # 缓存完整响应
                self.db_manager.cache_ai_response(prompt, complete_response)
                
                return complete_response
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
    
    async def _ask(self, prompt: str, callback=None) -> str:
        """异步向AI模型发送请求，支持请求合并和流式输出
        
        Args:
            prompt: 提示词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            AI模型的响应
        """
        # 如果启用流式输出，跳过缓存和请求合并
        if callback:
            async with self._semaphore:
                return await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    functools.partial(self._ask_sync, prompt, callback)
                )
        
        # 非流式输出模式下的处理
        cached_response = self.db_manager.get_cached_ai_response(prompt)
        if cached_response:
            log_info(f"AI缓存命中: {prompt[:30]}...")
            return cached_response
        
        # 检查是否有相同的请求正在进行
        prompt_hash = hash(prompt)
        with self._request_lock:
            if prompt_hash in self._active_requests:
                # 等待已有请求完成
                future = self._active_requests[prompt_hash]
                log_info(f"合并重复请求: {prompt[:30]}...")
                try:
                    return await future
                finally:
                    # 确保从活跃请求中移除
                    if prompt_hash in self._active_requests:
                        del self._active_requests[prompt_hash]
            
            # 创建新的future
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            self._active_requests[prompt_hash] = future
        
        try:
            # 使用信号量限制并发
            async with self._semaphore:
                # 在线程池中执行同步请求
                result = await loop.run_in_executor(
                    self._executor, 
                    functools.partial(self._ask_sync, prompt)
                )
                
            # 设置future结果
            future.set_result(result)
            return result
            
        except Exception as e:
            # 设置future异常
            future.set_exception(e)
            raise
        finally:
            # 清理活跃请求
            with self._request_lock:
                if prompt_hash in self._active_requests:
                    del self._active_requests[prompt_hash]
    
    async def translate(self, text: str, mode: str = "en2zh", callback=None) -> str:
        """异步翻译文本
        
        Args:
            text: 要翻译的文本
            mode: 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            翻译后的文本
        """
        lang = "中文" if mode == "en2zh" else "英文"
        prompt = f"你是一名精准翻译助手，请将以下内容翻译成{lang}，不要添加额外解释：{text}"
        return await self._ask(prompt, callback)
    
    def translate_sync(self, text: str, mode: str = "en2zh", callback=None) -> str:
        """同步翻译文本（兼容旧接口）
        
        Args:
            text: 要翻译的文本
            mode: 翻译模式
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            翻译后的文本
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.translate(text, mode, callback))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.translate(text, mode, callback))
    
    async def example(self, word: str, callback=None) -> str:
        """异步为单词生成例句
        
        Args:
            word: 要生成例句的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            包含例句和翻译的文本
        """
        prompt = f"请为单词 {word} 生成一个简单的英文例句，并附上中文翻译。\n"
        prompt += "请严格按照以下格式返回，不要添加任何额外内容和解释：\n"
        prompt += "英文例句|中文翻译"
        return await self._ask(prompt, callback)
    
    def example_sync(self, word: str, callback=None) -> str:
        """同步生成例句（兼容旧接口）
        
        Args:
            word: 要生成例句的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            包含例句和翻译的文本
        """
        # 直接调用异步方法
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.example(word, callback))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.example(word, callback))
    
    async def get_word_details(self, word: str, callback=None) -> str:
        """异步获取单词的详细属性（音标、词性、英语释义、中文释义、例句）
        
        Args:
            word: 要获取详细属性的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            包含单词详细属性的JSON字符串
        """
        prompt = f"请提供单词 '{word}' 的详细属性，包括：\n"
        prompt += "1. 音标（phonetic）- 保持英文\n"
        prompt += "2. 词性（tag）- 保持英文\n"
        prompt += "3. 英语释义（meaning_en）- 保持英文\n"
        prompt += "4. 中文释义（meaning_zh）- 保持中文，如果有多个含义，请返回数组形式\n"
        prompt += "5. 例句（example）- 保持英文，附上中文翻译（example_translation）\n"
        prompt += "请严格按照以下JSON格式返回，不要添加任何额外内容和解释：\n"
        prompt += '{"phonetic": "音标", "tag": "词性", "meaning_en": "英语释义", "meaning_zh": ["中文释义1", "中文释义2"], "example": "例句", "example_translation": "例句翻译"}'
        return await self._ask(prompt, callback)
    
    def get_word_details_sync(self, word: str, callback=None) -> str:
        """同步获取单词的详细属性（兼容旧接口）
        
        Args:
            word: 要获取详细属性的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            包含单词详细属性的JSON字符串
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_word_details(word, callback))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_word_details(word, callback))
    
    async def evaluate(self, expected: str, user_input: str, callback=None) -> dict:
        """异步评估听写结果
        
        Args:
            expected: 期望的正确单词
            user_input: 用户输入的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            评估结果字典，包含是否正确、错误原因等信息
        """
        prompt = f"""请评估用户的听写结果：
        正确单词：{expected}
        用户输入：{user_input}
        
        请返回一个JSON格式的评估结果，包含以下字段：
        - is_correct: 布尔值，表示是否正确
        - similarity: 浮点数，表示相似度（0-1）
        - error_type: 字符串，如果错误，说明错误类型（如'spelling', 'missing_letter', 'extra_letter', 'case_error', 'none'）
        - feedback: 字符串，简短的反馈建议
        """
        
        response = await self._ask(prompt, callback)
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'\{[^}]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 如果不是有效的JSON，尝试直接解析
                return {
                    "is_correct": expected.lower() == user_input.lower(),
                    "similarity": 1.0 if expected.lower() == user_input.lower() else 0.5,
                    "error_type": "none" if expected.lower() == user_input.lower() else "spelling",
                    "feedback": "评估完成"
                }
        except Exception as e:
            log_error(f"解析评估结果失败: {str(e)}")
            return {
                "is_correct": expected.lower() == user_input.lower(),
                "similarity": 1.0 if expected.lower() == user_input.lower() else 0.5,
                "error_type": "none" if expected.lower() == user_input.lower() else "unknown",
                "feedback": "评估解析失败"
            }
    
    def evaluate_sync(self, expected: str, user_input: str, callback=None) -> dict:
        """同步评估听写结果（兼容旧接口）
        
        Args:
            expected: 期望的正确单词
            user_input: 用户输入的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)
            
        Returns:
            评估结果字典
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.evaluate(expected, user_input, callback))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.evaluate(expected, user_input, callback))
    
    def get_usage_stats(self) -> dict:
        """获取AI使用统计信息
        
        Returns:
            使用统计字典
        """
        try:
            # 查询缓存命中率
            total_calls = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM ai_cache"
            )[0]['count']
            
            used_calls = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM ai_cache WHERE usage_count > 0"
            )[0]['count']
            
            return {
                "cache_count": total_calls,
                "used_cache_count": used_calls,
                "hit_rate": used_calls / total_calls if total_calls > 0 else 0
            }
        except Exception as e:
            log_error(f"获取使用统计失败: {str(e)}")
            return {
                "cache_count": 0,
                "used_cache_count": 0,
                "hit_rate": 0
            }
    
    def cleanup(self):
        """清理资源"""
        self._executor.shutdown(wait=True)
        log_info("AI管理器资源清理完成")
    
    def advise(self, user_stats: dict) -> str:
        """生成学习建议，考虑正确性和响应时间
        
        Args:
            user_stats: 用户学习统计数据，包含正确率和响应时间等信息
            
        Returns:
            个性化学习建议
        """
        # 构建更详细的提示词，引导AI关注时间因素
        prompt = f"你是一名专业的英语学习顾问，请根据以下学习数据生成详细的个性化建议，使用中文回答。\n"
        prompt += f"特别关注用户的响应时间数据，分析用户在哪些单词上花费时间较长或较短，并提供针对性的建议。\n"
        prompt += f"如果用户对某些单词反应很快且正确率高，可以建议减少复习频率；如果反应慢或正确率低，建议增加练习。\n"
        prompt += f"数据详情：\n{json.dumps(user_stats, ensure_ascii=False)}\n"
        prompt += f"请提供3-5点具体建议，包括单词学习策略、练习方法和时间管理建议。引用部分可以使用英语。"
        
        # 使用同步方式调用_ask方法
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._ask(prompt))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._ask(prompt))


# 测试用例
if __name__ == "__main__":
    ai_manager = AIManager()
    
    # 测试翻译功能
    print("翻译测试:")
    print(ai_manager.translate("Hello world", "en2zh"))
    print(ai_manager.translate("你好世界", "zh2en"))
    
    # 测试例句生成
    print("\n例句测试:")
    print(ai_manager.example_sync("apple"))
    
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