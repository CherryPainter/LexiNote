"""modules/ai_service.py 白盒测试。

mock 掉 AIManager 与 ComprehensionDatabase，聚焦内部 JSON 解析与字段容错逻辑：
- 必要字段缺失返回 None
- title / explanation 缺省兜底
- 字段拼写容错（answeers / answer / explanaations）
- 题目数量与答案/解析一致性校验
- 无效选择题（占位符 'question'）拦截
- temperature 透传
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from modules import ai_service as svc
from modules.ai_service import AIService
from modules.exam_specs import GEN_TEMPERATURE


@pytest.fixture
def ai():
    with patch("modules.ai_service.AIManager") as MockAIM, \
         patch("modules.ai_service.ComprehensionDatabase") as MockDB:
        s = AIService()
        s.ai_manager = MockAIM.return_value
        s.db_manager = MockDB.return_value
        s.ai_available = True
        s.is_ai_available = lambda: True
        s._save_raw_response = MagicMock()
        s.ai_manager._ask_sync.return_value = "{}"
        s.db_manager.add_cloze_test.return_value = 1
        s.db_manager.add_reading_comprehension.return_value = 1
        return s


CLOZE_OK = json.dumps({
    "title": "测试标题",
    "content": "文章 [BLANK_1] 内容 [BLANK_2] 结束",
    "options": [
        {"blank": 1, "text": "a;b;c;d"},
        {"blank": 2, "text": "e;f;g;h"},
    ],
    "answers": "1,2",
    "explanation": "逐空解析",
})

READING_OK = json.dumps({
    "article": "这是一篇阅读文章。",
    "questions": [
        "What is x? A. a B. b C. c D. d",
        "Why y? A. x B. y C. z D. w",
    ],
    "answers": ["A", "B"],
    "explanations": ["解析1", "解析2"],
})


class TestGenerateCloze:
    def test_正常生成(self, ai):
        ai.ai_manager._ask_sync.return_value = CLOZE_OK
        ai.db_manager.add_cloze_test.return_value = 7
        res = ai.generate_cloze_test("高中", "通用")
        assert res is not None
        assert res["id"] == 7
        assert res["answer"] == "1,2"
        assert res["options"][0]["options"] == ["a", "b", "c", "d"]

    def test_ai不可用返回None(self, ai):
        ai.ai_available = False
        ai.is_ai_available = lambda: False
        assert ai.generate_cloze_test() is None

    def test_title缺省兜底(self, ai):
        data = json.loads(CLOZE_OK)
        del data["title"]
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        res = ai.generate_cloze_test("高中", "通用")
        assert res["title"] == "高中英语完形填空（通用）"

    def test_explanation缺省置空(self, ai):
        data = json.loads(CLOZE_OK)
        del data["explanation"]
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        res = ai.generate_cloze_test()
        assert res["explanation"] == ""

    def test_answeers拼写容错(self, ai):
        data = json.loads(CLOZE_OK)
        data["answeers"] = data.pop("answers")
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        res = ai.generate_cloze_test()
        assert res["answer"] == "1,2"

    def test_answer单数容错(self, ai):
        data = json.loads(CLOZE_OK)
        data["answer"] = data.pop("answers")
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        res = ai.generate_cloze_test()
        assert res["answer"] == "1,2"

    @pytest.mark.parametrize("missing", ["content", "options", "answers"])
    def test_缺必要字段返回None(self, ai, missing):
        data = json.loads(CLOZE_OK)
        del data[missing]
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        assert ai.generate_cloze_test() is None

    def test_无法解析JSON返回None(self, ai):
        ai.ai_manager._ask_sync.return_value = "这根本不是 JSON 文本"
        assert ai.generate_cloze_test() is None

    def test_带代码块标记可解析(self, ai):
        ai.ai_manager._ask_sync.return_value = "```json\n" + CLOZE_OK + "\n```"
        res = ai.generate_cloze_test()
        assert res is not None

    def test_temperature透传(self, ai):
        ai.ai_manager._ask_sync.return_value = CLOZE_OK
        ai.generate_cloze_test("高中", "通用")
        args, kwargs = ai.ai_manager._ask_sync.call_args
        assert kwargs.get("temperature") == GEN_TEMPERATURE


class TestGenerateReading:
    def test_正常生成(self, ai):
        ai.ai_manager._ask_sync.return_value = READING_OK
        ai.db_manager.add_reading_comprehension.return_value = 9
        res = ai.generate_reading_comprehension("高中", "短篇", 5, "通用")
        assert res is not None
        assert res["id"] == 9
        assert len(res["questions"]) == 2

    def test_ai不可用返回None(self, ai):
        ai.ai_available = False
        ai.is_ai_available = lambda: False
        assert ai.generate_reading_comprehension() is None

    def test_answeers容错(self, ai):
        data = json.loads(READING_OK)
        data["answeers"] = data.pop("answers")
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        res = ai.generate_reading_comprehension()
        assert res["answers"] == ["A", "B"]

    def test_explanaations容错(self, ai):
        data = json.loads(READING_OK)
        data["explanaations"] = data.pop("explanations")
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        res = ai.generate_reading_comprehension()
        assert res["explanations"] == ["解析1", "解析2"]

    @pytest.mark.parametrize("missing", ["article", "questions", "answers", "explanations"])
    def test_缺必要字段返回None(self, ai, missing):
        data = json.loads(READING_OK)
        del data[missing]
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        assert ai.generate_reading_comprehension() is None

    def test_空题目返回None(self, ai):
        data = json.loads(READING_OK)
        data["questions"] = []
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        assert ai.generate_reading_comprehension() is None

    def test_占位符question拦截(self, ai):
        data = json.loads(READING_OK)
        data["questions"] = ["question", "question"]
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        assert ai.generate_reading_comprehension() is None

    def test_题目答案数量不匹配返回None(self, ai):
        data = json.loads(READING_OK)
        data["answers"] = ["A"]
        ai.ai_manager._ask_sync.return_value = json.dumps(data)
        assert ai.generate_reading_comprehension() is None

    def test_temperature透传(self, ai):
        ai.ai_manager._ask_sync.return_value = READING_OK
        ai.generate_reading_comprehension("高中", "短篇", 5, "通用")
        args, kwargs = ai.ai_manager._ask_sync.call_args
        assert kwargs.get("temperature") == GEN_TEMPERATURE


class TestEvaluate:
    def test_完形答案全对(self, ai):
        ok, result = ai.evaluate_cloze_answer("1,2,3", "1,2,3")[:2]
        assert ok is True
        assert "3/3" in result

    def test_完形答案部分对(self, ai):
        ok, result = ai.evaluate_cloze_answer("1,2,3", "1,9,3")[:2]
        assert ok is False
        assert "2/3" in result

    def test_完形数量不匹配(self, ai):
        ok, result = ai.evaluate_cloze_answer("1,2", "1,2,3")[:2]
        assert ok is False
        assert "数量不匹配" in result

    def test_阅读选择题正确(self, ai):
        ok, result = ai.evaluate_reading_answer("A", "A")[:2]
        assert ok is True

    def test_阅读选择题错误(self, ai):
        ok, result = ai.evaluate_reading_answer("B", "A")[:2]
        assert ok is False
        assert "正确答案" in result

    def test_阅读主观题正常评估(self, ai):
        ai.ai_available = True
        ai.ai_manager._ask_sync.return_value = '{"is_acceptable": true, "score": 80, "feedback": "不错"}'
        ok, result = ai.evaluate_reading_answer("学生答案", "标准答案", question_type="主观题")[:2]
        assert ok is True
        assert "80/100" in result
        assert "不错" in result

    def test_阅读主观题AI不可用(self, ai):
        ai.ai_available = False
        ai.is_ai_available = lambda: False
        ok, result = ai.evaluate_reading_answer("x", "y", question_type="主观题")[:2]
        assert ok is False
        assert "AI服务不可用" in result

    def test_阅读主观题解析失败降级(self, ai):
        ai.ai_available = True
        ai.ai_manager._ask_sync.return_value = "不是合法JSON"
        ai._save_raw_response = MagicMock()
        ok, result = ai.evaluate_reading_answer("x", "y", question_type="主观题")[:2]
        assert ok is False
        assert result == "评估失败"
