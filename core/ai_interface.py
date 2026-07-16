import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import threading
import functools
import requests
from concurrent.futures import ThreadPoolExecutor
from logger import log_info, log_error, log_warning
from .database_manager import DatabaseManager
from .settings_manager import SettingsManager


# 请求超时（连接, 读取）与重试配置，避免 UI 长时间卡死
_CLOUD_TIMEOUT = (10, 60)
_OLLAMA_TIMEOUT = (10, 60)
_MAX_RETRIES = 2
_RETRY_BACKOFF = 0.5
# AI 不可用时的返回哨兵前缀（与下方降级逻辑保持一致）
_AI_UNAVAILABLE_PREFIX = "AI功能暂不可用"


def _normalize_cloud_url(url: str) -> str:
    """自动补全 https:// 前缀，避免 requests 报 "No scheme supplied"

    Args:
        url: 用户输入的 API 地址（可能缺少协议头）

    Returns:
        带协议头的完整 URL；空字符串原样返回
    """
    url = (url or "").strip()
    if url and "://" not in url:
        return "https://" + url
    return url


def _is_ai_unavailable(text: str) -> bool:
    """判断 AI 调用返回是否为「不可用」哨兵字符串

    Args:
        text: AI 调用返回内容

    Returns:
        bool: 若为不可用哨兵则返回 True
    """
    return isinstance(text, str) and text.startswith(_AI_UNAVAILABLE_PREFIX)


class AIManager:
    """优化版AI管理器，加入缓存、异步和请求合并功能，支持本地Ollama和云端模型"""

    # 单例模式实现
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(AIManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, model=None):
        """初始化AI管理器（只在第一次创建实例时执行）

        Args:
            model: 使用的模型名称，如果为None则从设置中获取
        """
        # 确保初始化只执行一次
        if not AIManager._initialized:
            # 从设置中获取模型，如果没有则使用默认值
            self.settings_manager = SettingsManager()
            if model is None:
                model = self.settings_manager.get_ai_model()

            # 加载云端配置 + AI 模式（off / local / cloud）
            self._load_cloud_config()
            self.ai_mode = self.settings_manager.get_ai_mode()

            # 仅按当前模式对齐默认模型，避免“先找本地再找云端”的跨渠道试探：
            # - cloud 模式：使用云端模型名
            # - local 模式：使用本地模型名（默认 gemma3n:latest）
            # - off 模式：AI 不使用，模型标识仅作展示
            if self.ai_mode == "cloud" and self.cloud_model_name:
                model = self.cloud_model_name
                log_info(f"云端模式已启用，使用模型: {model}")
            elif self.ai_mode == "local" and not model:
                model = self.settings_manager.get_ai_model() or "gemma3n:latest"

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

            # 验证模型是否可用（AI 关闭时不探测，也不警告）
            self.available_models = self._get_available_models()
            if self.ai_mode != "off" and self.model not in self.available_models:
                available_models_str = ', '.join(self.available_models) \
                    if self.available_models else '无'
                log_warning(
                    f"指定的模型 {model} 可能不可用，可用模型: {available_models_str}"
                )

            # 标记为已初始化
            AIManager._initialized = True

    def _load_cloud_config(self):
        """加载云端模型配置"""
        self.cloud_enabled = self.settings_manager.get_setting("cloud_ai_enabled", False)
        # 自动补全 https:// 前缀，避免 requests 报 "No scheme supplied"
        self.cloud_api_url = _normalize_cloud_url(
            self.settings_manager.get_setting("cloud_ai_api_url", "")
        )
        self.cloud_api_key = self.settings_manager.get_setting("cloud_ai_api_key", "")
        self.cloud_model_name = self.settings_manager.get_setting("cloud_ai_model_name", "")

    def _is_cloud_model(self, model_name: str = None) -> bool:
        """判断当前是否使用云端模型

        Args:
            model_name: 模型名称，如果为None则使用当前模型

        Returns:
            bool: 是否使用云端模型
        """
        if model_name is None:
            model_name = self.model
        # 如果云端功能启用且当前模型匹配云端配置模型，则使用云端
        return (
            self.cloud_enabled
            and self.cloud_api_url
            and self.cloud_api_key
            and model_name == self.cloud_model_name
        )

    def _use_cloud_provider(self) -> bool:
        """判断当前是否应使用云端 provider

        由 AI 模式决定：仅当模式为 cloud 且云端配置完整时走云端。
        不再依赖当前 model 名是否等于云端模型名，也不在 local/off 模式下用云端。

        Returns:
            bool: 是否应使用云端 provider
        """
        return bool(
            self.ai_mode == "cloud"
            and self.cloud_api_url
            and self.cloud_api_key
        )

    def _get_available_models(self) -> list:
        """按当前 AI 模式获取可用模型列表（渠道互斥，不跨渠道试探）

        - off  : 不探测任何渠道，返回空列表
        - local: 仅探测本地 Ollama
        - cloud: 仅登记云端模型名（不发任何网络请求）

        Returns:
            可用模型名称列表
        """
        models = []

        # 以当前模式为准，确保 ai_mode 与云端配置一致
        self.ai_mode = self.settings_manager.get_ai_mode()
        self._load_cloud_config()

        if self.ai_mode == "local":
            # 仅探测本地 Ollama
            try:
                response = requests.get(
                    "http://localhost:11434/api/tags",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    ollama_models = [model["name"] for model in data.get("models", [])]
                    models.extend(ollama_models)
                    log_info(f"获取到本地Ollama模型: {ollama_models}")
            except requests.RequestException as e:
                log_warning(f"获取本地Ollama模型列表失败: {str(e)}")
        elif self.ai_mode == "cloud":
            # 仅登记云端模型，不发起任何网络请求（实际连通性在调用时校验）
            if self.cloud_model_name:
                models.append(self.cloud_model_name)
                log_info(f"添加云端模型: {self.cloud_model_name}")
        # ai_mode == "off": 不探测任何渠道

        return models

    def _test_cloud_connection(self) -> bool:
        """测试云端模型连接是否可用

        Returns:
            bool: 云端连接是否可用
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.cloud_api_key}",
                "Content-Type": "application/json"
            }
            # 发送一个简单的测试请求
            data = {
                "model": self.cloud_model_name,
                "messages": [{"role": "user", "content": "hello"}],
                "max_tokens": 5
            }
            response = requests.post(
                self.cloud_api_url,
                headers=headers,
                json=data,
                timeout=15
            )
            if response.status_code == 200:
                log_info("云端模型连接测试成功")
                return True
            else:
                log_warning(f"云端模型连接测试失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            log_warning(f"云端模型连接测试失败: {str(e)}")
            return False

    def _ask_sync(self, prompt: str, callback=None, temperature=None) -> str:
        """同步向AI模型发送请求，支持本地Ollama和云端模型

        Args:
            prompt: 提示词
            callback: 用于处理流式输出的回调函数，
                      接收参数：(chunk: str, done: bool)

        Returns:
            AI模型的响应
        """
        # 每次请求都按最新设置判定模式，确保运行时切换即时生效
        self.ai_mode = self.settings_manager.get_ai_mode()
        self._load_cloud_config()

        # AI 关闭：直接返回哨兵，不探测任何渠道（核心功能靠本地能力兜底）
        if self.ai_mode == "off":
            return f"{_AI_UNAVAILABLE_PREFIX}: AI 功能未启用"

        # 模式决定渠道，渠道互斥，不跨渠道回退：
        # cloud 模式只用云端；local 模式只用本地 Ollama
        if self._use_cloud_provider():
            return self._ask_cloud_sync(prompt, callback, temperature)

        return self._ask_ollama_sync(prompt, callback, temperature)

    def _safe_post(self, url, headers, data, timeout, stream=False,
                   max_retries: int = _MAX_RETRIES):
        """带指数退避重试的 POST 请求（仅在网络异常时重试）

        拿到响应后无论状态码如何都原样返回（非 200 由调用方按需处理），
        避免在 API Key 错误等确定性失败时无意义重试。

        Args:
            url: 请求地址
            headers: 请求头
            data: 请求体（dict）
            timeout: 超时（秒或 (connect, read) 元组）
            stream: 是否流式
            max_retries: 最大重试次数

        Returns:
            requests.Response

        Raises:
            requests.RequestException: 重试耗尽后仍失败
        """
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                return requests.post(
                    url, headers=headers, json=data,
                    timeout=timeout, stream=stream
                )
            except requests.RequestException as e:
                last_exc = e
                if attempt < max_retries:
                    wait = min(_RETRY_BACKOFF * (2 ** attempt), 3)
                    log_warning(
                        f"AI 请求网络异常（第{attempt + 1}次），"
                        f"{wait:.1f}s 后重试: {e}"
                    )
                    time.sleep(wait)
        raise last_exc if last_exc else requests.RequestException("未知请求错误")

    def _ask_ollama_sync(self, prompt: str, callback=None, temperature=None) -> str:
        """同步向本地Ollama模型发送请求

        Args:
            prompt: 提示词
            callback: 用于处理流式输出的回调函数

        Returns:
            AI模型的完整响应
        """
        try:
            # 检查服务状态
            try:
                health_response = requests.get(
                    "http://localhost:11434/api/tags",
                    timeout=5
                )
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
            if temperature is not None:
                data["temperature"] = temperature

            # 发送请求到Ollama API
            response = self._safe_post(
                "http://localhost:11434/api/generate",
                headers={},
                data=data,
                timeout=_OLLAMA_TIMEOUT,
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
                            chunk = chunk_data.get("response") or ""
                            done = chunk_data.get("done", False)
                            complete_response += chunk
                            if callback:
                                callback(chunk, done)
                else:
                    # 非流式处理
                    result = response.json().get("response", "")
                    complete_response = result

                log_info(f"Ollama AI调用成功: {prompt[:50]}...")

                # 缓存完整响应
                self.db_manager.cache_ai_response(prompt, complete_response)

                return complete_response
            else:
                error_msg = f"API调用失败，状态码: {response.status_code}"
                log_error(error_msg)
                return f"AI功能暂不可用: {error_msg}"

        except requests.RequestException as e:
            log_error(f"网络请求失败: {str(e)}")
            return "AI功能暂不可用: 连接Ollama服务失败，请确认服务已启动"
        except json.JSONDecodeError as e:
            log_error(f"响应解析失败: {str(e)}")
            return "AI功能暂不可用: 响应数据格式错误"
        except Exception as e:
            log_error(f"AI调用失败: {str(e)}")
            return f"AI功能暂不可用: {str(e)}"

    def _ask_cloud_sync(self, prompt: str, callback=None, temperature=None) -> str:
        """同步向云端模型发送请求（OpenAI兼容API格式）

        Args:
            prompt: 提示词
            callback: 用于处理流式输出的回调函数

        Returns:
            AI模型的完整响应
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.cloud_api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.cloud_model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "stream": True if callback else False
            }
            if temperature is not None:
                data["temperature"] = temperature

            response = self._safe_post(
                self.cloud_api_url,
                headers=headers,
                data=data,
                timeout=_CLOUD_TIMEOUT,
                stream=True if callback else False
            )

            if response.status_code == 200:
                complete_response = ""

                if callback:
                    # 流式处理响应（OpenAI格式）
                    for line in response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data: '):
                                json_str = line_str[6:]
                                if json_str.strip() == '[DONE]':
                                    callback("", True)
                                    break
                                try:
                                    chunk_data = json.loads(json_str)
                                    delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                    # 流式首包或推理型模型的 chunk 里 content 可能为 null，
                                    # .get("content", "") 在键存在但值为 null 时返回 None，
                                    # 会导致 str += None 报错，这里统一兜底为空串
                                    chunk = delta.get("content") or ""
                                    done = chunk_data.get("choices", [{}])[0].get("finish_reason") is not None
                                    complete_response += chunk
                                    callback(chunk, done)
                                except json.JSONDecodeError:
                                    continue
                else:
                    # 非流式处理
                    result_data = response.json()
                    complete_response = result_data.get("choices", [{}])[0].get("message", {}).get("content") or ""

                log_info(f"云端AI调用成功: {prompt[:50]}...")

                # 缓存完整响应
                self.db_manager.cache_ai_response(prompt, complete_response)

                return complete_response
            else:
                error_msg = f"云端API调用失败，状态码: {response.status_code}"
                log_error(error_msg)
                return f"AI功能暂不可用: {error_msg}"

        except requests.RequestException as e:
            log_error(f"云端网络请求失败: {str(e)}")
            return "AI功能暂不可用: 连接云端服务失败，请检查网络或配置"
        except json.JSONDecodeError as e:
            log_error(f"云端响应解析失败: {str(e)}")
            return "AI功能暂不可用: 云端响应数据格式错误"
        except Exception as e:
            log_error(f"云端AI调用失败: {str(e)}")
            return f"AI功能暂不可用: {str(e)}"

    async def _ask(self, prompt: str, callback=None, temperature=None) -> str:
        """异步向AI模型发送请求，支持请求合并和流式输出

        Args:
            prompt: 提示词
            callback: 用于处理流式输出的回调函数，
                      接收参数：(chunk: str, done: bool)

        Returns:
            AI模型的响应
        """
        # 如果启用流式输出，跳过缓存和请求合并
        if callback:
            async with self._semaphore:
                return await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    functools.partial(self._ask_sync, prompt, callback, temperature)
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
                    functools.partial(self._ask_sync, prompt, None, temperature)
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

    # ---------- 本地降级（无 AI 时保证基本可用） ----------

    def _load_local_dict(self) -> dict:
        """懒加载本地词典 data/word_dict.json，仅在首次调用时读取"""
        if not hasattr(self, '_local_dict'):
            self._local_dict = {}
            try:
                path = os.path.join('data', 'word_dict.json')
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self._local_dict = json.load(f)
            except Exception as e:
                log_warning(f"加载本地词典失败: {str(e)}")
                self._local_dict = {}
        return self._local_dict

    def _local_translate(self, text: str, mode: str) -> str:
        """本地翻译降级：单词级查本地词典，否则保留原文并提示离线"""
        if mode == "en2zh":
            meaning = self._load_local_dict().get(text.strip())
            if meaning:
                return meaning
            return f"（离线翻译不可用，已保留原文）{text}"
        return f"（离线翻译不可用，已保留原文）{text}"

    def _local_word_details(self, word: str) -> str:
        """本地单词详情降级：仅提供中文释义，其余字段留空"""
        meaning = self._load_local_dict().get(word.strip())
        meaning_zh = [m.strip() for m in meaning.split(';') if m.strip()] \
            if meaning else []
        result = {
            "phonetic": "",
            "tag": "",
            "meaning_en": "",
            "meaning_zh": meaning_zh if meaning_zh else [""],
            "example": "",
            "example_translation": ""
        }
        return json.dumps(result, ensure_ascii=False)

    def _local_example(self, word: str) -> str:
        """本地例句降级：无离线例句库，给出友好提示而非报错"""
        return f"（离线模式，暂无「{word}」的本地例句，连接网络后可重新生成。）"

    def _default_advice(self, user_stats: dict) -> str:
        """本地学习建议降级：依据正确率给出规则化建议"""
        try:
            mastered = user_stats.get('mastered', 0)
            review_needed = user_stats.get('review_needed', 0)
            total = (user_stats.get('total_words', 0)
                     or (mastered + review_needed) or 1)
            rate = mastered / total if total else 0
            tips = [
                f"当前整体掌握率约 {rate * 100:.0f}%，建议每天保持固定时长复习以巩固记忆。"
            ]
            if rate >= 0.7:
                tips.append("掌握情况良好，可适当减少已掌握单词的复习频率，把时间留给薄弱词。")
            elif rate >= 0.4:
                tips.append("掌握情况中等，建议增加每天的新词量与复习轮次。")
            else:
                tips.append("掌握率偏低，建议降低单次学习量、提高复习频率，先打牢基础。")
            if review_needed:
                tips.append(f"有 {review_needed} 个单词需要重点复习，请优先安排。")
            tips.append("合理安排碎片时间，利用听写和例句巩固拼写与用法。")
            return "\n".join(f"{i + 1}. {t}" for i, t in enumerate(tips))
        except Exception as e:
            log_warning(f"生成默认学习建议失败: {str(e)}")
            return "保持每日学习节奏，重点复习掌握度较低的单词即可。"

    async def translate(self, text: str, mode: str = "en2zh", callback=None) -> str:
        """异步翻译文本

        Args:
            text: 要翻译的文本
            mode: 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)
            callback: 用于处理流式输出的回调函数，
                      接收参数：(chunk: str, done: bool)

        Returns:
            翻译后的文本
        """
        lang = "中文" if mode == "en2zh" else "英文"
        prompt = (
            f"你是一名精准翻译助手，请将以下内容翻译成{lang}，不要添加额外解释："
            f"{text}"
        )
        result = await self._ask(prompt, callback)
        # AI 不可用时切换到本地词典兜底（仅非流式场景，流式由调用方处理）
        if callback is None and _is_ai_unavailable(result):
            log_warning("翻译 AI 不可用，启用本地降级")
            return self._local_translate(text, mode)
        return result

    def translate_sync(self, text: str, mode: str = "en2zh", callback=None) -> str:
        """同步翻译文本（兼容旧接口）

        Args:
            text: 要翻译的文本
            mode: 翻译模式
            callback: 用于处理流式输出的回调函数，
                      接收参数：(chunk: str, done: bool)

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
        prompt = (
            f"请为单词 '{word}' 写一句自然、真实、有具体语境的英文例句，并附上中文翻译。"
            f"\n"
        )
        prompt += "要求：\n"
        prompt += f"1. 句子必须体现该单词的常见用法或搭配，禁止使用 \"This is an example sentence with the word '{word}'\" 这类无意义的模板句。\n"
        prompt += "2. 句子长度控制在 15 个单词以内，适合英语学习者阅读。\n"
        prompt += "3. 只返回一行：英文例句|中文翻译。不要添加解释、编号、引号或额外内容。\n"
        result = await self._ask(prompt, callback)
        if callback is None and _is_ai_unavailable(result):
            return self._local_example(word)
        return result

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
        """异步获取单词的详细属性

        Args:
            word: 要获取详细属性的单词
            callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

        Returns:
            包含单词详细属性的JSON字符串
        """
        prompt = f"请提供单词 '{word}' 的详细属性，包括：\n"
        prompt += "1. 音标（phonetic）- 保持英文\n"
        prompt += "2. 词性（tag）- 保持英文，如果有多个词性，请用斜杠"
        prompt += "   分隔，如'adjective/noun'\n"
        prompt += "3. 英语释义（meaning_en）- 保持英文\n"
        prompt += "4. 中文释义（meaning_zh）- 保持中文，如果有多个含义，请返回数组形式\n"
        prompt += "5. 例句（example）- 只保持英文，要求自然、真实、有具体语境，长度控制在 15 个单词以内。\n"
        prompt += "   禁止使用类似 'This is an example sentence with the word...' 的模板句。\n"
        prompt += "6. 例句翻译（example_translation）- 只保持中文，是例句的中文翻译\n"
        prompt += "请严格按照以下JSON格式返回，不要添加任何额外内容和解释：\n"
        prompt += '''{
  "phonetic": "音标",
  "tag": "词性",
  "meaning_en": "英语释义",
  "meaning_zh": ["中文释义1", "中文释义2"],
  "example": "英文例句",
  "example_translation": "中文翻译"
}'''
        result = await self._ask(prompt, callback)
        if callback is None and _is_ai_unavailable(result):
            log_warning(f"单词详情 AI 不可用，启用本地降级: {word}")
            return self._local_word_details(word)
        return result

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
            return loop.run_until_complete(
                self.get_word_details(word, callback)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.get_word_details(word, callback)
            )

    async def evaluate(
        self, expected: str, user_input: str, callback=None
    ) -> dict:
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
        - error_type: 字符串，如果错误，说明错误类型（如
          'spelling', 'missing_letter', 'extra_letter', 'case_error', 'none'）
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
                is_correct = expected.lower() == user_input.lower()
                return {
                    "is_correct": is_correct,
                    "similarity": 1.0 if is_correct else 0.5,
                    "error_type": "none" if is_correct else "spelling",
                    "feedback": "评估完成"
                }
        except Exception as e:
            log_error(f"解析评估结果失败: {str(e)}")
            is_correct = expected.lower() == user_input.lower()
            return {
                "is_correct": is_correct,
                "similarity": 1.0 if is_correct else 0.5,
                "error_type": "none" if is_correct else "unknown",
                "feedback": "评估解析失败"
            }

    def evaluate_sync(
        self, expected: str, user_input: str, callback=None
    ) -> dict:
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
            return loop.run_until_complete(
                self.evaluate(expected, user_input, callback)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.evaluate(expected, user_input, callback)
            )

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

    def is_ai_available(self) -> bool:
        """按当前 AI 模式判断是否存在可用的 AI

        - off  : 始终不可用（不探测任何渠道）
        - cloud: 云端配置完整即视为可用，不在初始化时预发网络请求（实际连通性在
                 请求时校验），避免阻塞启动与无谓的外网探测。
        - local: 检查本地 Ollama 服务是否存活。

        Returns:
            bool: 当前模式下是否存在可用 AI
        """
        self.ai_mode = self.settings_manager.get_ai_mode()
        self._load_cloud_config()

        if self.ai_mode == "off":
            return False
        if self.ai_mode == "cloud":
            # 云端配置完整即视为可用
            return bool(self.cloud_api_url and self.cloud_api_key)
        # local：检查 Ollama 服务存活
        try:
            health = requests.get("http://localhost:11434/api/tags", timeout=5)
            return health.status_code == 200
        except requests.RequestException:
            return False

    def set_model(self, model_name):
        """动态切换AI模型，支持本地Ollama和云端模型

        Args:
            model_name: 新的模型名称

        Returns:
            bool: 切换是否成功
        """
        try:
            # 重新加载云端配置（可能已更新）
            self._load_cloud_config()

            # 验证模型是否可用
            if self._is_model_available(model_name):
                # 更新当前模型
                self.model = model_name
                log_info(f"AI模型已切换为: {model_name}")
                return True
            else:
                log_error(f"无法切换到模型 {model_name}: 模型不可用")
                return False
        except Exception as e:
            log_error(f"切换模型时出错: {str(e)}")
            return False

    def _is_model_available(self, model_name):
        """检查模型是否可用，支持本地Ollama和云端模型

        Args:
            model_name: 要检查的模型名称

        Returns:
            bool: 模型是否可用
        """
        # 如果是云端模型，测试云端连接
        if self._is_cloud_model(model_name):
            return self._test_cloud_connection()

        # 否则测试本地Ollama模型
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": "test",
                    "stream": False
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            log_warning(f"检查模型 {model_name} 可用性失败: {str(e)}")
            return False

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
        prompt = "你是一名专业的英语学习顾问，请根据以下学习数据生成详细的个性化建议，使用中文回答。\n"
        prompt += "特别关注用户的响应时间数据，分析用户在哪些单词上花费时间较长或较短，并提供针对性的建议。\n"
        prompt += "如果用户对某些单词反应很快且正确率高，可以建议减少复习频率；如果反应慢或正确率低，建议增加练习。\n"
        prompt += f"数据详情：\n{json.dumps(user_stats, ensure_ascii=False)}\n"
        prompt += "请提供3-5点具体建议，包括单词学习策略、练习方法和时间管理建议。引用部分可以使用英语。"

        # 使用同步方式调用_ask方法
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self._ask(prompt))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._ask(prompt))

        if _is_ai_unavailable(result):
            log_warning("学习建议 AI 不可用，启用本地降级")
            return self._default_advice(user_stats)
        return result


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
