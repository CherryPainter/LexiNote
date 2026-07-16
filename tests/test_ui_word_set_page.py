"""ui/word_set_page.py 白盒测试。

使用 headless tkinter：用 MagicMock 构造 word_manager，注入具体返回值驱动
各项列表/分页逻辑，验证：
- _load_word_sets 词库列表填充、激活词库选中、current_set_id 维护
- _update_set_info 信息文案聚合
- _goto_page 空/非数字/越界/有效 四种输入校验
- _next_page / _prev_page / _first_page / _last_page 分页跳转
- _search_words 搜索重置到首页
"""
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from ui.word_set_page import WordSetPage


def _make_word_manager():
    wm = MagicMock()
    wm.get_all_word_sets.return_value = [
        {"id": 1, "name": "CET4", "word_count": 100, "description": "大学四级", "create_time": "2025"},
    ]
    wm.get_active_word_set.return_value = {"id": 1, "name": "CET4", "word_count": 100}
    wm.get_word_set_by_id.return_value = {"id": 1, "name": "CET4", "word_count": 100}
    wm.get_words_by_set_id.return_value = [
        {"id": 1, "word": "apple", "phonetic": "/a/", "tag": "n"},
    ]
    wm.get_translation.return_value = "苹果"
    return wm


@pytest.fixture
def word_set_page(tk_root):
    wm = _make_word_manager()
    font_config = {
        "header": ("Arial", 16, "bold"),
        "normal": ("Arial", 12),
        "button": ("Arial", 12, "bold"),
    }
    page = WordSetPage(tk_root, wm, font_config)
    yield page
    page.destroy()


# ---------------------------------------------------------------------------
# 词库列表加载
# ---------------------------------------------------------------------------
class TestLoadWordSets:
    def test_词库列表与激活态(self, word_set_page):
        assert word_set_page.set_listbox.size() == 1
        assert word_set_page.word_set_map == {0: 1}
        assert word_set_page.current_set_id == 1
        assert "CET4" in word_set_page.set_info_label.cget("text")

    def test_更新词库信息聚合(self, word_set_page):
        word_set_page._update_set_info(
            {"name": "TOEFL", "description": "托福词汇", "create_time": "2025"}
        )
        text = word_set_page.set_info_label.cget("text")
        assert "TOEFL" in text
        assert "托福词汇" in text
        assert "2025" in text


# ---------------------------------------------------------------------------
# 跳转页码校验
# ---------------------------------------------------------------------------
class TestGotoPage:
    def _set_goto(self, page, value):
        page.goto_entry.delete(0, tk.END)
        page.goto_entry.insert(0, value)

    def test_有效页码跳转(self, word_set_page):
        word_set_page.word_manager.get_word_set_by_id.return_value = {"word_count": 100}
        self._set_goto(word_set_page, "2")
        word_set_page._goto_page()
        assert word_set_page.current_page == 2
        # 100 个单词、每页 30 -> 总页数 4，offset = (2-1)*30 = 30
        args = word_set_page.word_manager.get_words_by_set_id.call_args
        assert args.kwargs["offset"] == 30

    def test_空输入警告(self, word_set_page):
        word_set_page.current_page = 1
        self._set_goto(word_set_page, "")
        with patch("ui.word_set_page.messagebox.showwarning") as warn:
            word_set_page._goto_page()
        warn.assert_called_once()
        assert word_set_page.current_page == 1

    def test_非数字警告(self, word_set_page):
        word_set_page.current_page = 1
        self._set_goto(word_set_page, "abc")
        with patch("ui.word_set_page.messagebox.showwarning") as warn:
            word_set_page._goto_page()
        warn.assert_called_once()
        assert word_set_page.current_page == 1

    def test_超过总页警告(self, word_set_page):
        word_set_page.word_manager.get_word_set_by_id.return_value = {"word_count": 100}
        word_set_page.current_page = 1
        self._set_goto(word_set_page, "10")  # 总页数仅 4
        with patch("ui.word_set_page.messagebox.showwarning") as warn:
            word_set_page._goto_page()
        warn.assert_called_once()
        assert word_set_page.current_page == 1

    def test_小于1警告(self, word_set_page):
        word_set_page.current_page = 1
        self._set_goto(word_set_page, "0")
        with patch("ui.word_set_page.messagebox.showwarning") as warn:
            word_set_page._goto_page()
        warn.assert_called_once()
        assert word_set_page.current_page == 1


# ---------------------------------------------------------------------------
# 分页按钮
# ---------------------------------------------------------------------------
class TestPaginationButtons:
    def test_下一页(self, word_set_page):
        word_set_page.current_page = 1
        word_set_page._next_page()
        assert word_set_page.current_page == 2

    def test_上一页(self, word_set_page):
        word_set_page.current_page = 3
        word_set_page._prev_page()
        assert word_set_page.current_page == 2

    def test_首页(self, word_set_page):
        word_set_page.current_page = 3
        word_set_page._first_page()
        assert word_set_page.current_page == 1

    def test_末页(self, word_set_page):
        word_set_page.word_manager.get_word_set_by_id.return_value = {"word_count": 100}
        word_set_page.current_page = 1
        word_set_page._last_page()
        # 100 个单词、每页 30 -> 总页数 4
        assert word_set_page.current_page == 4


# ---------------------------------------------------------------------------
# 搜索
# ---------------------------------------------------------------------------
class TestSearch:
    def test_搜索重置到首页(self, word_set_page):
        word_set_page.current_page = 3
        word_set_page.search_entry.delete(0, tk.END)
        word_set_page.search_entry.insert(0, "app")
        word_set_page._search_words()
        assert word_set_page.current_page == 1
        args = word_set_page.word_manager.get_words_by_set_id.call_args
        assert args.kwargs["keyword"] == "app"
