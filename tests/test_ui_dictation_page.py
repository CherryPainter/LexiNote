"""ui/dictation_page.py 白盒测试。

使用 headless tkinter：用 MagicMock 构造 word_manager / settings_manager，
并对会触发真实 DB/AI 链接的 DictationManager、以及真实音频播放的 AudioPlayer
在模块层打桩；直接调用纯逻辑/事件处理方法，验证：
- _has_today_words / _ensure_source_has_words 来源可用性判断
- _on_mode_change 模式切换的 UI 显隐
- _check_answer 拼写校验与结果/记录
- _skip_word / _handle_timeout 跳过与超时处理
- _next_word 取词与界面重置
- _on_auto_mode_word_learning_change 自动/手动模式回调
- _start_dictation 单一模式(自动)下的参数组装
"""
import sys
import types
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

# audio_player 顶层依赖 gtts / playsound，测试环境未安装；
# 注入占位模块使页面模块可被导入（AudioPlayer 本身会在用例中打桩替换）
if "gtts" not in sys.modules:
    _g = types.ModuleType("gtts")
    _g.gTTS = object
    sys.modules["gtts"] = _g
if "playsound" not in sys.modules:
    _p = types.ModuleType("playsound")
    _p.playsound = lambda *a, **k: None
    sys.modules["playsound"] = _p

from ui.dictation_page import DictationPage


@pytest.fixture
def dictation_page(tk_root):
    wm = MagicMock()
    sm = MagicMock()
    sm.get_auto_mode.return_value = "manual"
    with patch("ui.dictation_page.DictationManager"), \
            patch("ui.dictation_page.AudioPlayer"):
        page = DictationPage(tk_root, wm, sm)
        yield page
        page.destroy()


# ---------------------------------------------------------------------------
# 来源可用性判断
# ---------------------------------------------------------------------------
class TestSourceAvailability:
    def test_今日单词存在(self, dictation_page):
        dictation_page.word_manager.get_today_learned_words.return_value = ["apple"]
        assert dictation_page._has_today_words() is True

    def test_今日单词为空(self, dictation_page):
        dictation_page.word_manager.get_today_learned_words.return_value = []
        assert dictation_page._has_today_words() is False

    def test_全词库来源有词(self, dictation_page):
        dictation_page.current_source = "library"
        dictation_page.word_manager.get_all_words.return_value = ["a", "b"]
        assert dictation_page._ensure_source_has_words() is True

    def test_熟词库来源有词(self, dictation_page):
        dictation_page.current_source = "familiar"
        dictation_page.word_manager.get_familiar_words.return_value = ["a"]
        assert dictation_page._ensure_source_has_words() is True

    def test_今日来源无词时询问且不继续(self, dictation_page):
        dictation_page.current_source = "today"
        dictation_page.word_manager.get_today_learned_words.return_value = []
        with patch("ui.dictation_page.messagebox.askyesno", return_value=False) as ask:
            result = dictation_page._ensure_source_has_words()
        assert result is False
        ask.assert_called_once()


# ---------------------------------------------------------------------------
# 模式切换
# ---------------------------------------------------------------------------
class TestModeChange:
    def test_队列模式显示批大小与时间(self, dictation_page):
        dictation_page.mode_var.set("queue")
        dictation_page._on_mode_change()
        assert dictation_page.batch_frame.winfo_manager() == "pack"
        assert dictation_page.time_frame.winfo_manager() == "pack"

    def test_单一模式隐藏批大小与时间(self, dictation_page):
        dictation_page.mode_var.set("single")
        dictation_page._on_mode_change()
        assert dictation_page.batch_frame.winfo_manager() == ""
        assert dictation_page.time_frame.winfo_manager() == ""


# ---------------------------------------------------------------------------
# 答题 / 跳过 / 超时
# ---------------------------------------------------------------------------
class TestAnswerFlow:
    def _prepare_exercise(self, page):
        page.current_mode = "single"
        page._create_exercise_ui()
        page.current_word = "apple"
        page.word_entry.delete(0, tk.END)
        page.session_results = []

    def test_拼写正确更新结果并记错空(self, dictation_page):
        self._prepare_exercise(dictation_page)
        dictation_page.word_entry.insert(0, "apple")
        dictation_page.word_manager.check_spelling.return_value = True
        dictation_page.word_manager.get_progress.return_value = {"correct_rate": 0.5}
        dictation_page._check_answer()
        assert dictation_page.result_var.get() == "✓ 正确！"
        _call = dictation_page.dictation_manager.record_result.call_args
        assert _call.args[0] == "apple"
        assert _call.args[1] is True
        assert dictation_page.session_results[-1]["correct"] is True

    def test_拼写错误记录错词(self, dictation_page):
        self._prepare_exercise(dictation_page)
        dictation_page.word_entry.insert(0, "appl")
        dictation_page.word_manager.check_spelling.return_value = False
        dictation_page.word_manager.get_progress.return_value = {"correct_rate": 0.5}
        dictation_page._check_answer()
        assert "错误" in dictation_page.result_var.get()
        dictation_page.word_manager.add_wrong_word.assert_called_once_with("apple")
        assert dictation_page.session_results[-1]["correct"] is False

    def test_空输入给出警告(self, dictation_page):
        self._prepare_exercise(dictation_page)
        dictation_page.word_entry.insert(0, "   ")
        with patch("ui.dictation_page.messagebox.showwarning") as warn:
            dictation_page._check_answer()
        warn.assert_called_once()
        dictation_page.dictation_manager.record_result.assert_not_called()

    def test_跳过单词记录(self, dictation_page):
        self._prepare_exercise(dictation_page)
        dictation_page.current_word = "apple"
        dictation_page._skip_word()
        _call = dictation_page.dictation_manager.skip_current_word.call_args
        assert _call.args[0] == "apple"
        assert "已跳过" in dictation_page.result_var.get()
        assert dictation_page.session_results[-1]["input"] == "skipped"

    def test_超时记录为错误(self, dictation_page):
        self._prepare_exercise(dictation_page)
        dictation_page.current_word = "apple"
        dictation_page.dictation_manager.current_queue = []
        dictation_page.dictation_manager.current_queue_index = 0
        dictation_page._handle_timeout()
        _call = dictation_page.dictation_manager.record_result.call_args
        assert _call.args[0] == "apple"
        assert _call.args[1] is False
        assert "超时" in dictation_page.result_var.get()
        assert dictation_page.session_results[-1]["input"] == "timeout"


# ---------------------------------------------------------------------------
# 取词
# ---------------------------------------------------------------------------
class TestNextWord:
    def test_取到单词并重置输入(self, dictation_page):
        dictation_page.current_mode = "single"
        dictation_page._create_exercise_ui()
        dictation_page.dictation_manager.select_word.return_value = "banana"
        dictation_page._next_word()
        assert dictation_page.current_word == "banana"
        assert dictation_page.word_entry.get() == ""
        assert dictation_page.result_var.get() == ""


# ---------------------------------------------------------------------------
# 自动/手动模式回调
# ---------------------------------------------------------------------------
class TestAutoModeChange:
    def test_切换为自动强制自动跳转(self, dictation_page):
        dictation_page._on_auto_mode_word_learning_change("auto_mode_word_learning", "auto")
        assert dictation_page.auto_next is True
        assert dictation_page.auto_next_checkbox.cget("state") == tk.DISABLED

    def test_切换为手动恢复勾选框(self, dictation_page):
        dictation_page._on_auto_mode_word_learning_change("auto_mode_word_learning", "manual")
        assert dictation_page.auto_next_checkbox.cget("state") == tk.NORMAL


# ---------------------------------------------------------------------------
# 开始听写（单一 + 自动模式）
# ---------------------------------------------------------------------------
class TestStartDictation:
    def test_单一自动模式组装参数(self, dictation_page):
        dictation_page.mode_var.set("single")
        dictation_page.auto_next_var.set(True)
        dictation_page.source_var.set("全词库随机")  # -> library
        dictation_page.settings_manager.get_auto_mode.return_value = "auto"
        dictation_page.word_manager.get_all_words.return_value = ["a", "b"]
        dictation_page.dictation_manager.select_word.return_value = "apple"
        dictation_page._start_dictation()
        assert dictation_page.auto_next is True
        assert dictation_page.current_source == "library"
        args = dictation_page.dictation_manager.start_session.call_args.kwargs
        assert args["mode"] == "single"
        assert args["source"] == "library"
        assert args["batch_size"] == 1
