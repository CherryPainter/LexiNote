"""modules/cloze_test.py 与 modules/reading_comprehension.py 命题/流程白盒测试。

通过把 ComprehensionDatabase 与 AIService 在模块内打桩，验证完形/阅读两个模块
的模式切换、题目加载与规范化、答题评估、计分、统计、按 ID 获取与删除等逻辑，
不依赖真实数据库与真实 AI。
"""
from unittest.mock import MagicMock, patch

import pytest

import modules.cloze_test as cloze_mod
import modules.reading_comprehension as reading_mod
from modules.cloze_test import ClozeTestModule
from modules.reading_comprehension import ReadingComprehensionModule


def _make_cloze(ai_available, db_mock=None, ai_mock=None):
    wm = MagicMock()
    wm.ai_available = ai_available
    with patch.object(cloze_mod, "ComprehensionDatabase", return_value=db_mock or MagicMock()), \
         patch.object(cloze_mod, "AIService", return_value=ai_mock or MagicMock()):
        return ClozeTestModule(wm), wm


def _make_reading(ai_available, db_mock=None, ai_mock=None):
    wm = MagicMock()
    wm.ai_available = ai_available
    with patch.object(reading_mod, "ComprehensionDatabase", return_value=db_mock or MagicMock()), \
         patch.object(reading_mod, "AIService", return_value=ai_mock or MagicMock()):
        return ReadingComprehensionModule(wm), wm


class TestClozeFlow:
    def test_模式_在线(self):
        mod, _ = _make_cloze(ai_available=True)
        assert mod.get_mode() == "online"

    def test_模式_离线(self):
        mod, _ = _make_cloze(ai_available=False)
        assert mod.get_mode() == "offline"

    def test_在线生成成功(self):
        ai = MagicMock()
        ai.generate_cloze_test.return_value = {
            "title": "测试", "content": "正文", "answer": ["A"],
            "options": [{"blank": 1, "options": ["A", "B", "C", "D"]}],
            "explanation": "解析"
        }
        mod, _ = _make_cloze(ai_available=True, ai_mock=ai)
        disp = mod.start_new_test(mode="online", level="高中", topic="通用")
        assert disp["content"] == "正文"
        assert disp["options"][0]["options"] == ["A", "B", "C", "D"]

    def test_在线生成失败返回None(self):
        ai = MagicMock()
        ai.generate_cloze_test.return_value = None
        mod, _ = _make_cloze(ai_available=True, ai_mock=ai)
        assert mod.start_new_test(mode="online") is None

    def test_离线空库返回None(self):
        db = MagicMock()
        db.count_cloze_tests.return_value = 0
        mod, _ = _make_cloze(ai_available=False, db_mock=db)
        assert mod.start_new_test(mode="offline") is None

    def test_离线加载并规范化选项(self):
        db = MagicMock()
        db.count_cloze_tests.return_value = 1
        db.get_cloze_test.return_value = {
            "id": 7, "title": "T", "content": "C",
            "answers": ["B"],
            # 旧格式：选项以 'text' 字段存分号分隔字符串
            "options": [{"blank": 1, "text": "A;B;C;D"}],
            "explanation": "E"
        }
        mod, _ = _make_cloze(ai_available=False, db_mock=db)
        disp = mod.start_new_test(mode="offline")
        # answer 从 answers 兼容而来
        assert mod.current_test["answer"] == ["B"]
        # text 分号串被规范为列表
        assert disp["options"][0]["options"] == ["A", "B", "C", "D"]

    def test_提交答案正确与否(self):
        ai = MagicMock()
        ai.generate_cloze_test.return_value = {
            "answer": "A", "explanation": "解析", "content": "c",
            "options": [{"blank": 1, "options": ["A", "B"]}]
        }
        ai.evaluate_cloze_answer.side_effect = lambda ua, ca: (ua == ca, "评测")
        mod, _ = _make_cloze(ai_available=True, ai_mock=ai)
        mod.start_new_test(mode="online")
        ok, _, _ = mod.submit_answer("A")
        assert ok is True
        bad, _, _ = mod.submit_answer("B")
        assert bad is False

    def test_无进行中题目提交(self):
        mod, _ = _make_cloze(ai_available=False)
        assert mod.submit_answer("A") == (False, "没有正在进行的练习", "")

    def test_答案格式化(self):
        mod, _ = _make_cloze(ai_available=True)
        out = mod.format_answer_for_display("A, B ,C")
        assert "第1题: A" in out and "第3题: C" in out

    def test_删除与按id获取(self):
        db = MagicMock()
        db.get_cloze_test.return_value = {"id": 3, "content": "x", "options": [], "questions": []}
        db.delete_cloze_test.return_value = True
        mod, _ = _make_cloze(ai_available=False, db_mock=db)
        assert mod.delete_test(3) is True
        disp = mod.get_test_by_id(3)
        assert disp["id"] == 3

    def test_统计信息(self):
        db = MagicMock()
        db.count_cloze_tests.return_value = 5
        mod, _ = _make_cloze(ai_available=True, db_mock=db)
        stats = mod.get_test_statistics()
        assert stats["total_tests"] == 5
        assert stats["ai_available"] is True


class TestReadingFlow:
    def test_模式_在线(self):
        mod, _ = _make_reading(ai_available=True)
        assert mod.get_mode() == "online"

    def test_在线重试后成功(self):
        ai = MagicMock()
        good = {"article": "文章", "questions": ["1. Q A. x B. y"],
                "answers": ["A"], "explanations": ["e"]}
        ai.generate_reading_comprehension.side_effect = [None, None, good]
        mod, _ = _make_reading(ai_available=True, ai_mock=ai)
        disp = mod.start_new_test(mode="online")
        assert disp["article"] == "文章"
        assert disp["total_questions"] == 1

    def test_在线失败且离线无题返回None(self):
        ai = MagicMock()
        ai.generate_reading_comprehension.return_value = None
        db = MagicMock()
        db.count_reading_comprehensions.return_value = 0
        mod, _ = _make_reading(ai_available=True, db_mock=db, ai_mock=ai)
        assert mod.start_new_test(mode="online") is None

    def test_离线加载(self):
        db = MagicMock()
        db.count_reading_comprehensions.return_value = 1
        db.get_reading_comprehension.return_value = {
            "id": 9, "article": "A", "questions": ["q"], "answers": ["a"],
            "explanations": ["e"]
        }
        mod, _ = _make_reading(ai_available=False, db_mock=db)
        disp = mod.start_new_test(mode="offline")
        assert disp["article"] == "A"

    def test_提交单题(self):
        ai = MagicMock()
        ai.generate_reading_comprehension.return_value = {
            "article": "a", "questions": ["1. Q A. x B. y"],
            "answers": ["A"], "explanations": ["e"]
        }
        ai.evaluate_reading_answer.side_effect = lambda ua, ca, qt: (ua == ca, "ok")
        mod, _ = _make_reading(ai_available=True, ai_mock=ai)
        mod.start_new_test(mode="online")
        ok, _, _ = mod.submit_question_answer(0, "A")
        assert ok is True

    def test_提交全部计分(self):
        ai = MagicMock()
        ai.generate_reading_comprehension.return_value = {
            "article": "a",
            "questions": ["1. Q A. x B. y", "2. Q A. m B. n"],
            "answers": ["A", "B"], "explanations": ["e", "e"]
        }
        ai.evaluate_reading_answer.side_effect = lambda ua, ca, qt: (ua == ca, "ok")
        mod, _ = _make_reading(ai_available=True, ai_mock=ai)
        mod.start_new_test(mode="online")
        score_all, results = mod.submit_all_answers(["A", "B"])
        assert score_all == 100.0
        score_half, _ = mod.submit_all_answers(["A", "X"])
        assert score_half == 50.0

    def test_选择题判定(self):
        ai = MagicMock()
        ai.generate_reading_comprehension.return_value = {
            "article": "a",
            "questions": ["1. 细节 A. x B. y", "2. 主观题：谈谈你的看法"],
            "answers": ["A", "开放"], "explanations": ["e", "e"]
        }
        mod, _ = _make_reading(ai_available=True, ai_mock=ai)
        mod.start_new_test(mode="online")
        assert mod.is_question_multiple_choice(0) is True
        assert mod.is_question_multiple_choice(1) is False

    def test_无进行中提交全部(self):
        mod, _ = _make_reading(ai_available=False)
        assert mod.submit_all_answers(["A"]) == (0.0, [])
