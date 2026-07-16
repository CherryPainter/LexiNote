"""ui/learning_page.py 白盒测试。

使用 headless tkinter：用 MagicMock 构造 word_manager / learning_manager /
settings_manager；直接调用纯展示/答题逻辑方法，验证：
- _show_current_word 依据单词 dict / 字符串分别取释义与音标
- _update_progress 进度文本聚合
- _enable_buttons / _disable_buttons 按钮状态切换
- mark_mastered / mark_review 写入学习管理并推进到下个单词
- _move_to_next_word 索引推进
- _handle_left/right/return_key 键盘事件路由
- toggle_example / _on_example_fetched 例句显示状态
- start_learning 恢复/新建批次
- _finish_batch 完成与界面重置
"""
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from ui.learning_page import LearningPage


def _make_managers():
    wm = MagicMock()
    wm.get_translation.return_value = "苹果"
    lm = MagicMock()
    lm.get_current_stats.return_value = {
        "batch": {"mastered": 2, "review": 1, "total": 5},
        "summary": {
            "total_words": 100,
            "learned_words": 50,
            "overall_accuracy": 0.5,
            "today_practices": 3,
        },
    }
    sm = MagicMock()
    # 默认所有开关为 False，使 mark 类方法走“立即下一个”分支
    sm.get_setting.side_effect = lambda key, default=None: False
    return wm, lm, sm


@pytest.fixture
def learning_page(tk_root):
    wm, lm, sm = _make_managers()
    page = LearningPage(tk_root, wm, lm, sm)
    # 让 master.after 立即执行，便于断言例句 UI 同步更新
    page.master = MagicMock()
    page.master.after = lambda ms, func: func()
    yield page
    page.destroy()


# ---------------------------------------------------------------------------
# 单词展示
# ---------------------------------------------------------------------------
class TestShowCurrentWord:
    def test_字典格式单词显示释义与音标(self, learning_page):
        learning_page.current_batch = [{"word": "apple", "phonetic": "/ˈæp.l/"}]
        learning_page.current_index = 0
        learning_page._show_current_word()
        assert learning_page.word_label.cget("text") == "apple"
        assert learning_page.definition_label.cget("text") == "苹果"
        assert learning_page.phonetic_label.cget("text") == "/ˈæp.l/"

    def test_无音标时隐藏音标(self, learning_page):
        learning_page.current_batch = [{"word": "apple", "phonetic": ""}]
        learning_page.current_index = 0
        learning_page._show_current_word()
        assert learning_page.phonetic_label.cget("text") == ""
        assert learning_page.phonetic_label.winfo_manager() == ""

    def test_字符串格式单词经learning_manager取释义(self, learning_page):
        learning_page.current_batch = ["banana"]
        learning_page.current_index = 0
        learning_page.learning_manager.get_word_definition.return_value = "香蕉"
        learning_page._show_current_word()
        assert learning_page.word_label.cget("text") == "banana"
        assert learning_page.definition_label.cget("text") == "香蕉"


# ---------------------------------------------------------------------------
# 进度与按钮状态
# ---------------------------------------------------------------------------
class TestProgressAndButtons:
    def test_进度文本聚合(self, learning_page):
        learning_page.current_batch = [{"word": "a"}, {"word": "b"}]
        learning_page.current_index = 0
        learning_page._update_progress()
        txt = learning_page.progress_label.cget("text")
        assert "进度: 1/2" in txt
        assert "掌握: 2" in txt
        assert "需复习: 1" in txt

    def test_启用按钮(self, learning_page):
        learning_page._enable_buttons()
        assert learning_page.pronounce_button.cget("state") == tk.NORMAL
        assert learning_page.review_button.cget("state") == tk.NORMAL
        assert learning_page.mastered_button.cget("state") == tk.NORMAL

    def test_禁用按钮(self, learning_page):
        learning_page._disable_buttons()
        assert learning_page.pronounce_button.cget("state") == tk.DISABLED
        assert learning_page.review_button.cget("state") == tk.DISABLED
        assert learning_page.mastered_button.cget("state") == tk.DISABLED


# ---------------------------------------------------------------------------
# 标记掌握 / 需复习 / 推进
# ---------------------------------------------------------------------------
class TestMarkAndMove:
    def test_标记已掌握写入并推进(self, learning_page):
        learning_page.current_batch = [{"word": "apple"}, {"word": "banana"}]
        learning_page.current_index = 0
        learning_page.current_word = {"word": "apple"}
        learning_page.mark_mastered()
        learning_page.learning_manager.mark_mastered.assert_called_once_with("apple")
        # 自动下一个关闭 -> 立即推进
        assert learning_page.current_index == 1
        learning_page.learning_manager.save_progress.assert_called()

    def test_标记需复习写入并推进(self, learning_page):
        learning_page.current_batch = [{"word": "apple"}, {"word": "banana"}]
        learning_page.current_index = 0
        learning_page.current_word = {"word": "apple"}
        learning_page.mark_review()
        learning_page.learning_manager.mark_review.assert_called_once_with("apple")
        assert learning_page.current_index == 1

    def test_移动到下一个单词(self, learning_page):
        learning_page.current_batch = [{"word": "apple"}, {"word": "banana"}]
        learning_page.current_index = 0
        learning_page._move_to_next_word()
        assert learning_page.current_index == 1


# ---------------------------------------------------------------------------
# 键盘事件路由
# ---------------------------------------------------------------------------
class TestKeyEvents:
    def test_左方向键触发需复习(self, learning_page):
        learning_page.current_batch = [{"word": "apple"}, {"word": "banana"}]
        learning_page.current_index = 0
        learning_page.current_word = {"word": "apple"}
        event = MagicMock()
        event.widget = tk_root_dummy()
        learning_page._handle_left_key(event)
        learning_page.learning_manager.mark_review.assert_called_once_with("apple")

    def test_右方向键触发已掌握(self, learning_page):
        learning_page.current_batch = [{"word": "apple"}, {"word": "banana"}]
        learning_page.current_index = 0
        learning_page.current_word = {"word": "apple"}
        event = MagicMock()
        event.widget = tk_root_dummy()
        learning_page._handle_right_key(event)
        learning_page.learning_manager.mark_mastered.assert_called_once_with("apple")

    def test_输入框聚焦时不响应键盘(self, learning_page):
        learning_page.current_word = {"word": "apple"}
        event = MagicMock()
        event.widget = tk.Entry(learning_page)  # 输入框 -> 不应触发
        learning_page._handle_left_key(event)
        learning_page.learning_manager.mark_review.assert_not_called()


# ---------------------------------------------------------------------------
# 例句显示
# ---------------------------------------------------------------------------
class TestExample:
    def test_已缓存例句直接显示(self, learning_page):
        learning_page.current_word = {"word": "apple"}
        learning_page.current_example = "An apple a day."
        learning_page.toggle_example()
        assert learning_page.is_example_visible is True
        assert learning_page.example_label.cget("text") == "An apple a day."
        assert learning_page.example_button.cget("text") == "📝 隐藏例句"

    def test_无单词时不显示例句(self, learning_page):
        learning_page.current_word = None
        learning_page.toggle_example()
        assert learning_page.is_example_visible is False

    def test_例句回调更新可见标签(self, learning_page):
        learning_page.current_word = {"word": "apple"}
        learning_page.is_example_visible = True
        learning_page._on_example_fetched("Fetched example.")
        assert learning_page.current_example == "Fetched example."
        assert learning_page.example_label.cget("text") == "Fetched example."


# ---------------------------------------------------------------------------
# 开始学习与完成批次
# ---------------------------------------------------------------------------
class TestStartAndFinish:
    def test_无法恢复进度时新建批次(self, learning_page):
        learning_page.learning_manager.load_daily_progress.return_value = False
        learning_page.word_manager.get_active_word_set.return_value = {"name": "CET4"}
        learning_page.learning_manager.get_batch.return_value = [{"word": "apple"}]
        learning_page.start_learning()
        assert learning_page.current_batch == [{"word": "apple"}]
        assert learning_page.current_index == 0

    def test_完成批次后重置界面(self, learning_page):
        learning_page.learning_manager.save_progress.return_value = True
        learning_page.current_batch = [{"word": "apple"}]
        learning_page.current_index = 1
        with patch("ui.learning_page.messagebox.showinfo"):
            learning_page._finish_batch()
        assert learning_page.current_batch == []
        assert learning_page.current_index == -1
        assert learning_page.word_label.cget("text") == "请点击开始学习"


def tk_root_dummy():
    """返回一个非 Entry / 非 Combobox 的控件，用于模拟“焦点不在输入框”。

    直接用 tk.Tk 之外的简单对象即可——只要不是 tk.Entry/ttk.Combobox 实例。
    """
    return object()
