"""ui/translation_page.py 白盒测试。

使用 headless tkinter：用 MagicMock 构造 word_manager / settings_manager，
对真实音频播放的 AudioPlayer 在模块层打桩；直接调用纯逻辑/事件处理方法，验证：
- _on_direction_change 翻译方向切换更新提示文案
- _check_translation 空输入校验 / 正确 / 错误三种分支
- _skip_translation 跳过结果文案
- _toggle_example 例句显示状态
- _on_auto_mode_translation_change 自动/手动模式对“下一个”按钮的影响
- _flash_background 背景闪烁
"""
import sys
import types
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

# audio_player 顶层依赖 gtts / playsound，测试环境未安装；注入占位模块
if "gtts" not in sys.modules:
    _g = types.ModuleType("gtts")
    _g.gTTS = object
    sys.modules["gtts"] = _g
if "playsound" not in sys.modules:
    _p = types.ModuleType("playsound")
    _p.playsound = lambda *a, **k: None
    sys.modules["playsound"] = _p

from ui.translation_page import TranslationPage


@pytest.fixture
def translation_page(tk_root):
    wm = MagicMock()
    wm.get_words_from_active_set.return_value = []
    wm.ai_available = True
    sm = MagicMock()
    font_config = {
        "title": ("Arial", 24),
        "normal": ("Arial", 16),
        "small": ("Arial", 12),
        "header": ("Arial", 18, "bold"),
        "button": ("Arial", 12),
    }
    with patch("ui.translation_page.AudioPlayer"):
        page = TranslationPage(tk_root, settings_manager=sm, word_manager=wm, font_config=font_config)
        yield page
        page.destroy()


# ---------------------------------------------------------------------------
# 翻译方向切换
# ---------------------------------------------------------------------------
class TestDirectionChange:
    def test_切到中译英更新提示(self, translation_page):
        translation_page.direction_var.set(False)
        translation_page._on_direction_change()
        assert translation_page.is_english_to_chinese is False
        assert translation_page.hint_var.get() == "请输入中文的英文翻译"

    def test_切到英译中更新提示(self, translation_page):
        translation_page.direction_var.set(True)
        translation_page._on_direction_change()
        assert translation_page.is_english_to_chinese is True
        assert translation_page.hint_var.get() == "请输入单词的中文翻译"


# ---------------------------------------------------------------------------
# 检查翻译
# ---------------------------------------------------------------------------
class TestCheckTranslation:
    def _prepare(self, page, is_correct):
        page.current_word = "apple"
        page.current_translation = "苹果"
        page.translation_text.delete("1.0", tk.END)
        page.translation_text.insert("1.0", "苹果")
        page.word_manager.check_translation.return_value = is_correct
        page.word_manager.get_progress.return_value = {"correct_rate": 0.5}
        page.word_manager.translate_text.return_value = "apple"

    def test_空输入给出警告(self, translation_page):
        translation_page.translation_text.delete("1.0", tk.END)
        translation_page.translation_text.insert("1.0", "   ")
        with patch("ui.translation_page.messagebox.showwarning") as warn:
            translation_page._check_translation()
        warn.assert_called_once()
        translation_page.word_manager.check_translation.assert_not_called()

    def test_翻译正确(self, translation_page):
        self._prepare(translation_page, True)
        translation_page._check_translation()
        assert "正确" in translation_page.result_var.get()
        translation_page.word_manager.update_word_weight.assert_called_once_with("apple", True, 0)

    def test_翻译错误(self, translation_page):
        self._prepare(translation_page, False)
        translation_page._check_translation()
        assert "不正确" in translation_page.result_var.get()
        translation_page.word_manager.add_wrong_word.assert_called_once_with("apple")


# ---------------------------------------------------------------------------
# 跳过翻译
# ---------------------------------------------------------------------------
class TestSkipTranslation:
    def test_跳过结果文案(self, translation_page):
        translation_page.current_word = "apple"
        translation_page.current_translation = "苹果"
        translation_page.word_manager.translate_text.return_value = "apple"
        translation_page._skip_translation()
        assert "已跳过" in translation_page.result_var.get()
        translation_page.word_manager.update_word_weight.assert_called_once_with("apple", False, 0)


# ---------------------------------------------------------------------------
# 例句显示
# ---------------------------------------------------------------------------
class TestToggleExample:
    def test_已缓存例句直接显示(self, translation_page):
        translation_page.current_word = "apple"
        translation_page.current_example = "An apple a day."
        translation_page._toggle_example()
        assert translation_page.is_example_visible is True
        assert translation_page.example_label.cget("text") == "An apple a day."
        assert translation_page.example_button.cget("text") == "📝 隐藏例句"


# ---------------------------------------------------------------------------
# 自动/手动模式回调
# ---------------------------------------------------------------------------
class TestAutoModeChange:
    def test_自动模式隐藏下一个按钮(self, translation_page):
        translation_page.result_var.set("✓ 正确")
        translation_page._on_auto_mode_translation_change("auto_mode_translation_practice", "auto")
        assert translation_page.next_button.winfo_manager() == ""

    def test_手动模式显示下一个按钮(self, translation_page):
        translation_page.result_var.set("✓ 正确")
        translation_page._on_auto_mode_translation_change("auto_mode_translation_practice", "manual")
        assert translation_page.next_button.winfo_manager() == "pack"


# ---------------------------------------------------------------------------
# 背景闪烁
# ---------------------------------------------------------------------------
class TestFlashBackground:
    def test_立即设置高亮背景(self, translation_page):
        translation_page._flash_background("#E8F5E9")
        # 第一次闪烁会把背景设为高亮色（后续恢复由 after 调度，无主循环不执行）
        assert translation_page.main_frame.cget("bg") == "#E8F5E9"
