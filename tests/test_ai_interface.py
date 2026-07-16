"""core/ai_interface.py 白盒测试。

通过 AIManager.__new__ 绕过 __init__，手动注入被 mock 的依赖，
针对内部逻辑分支做精细断言：URL 归一化、请求重试、ai_mode 门控、
流式 chunk 为 null 的健壮性、本地降级、哨兵返回、temperature 透传等。
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import ai_interface as ai_mod
from core.ai_interface import AIManager, _is_ai_unavailable, _normalize_cloud_url


def make_aim(ai_mode="off", cloud_api_url="", cloud_api_key="", cloud_model_name=""):
    aim = AIManager.__new__(AIManager)
    sm = MagicMock()
    cfg = {
        "cloud_ai_api_url": cloud_api_url,
        "cloud_ai_api_key": cloud_api_key,
        "cloud_ai_model_name": cloud_model_name,
        "cloud_ai_enabled": bool(cloud_api_url and cloud_api_key),
    }
    sm.get_setting.side_effect = lambda k, d=None: cfg.get(k, d)
    sm.get_ai_mode.return_value = ai_mode
    aim.settings_manager = sm
    aim.db_manager = MagicMock()
    aim.ai_mode = ai_mode
    aim.cloud_api_url = cloud_api_url
    aim.cloud_api_key = cloud_api_key
    aim.cloud_model_name = cloud_model_name
    aim.cloud_enabled = bool(cloud_api_url and cloud_api_key)
    aim.model = cloud_model_name or "local-model"
    return aim


class TestPureFunctions:
    @pytest.mark.parametrize("raw,expected", [
        ("ws-abc.cn-beijing.aliyun.com", "https://ws-abc.cn-beijing.aliyun.com"),
        ("https://x.com", "https://x.com"),
        ("http://x.com", "http://x.com"),
        ("", ""),
        ("  ws-x.com  ", "https://ws-x.com"),
    ])
    def test_normalize_cloud_url(self, raw, expected):
        assert _normalize_cloud_url(raw) == expected

    @pytest.mark.parametrize("text,exp", [
        ("AI功能暂不可用: xxx", True),
        ("AI功能暂不可用", True),
        ("正常结果", False),
        ("", False),
        (None, False),
    ])
    def test_is_ai_unavailable(self, text, exp):
        assert _is_ai_unavailable(text) is exp


class TestIsAiAvailable:
    def test_off模式恒为False(self):
        aim = make_aim(ai_mode="off")
        assert aim.is_ai_available() is False

    def test_cloud配置完整为True(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        assert aim.is_ai_available() is True

    def test_cloud缺少key为False(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="", cloud_model_name="m")
        assert aim.is_ai_available() is False

    def test_local_ollama存活为True(self):
        aim = make_aim(ai_mode="local")
        with patch.object(ai_mod.requests, "get", return_value=MagicMock(status_code=200)):
            assert aim.is_ai_available() is True

    def test_local_ollama异常为False(self):
        aim = make_aim(ai_mode="local")
        with patch.object(ai_mod.requests, "get", side_effect=ai_mod.requests.RequestException("conn")):
            assert aim.is_ai_available() is False

    def test_local_ollama非200为False(self):
        aim = make_aim(ai_mode="local")
        with patch.object(ai_mod.requests, "get", return_value=MagicMock(status_code=500)):
            assert aim.is_ai_available() is False


class TestGetAvailableModels:
    def test_off返回空(self):
        aim = make_aim(ai_mode="off")
        assert aim._get_available_models() == []

    def test_local探测ollama(self):
        aim = make_aim(ai_mode="local")
        with patch.object(ai_mod.requests, "get",
                          return_value=MagicMock(status_code=200,
                                                 json=lambda: {"models": [{"name": "qwen"}, {"name": "llama"}]})):
            assert aim._get_available_models() == ["qwen", "llama"]

    def test_cloud仅登记模型名(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="my-model")
        assert aim._get_available_models() == ["my-model"]


class TestSafePost:
    def test_成功直接返回(self):
        aim = make_aim()
        resp = MagicMock()
        with patch.object(ai_mod.requests, "post", return_value=resp) as m:
            out = aim._safe_post("http://x", {}, {}, (10, 60))
            assert out is resp
            assert m.call_count == 1
            assert m.call_args.kwargs["timeout"] == (10, 60)

    def test_网络异常重试后成功(self):
        aim = make_aim()
        resp = MagicMock()
        side = [ai_mod.requests.RequestException("boom"), ai_mod.requests.RequestException("boom2"), resp]
        with patch.object(ai_mod.requests, "post", side_effect=side) as m, \
             patch.object(ai_mod.time, "sleep") as ms:
            out = aim._safe_post("http://x", {}, {}, (10, 60))
            assert out is resp
            assert m.call_count == 3
            assert ms.call_count == 2

    def test_始终失败抛最后异常(self):
        aim = make_aim()
        side = [ai_mod.requests.RequestException("e1"), ai_mod.requests.RequestException("e2"), ai_mod.requests.RequestException("e3")]
        with patch.object(ai_mod.requests, "post", side_effect=side), \
             patch.object(ai_mod.time, "sleep"):
            with pytest.raises(ai_mod.requests.RequestException):
                aim._safe_post("http://x", {}, {}, (10, 60), max_retries=2)


class TestAskSync:
    def test_off模式返回哨兵(self):
        aim = make_aim(ai_mode="off")
        out = aim._ask_sync("prompt")
        assert out.startswith("AI功能暂不可用")
        assert out == "AI功能暂不可用: AI 功能未启用"

    def test_cloud走云端通道(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        with patch.object(aim, "_ask_cloud_sync", return_value="cloud-ok") as m:
            assert aim._ask_sync("prompt", temperature=0.5) == "cloud-ok"
            m.assert_called_once()
            assert m.call_args.args[0] == "prompt"
            assert m.call_args.args[2] == 0.5

    def test_local走本地通道(self):
        aim = make_aim(ai_mode="local")
        with patch.object(aim, "_ask_ollama_sync", return_value="ollama-ok") as m:
            assert aim._ask_sync("prompt") == "ollama-ok"
            m.assert_called_once()


class _FakeResp:
    def __init__(self, lines=None, json_data=None, status=200):
        self._lines = lines or []
        self._json = json_data
        self.status_code = status

    def iter_lines(self):
        return iter(self._lines)

    def json(self):
        return self._json


class TestAskCloudSync:
    def test_非流式返回content(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        resp = _FakeResp(json_data={"choices": [{"message": {"content": "你好"}}]})
        with patch.object(ai_mod.requests, "post", return_value=resp) as m:
            out = aim._ask_cloud_sync("prompt")
            assert out == "你好"
            # temperature 为 None 时不写入请求体
            assert "temperature" not in m.call_args.kwargs["json"]

    def test_temperature透传(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        captured = {}
        def fake_post(url, headers=None, json=None, timeout=None, stream=False):
            captured["json"] = json
            return _FakeResp(json_data={"choices": [{"message": {"content": "x"}}]})
        with patch.object(ai_mod.requests, "post", side_effect=fake_post):
            aim._ask_cloud_sync("prompt", temperature=0.7)
            assert captured["json"]["temperature"] == 0.7

    def test_流式content为null不报错(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        lines = [
            b'data: {"choices":[{"delta":{"content":"Hello "}}]}',
            b'data: {"choices":[{"delta":{"content":null}}]}',
            b'data: {"choices":[{"delta":{}}]}',
            b'data: {"choices":[{"delta":{"content":"World"}}]}',
            b'data: [DONE]',
        ]
        resp = _FakeResp(lines=lines)
        chunks = []
        with patch.object(ai_mod.requests, "post", return_value=resp):
            out = aim._ask_cloud_sync("prompt", callback=lambda c, d: chunks.append(c))
        assert out == "Hello World"
        assert "".join(chunks) == "Hello World"

    def test_非200返回哨兵(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        resp = _FakeResp(status=401)
        with patch.object(ai_mod.requests, "post", return_value=resp):
            out = aim._ask_cloud_sync("prompt")
            assert out.startswith("AI功能暂不可用")


class TestAskOllamaSync:
    def test_健康检查失败返回哨兵(self):
        aim = make_aim(ai_mode="local")
        with patch.object(ai_mod.requests, "get", return_value=MagicMock(status_code=503)):
            out = aim._ask_ollama_sync("prompt")
            assert out.startswith("AI功能暂不可用")

    def test_成功流式且null安全(self):
        aim = make_aim(ai_mode="local")
        ollama_lines = [
            b'{"response":"The ","done":false}',
            b'{"response":null,"done":false}',
            b'{"response":"cat sat.","done":true}',
        ]
        health = MagicMock(status_code=200)
        gen = _FakeResp(lines=ollama_lines)
        chunks = []
        with patch.object(ai_mod.requests, "get", return_value=health), \
             patch.object(aim, "_safe_post", return_value=gen) as m:
            out = aim._ask_ollama_sync("prompt", callback=lambda c, d: chunks.append(c))
            assert out == "The cat sat."
            assert "".join(chunks) == "The cat sat."
            # temperature 为 None 时不写入请求体
            assert "temperature" not in m.call_args.kwargs["data"]

    def test_temperature透传(self):
        aim = make_aim(ai_mode="local")
        captured = {}
        def fake_safe(url, headers=None, data=None, timeout=None, stream=False):
            captured["data"] = data
            return _FakeResp(lines=[b'{"response":"ok","done":true}'])
        with patch.object(ai_mod.requests, "get", return_value=MagicMock(status_code=200)), \
             patch.object(aim, "_safe_post", side_effect=fake_safe):
            aim._ask_ollama_sync("prompt", temperature=0.3)
            assert captured["data"]["temperature"] == 0.3


class TestLocalFallback:
    def test_local_translate_命中词典(self, tmp_path):
        aim = make_aim()
        import json
        aim._local_dict = {"apple": "苹果", "run": "跑"}
        assert aim._local_translate("apple", "en2zh") == "苹果"

    def test_local_translate_未命中返回离线前缀(self):
        aim = make_aim()
        aim._local_dict = {}
        assert "离线翻译不可用" in aim._local_translate("zzz", "en2zh")
        assert "离线翻译不可用" in aim._local_translate("zzz", "zh2en")

    def test_local_word_details(self):
        aim = make_aim()
        aim._local_dict = {"book": "书"}
        import json
        obj = json.loads(aim._local_word_details("book"))
        assert obj["meaning_zh"] == ["书"]
        assert obj["phonetic"] == ""

    def test_local_example(self):
        aim = make_aim()
        out = aim._local_example("happy")
        assert "happy" in out and "离线" in out

    def test_default_advice_高掌握率(self):
        aim = make_aim()
        out = aim._default_advice({"mastered": 80, "review_needed": 5, "total_words": 100})
        assert "良好" in out

    def test_default_advice_中等(self):
        aim = make_aim()
        out = aim._default_advice({"mastered": 50, "review_needed": 10, "total_words": 100})
        assert "中等" in out

    def test_default_advice_低掌握率(self):
        aim = make_aim()
        out = aim._default_advice({"mastered": 10, "review_needed": 30, "total_words": 100})
        assert "偏低" in out

    def test_default_advice_total为0不崩溃(self):
        aim = make_aim()
        out = aim._default_advice({"mastered": 0, "review_needed": 0, "total_words": 0})
        assert isinstance(out, str) and len(out) > 0


class TestEvaluate:
    def test_正常解析JSON(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value='{"is_correct": true, "similarity": 0.9, "error_type": "none", "feedback": "good"}')
        res = asyncio.run(aim.evaluate("apple", "apple"))
        assert res["is_correct"] is True
        assert res["feedback"] == "good"

    def test_非JSON回退到字符串比较(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="无法解析的内容")
        res = asyncio.run(aim.evaluate("Apple", "apple"))
        assert res["is_correct"] is True

    def test_大小写不一致判错(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="no json")
        res = asyncio.run(aim.evaluate("apple", "banana"))
        assert res["is_correct"] is False


class TestAIEnhancedMethods:
    def test_advise哨兵降级(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="AI功能暂不可用: 关闭")
        out = aim.advise({"mastered": 10, "review_needed": 5, "total_words": 100})
        assert "掌握率" in out

    def test_advise透传(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="个性化建议文本")
        assert aim.advise({}) == "个性化建议文本"

    def test_translate哨兵降级(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="AI功能暂不可用: 关闭")
        out = asyncio.run(aim.translate("apple"))
        assert "离线翻译不可用" in out

    def test_translate透传(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="苹果")
        assert asyncio.run(aim.translate("apple")) == "苹果"

    def test_example哨兵降级(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="AI功能暂不可用: 关闭")
        out = asyncio.run(aim.example("cat"))
        assert "离线模式" in out

    def test_get_word_details哨兵降级(self):
        aim = make_aim()
        aim._ask = AsyncMock(return_value="AI功能暂不可用: 关闭")
        out = asyncio.run(aim.get_word_details("dog"))
        import json
        obj = json.loads(out)
        assert obj["meaning_zh"] == [""]


class TestConnectionAndMisc:
    def test_use_cloud_provider完整为True(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        assert aim._use_cloud_provider() is True

    def test_use_cloud_provider缺key为False(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="", cloud_model_name="m")
        assert aim._use_cloud_provider() is False

    def test_test_cloud_connection成功(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        with patch.object(ai_mod.requests, "post", return_value=MagicMock(status_code=200)):
            assert aim._test_cloud_connection() is True

    def test_test_cloud_connection非200(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        with patch.object(ai_mod.requests, "post", return_value=MagicMock(status_code=500)):
            assert aim._test_cloud_connection() is False

    def test_test_cloud_connection异常(self):
        aim = make_aim(ai_mode="cloud", cloud_api_url="https://x", cloud_api_key="k", cloud_model_name="m")
        with patch.object(ai_mod.requests, "post", side_effect=Exception("net")):
            assert aim._test_cloud_connection() is False

    def test_get_usage_stats(self):
        aim = make_aim()
        aim.db_manager.execute_read.side_effect = [
            [{"count": 10}],
            [{"count": 4}],
        ]
        stats = aim.get_usage_stats()
        assert stats["cache_count"] == 10
        assert stats["used_cache_count"] == 4
        assert abs(stats["hit_rate"] - 0.4) < 1e-9
