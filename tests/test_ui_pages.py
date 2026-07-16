"""ui/cloze_test_page.py 与 ui/reading_comprehension_page.py 白盒测试。

使用 headless tkinter：构造页面实例（绕过模块懒加载的 AI 连接），
直接调用纯展示/答题逻辑方法，验证：
- 选项按空/按题渲染为 A/B/C/D 单选
- 已选答案汇总标签实时更新
- 提交时收集选择并调用模块判分、回填结果
- 未答全时给出警告且不提交
- _clear_ui 正确重置状态
- 阅读理解题干与选项解析（含 Multiple Choice 前缀）
"""
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from ui.cloze_test_page import ClozeTestPage
from ui.reading_comprehension_page import ReadingComprehensionPage


@pytest.fixture
def cloze_page(tk_root):
    ctrl = MagicMock()
    ctrl.root = tk_root
    ctrl.word_manager = MagicMock()
    page = ClozeTestPage(tk_root, ctrl)
    page.cloze_module = MagicMock()
    yield page
    page.destroy()


@pytest.fixture
def reading_page(tk_root):
    ctrl = MagicMock()
    ctrl.root = tk_root
    ctrl.word_manager = MagicMock()
    page = ReadingComprehensionPage(tk_root, ctrl)
    page.reading_module = MagicMock()
    yield page
    page.destroy()


# ---------------------------------------------------------------------------
# 完形填空页
# ---------------------------------------------------------------------------
class TestClozePage:
    def test_选项按空渲染且按blank排序(self, cloze_page):
        opts = [
            {"blank": 2, "options": ["b2", "c2", "d2", "a2"]},
            {"blank": 1, "options": ["a1", "b1", "c1", "d1"]},
        ]
        cloze_page._display_options(opts)
        assert len(cloze_page.blank_vars) == 2
        # 第 1 空对应 blank_vars[0]，选项 a1
        cloze_page.blank_vars[0].set("A")
        cloze_page.blank_vars[1].set("C")
        cloze_page._update_selected_answers_label()
        label = cloze_page.selected_answers_label.cget("text")
        assert "A" in label and "C" in label

    def test_已选答案汇总格式(self, cloze_page):
        cloze_page._display_options([
            {"blank": 1, "options": ["a", "b", "c", "d"]},
            {"blank": 2, "options": ["a", "b", "c", "d"]},
        ])
        cloze_page.blank_vars[0].set("B")
        cloze_page.blank_vars[1].set("")
        cloze_page._update_selected_answers_label()
        # 未选显示占位 _
        assert cloze_page.selected_answers_label.cget("text") == "已选答案：B,_"

    def test_提交收集选择并回填结果(self, cloze_page):
        cloze_page._display_options([
            {"blank": 1, "options": ["a", "b", "c", "d"]},
            {"blank": 2, "options": ["a", "b", "c", "d"]},
        ])
        cloze_page.blank_vars[0].set("A")
        cloze_page.blank_vars[1].set("B")
        cloze_page.cloze_module.submit_answer.return_value = (True, "正确率 2/2", "逐空解析内容")
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"):
            cloze_page._submit_answer()
        # 收集的答案以逗号拼接
        args = cloze_page.cloze_module.submit_answer.call_args.args
        assert args[0] == "A,B"
        # 结果回填到文本框
        text = cloze_page.result_text.get("1.0", tk.END)
        assert "正确率 2/2" in text
        assert "逐空解析内容" in text

    def test_未答全不提交(self, cloze_page):
        cloze_page._display_options([
            {"blank": 1, "options": ["a", "b", "c", "d"]},
            {"blank": 2, "options": ["a", "b", "c", "d"]},
        ])
        cloze_page.blank_vars[0].set("A")
        cloze_page.blank_vars[1].set("")  # 第二空未选
        with patch("tkinter.messagebox.showwarning") as warn:
            cloze_page._submit_answer()
        warn.assert_called_once()
        cloze_page.cloze_module.submit_answer.assert_not_called()

    def test_clear_ui重置(self, cloze_page):
        cloze_page._display_options([
            {"blank": 1, "options": ["a", "b", "c", "d"]},
        ])
        cloze_page.blank_vars[0].set("A")
        cloze_page._clear_ui()
        assert cloze_page.blank_vars == []
        assert cloze_page.selected_answers_label.cget("text") == "已选答案："
        assert cloze_page.submit_button.cget("state") == tk.DISABLED

    def test_更新状态(self, cloze_page):
        cloze_page.cloze_module.get_test_statistics.return_value = {
            "current_mode": "online", "ai_available": True, "total_tests": 5
        }
        cloze_page._update_status()
        txt = cloze_page.status_var.get()
        assert "online" in txt and "5" in txt

    def test_删除无当前题目(self, cloze_page):
        cloze_page.current_test_id = None
        with patch("tkinter.messagebox.showwarning") as w:
            cloze_page._on_delete_question()
        w.assert_called_once()

    def test_删除成功(self, cloze_page):
        cloze_page.current_test_id = 7
        with patch("modules.database.ComprehensionDatabase") as D, \
             patch("tkinter.messagebox.askyesno", return_value=True), \
             patch("tkinter.messagebox.showinfo") as info:
            D.return_value.delete_cloze_test.return_value = True
            cloze_page._on_delete_question()
        D.return_value.delete_cloze_test.assert_called_with(7)
        info.assert_called_once()


# ---------------------------------------------------------------------------
# 阅读理解页
# ---------------------------------------------------------------------------
class TestReadingPage:
    def test_题干选项解析_常规(self, reading_page):
        stem, options = reading_page._extract_options(
            "Why did he go? A. because B. but C. so D. though"
        )
        assert stem == "Why did he go?"
        assert options[0] == ("A", "because")
        assert options[3] == ("D", "though")

    def test_题干选项解析_去MultipleChoice前缀(self, reading_page):
        stem, options = reading_page._extract_options(
            "Multiple Choice: What is the main idea? A. a B. b C. c D. d"
        )
        assert stem == "What is the main idea?"
        assert len(options) == 4

    def test_题干选项解析_结尾空格(self, reading_page):
        stem, options = reading_page._extract_options(
            "Choose. A. x   B. y   C. z   D. w   "
        )
        assert options[1] == ("B", "y")

    def test_题目渲染与汇总(self, reading_page):
        qs = [
            "Q1? A. a B. b C. c D. d",
            "Q2? A. x B. y C. z D. w",
        ]
        reading_page._display_questions(qs)
        assert len(reading_page.question_vars) == 2
        assert len(reading_page.question_result_labels) == 2
        reading_page.question_vars[0].set("A")
        reading_page.question_vars[1].set("")
        reading_page._update_selected_answers_label()
        assert reading_page.selected_answers_label.cget("text") == "已选答案：A,_"

    def test_提交收集并判分(self, reading_page):
        qs = ["Q1? A. a B. b C. c D. d", "Q2? A. x B. y C. z D. w"]
        reading_page._display_questions(qs)
        reading_page.question_vars[0].set("A")
        reading_page.question_vars[1].set("B")
        results = [
            {"is_correct": True, "explanation": "解析一"},
            {"is_correct": False, "explanation": "解析二"},
        ]
        reading_page.reading_module.submit_all_answers.return_value = (50.0, results)
        with patch("tkinter.messagebox.showinfo") as info:
            reading_page._submit_answer()
        # 提交时收集到 [A, B]
        assert reading_page.reading_module.submit_all_answers.call_args.args[0] == ["A", "B"]
        # 结果标签回填
        assert "✓" in reading_page.question_result_labels[0].cget("text")
        assert "✗" in reading_page.question_result_labels[1].cget("text")
        # 总分弹窗
        assert info.called
        assert reading_page.submit_button.cget("state") == tk.DISABLED

    def test_未答全不提交(self, reading_page):
        qs = ["Q1? A. a B. b C. c D. d", "Q2? A. x B. y C. z D. w"]
        reading_page._display_questions(qs)
        reading_page.question_vars[0].set("A")
        reading_page.question_vars[1].set("")
        with patch("tkinter.messagebox.showwarning") as warn:
            reading_page._submit_answer()
        warn.assert_called_once()
        reading_page.reading_module.submit_all_answers.assert_not_called()

    def test_clear_ui重置(self, reading_page):
        qs = ["Q1? A. a B. b C. c D. d"]
        reading_page._display_questions(qs)
        reading_page.question_vars[0].set("A")
        reading_page._clear_ui()
        assert reading_page.question_vars == []
        assert reading_page.selected_answers_label.cget("text") == "已选答案："
        assert reading_page.submit_button.cget("state") == tk.DISABLED

    def test_更新状态(self, reading_page):
        reading_page.reading_module.get_test_statistics.return_value = {
            "current_mode": "offline", "ai_available": False, "total_tests": 3
        }
        reading_page._update_status()
        txt = reading_page.status_var.get()
        assert "offline" in txt and "3" in txt

    def test_显示页延迟初始化(self, reading_page):
        reading_page.reading_module = None
        with patch("modules.reading_comprehension.ReadingComprehensionModule") as M:
            reading_page._on_show_page()
            M.assert_called_once()
            assert reading_page.reading_module is not None
        # 已初始化时不重复创建
        with patch("modules.reading_comprehension.ReadingComprehensionModule") as M2:
            reading_page._on_show_page()
            M2.assert_not_called()

    def test_删除成功(self, reading_page):
        reading_page.current_test_id = 9
        with patch("modules.database.ComprehensionDatabase") as D, \
             patch("tkinter.messagebox.askyesno", return_value=True), \
             patch("tkinter.messagebox.showinfo") as info:
            D.return_value.delete_reading_comprehension.return_value = True
            reading_page._on_delete_question()
        D.return_value.delete_reading_comprehension.assert_called_with(9)
        info.assert_called_once()
