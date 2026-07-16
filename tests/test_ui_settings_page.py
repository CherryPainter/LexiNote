"""ui/settings_page.py 白盒测试。

使用 headless tkinter：用 MagicMock 构造 settings_manager / word_manager，
并对会触发真实 AI 连接的 AIManager 在模块层打桩；
直接调用纯逻辑/事件处理方法，验证：
- _normalize_url 的 URL 补全逻辑
- 各开关/模式切换回调对 settings_manager 的写入
- _apply_ai_mode_ui 对本地/云端配置区域的显示切换
- _on_save_cloud_config 的必填项校验与保存分支
- _on_reset_settings 重置流程
"""
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from ui.settings_page import SettingsPage


def _make_settings_manager():
    """构造一个返回合理默认值的 settings_manager Mock。"""
    sm = MagicMock()

    defaults = {
        "auto_next_correct": False,
        "auto_next_wrong": False,
        "example_enabled": True,
        "voice_enabled": True,
        "ai_summary_enabled": True,
        "translation_mode": "ai_first",
        "auto_mode_word_learning": "manual",
        "auto_mode_translation_practice": "manual",
        "auto_mode_review": "manual",
    }

    def get_setting(key, default=None):
        return defaults.get(key, default)

    sm.get_setting.side_effect = get_setting
    sm.get_ai_mode.return_value = "off"
    sm.get_cloud_ai_enabled.return_value = False
    sm.get_cloud_ai_api_url.return_value = ""
    sm.get_cloud_ai_api_key.return_value = ""
    sm.get_cloud_ai_model_name.return_value = ""
    return sm


@pytest.fixture
def settings_page(tk_root):
    sm = _make_settings_manager()
    wm = MagicMock()
    with patch("ui.settings_page.AIManager"):
        page = SettingsPage(tk_root, settings_manager=sm, word_manager=wm)
        yield page
        page.destroy()


# ---------------------------------------------------------------------------
# _normalize_url：纯字符串处理逻辑
# ---------------------------------------------------------------------------
class TestNormalizeUrl:
    def test_空字符串返回空(self):
        assert SettingsPage._normalize_url("") == ""

    def test_无协议前缀自动补全https(self):
        assert SettingsPage._normalize_url("api.example.com") == "https://api.example.com"

    def test_已有http协议保持不变(self):
        assert SettingsPage._normalize_url("http://a.com/x") == "http://a.com/x"

    def test_已有https协议保持不变(self):
        assert SettingsPage._normalize_url("https://a.com/x") == "https://a.com/x"

    def test_首尾空格被剥离后再补全(self):
        assert SettingsPage._normalize_url("  example.com  ") == "https://example.com"


# ---------------------------------------------------------------------------
# 开关/模式切换回调
# ---------------------------------------------------------------------------
class TestToggleCallbacks:
    def test_答对自动下一个写入设置(self, settings_page):
        settings_page.auto_next_correct_var.set(True)
        settings_page._on_auto_next_correct_change()
        settings_page.settings_manager.set_setting.assert_called_with("auto_next_correct", True)

    def test_答错自动下一个写入设置(self, settings_page):
        settings_page.auto_next_wrong_var.set(False)
        settings_page._on_auto_next_wrong_change()
        settings_page.settings_manager.set_setting.assert_called_with("auto_next_wrong", False)

    def test_例句功能开关写入设置(self, settings_page):
        settings_page.example_enabled_var.set(False)
        settings_page._on_example_enabled_change()
        settings_page.settings_manager.set_setting.assert_called_with("example_enabled", False)

    def test_云开关启用时同步ai模式为cloud(self, settings_page):
        settings_page.cloud_enabled_var.set(True)
        settings_page._on_cloud_enabled_change()
        sm = settings_page.settings_manager
        sm.set_cloud_ai_enabled.assert_called_with(True)
        sm.set_ai_mode.assert_called_with("cloud")
        assert settings_page.ai_mode_var.get() == "cloud"

    def test_云开关关闭时同步ai模式为off(self, settings_page):
        settings_page.cloud_enabled_var.set(False)
        settings_page._on_cloud_enabled_change()
        sm = settings_page.settings_manager
        sm.set_cloud_ai_enabled.assert_called_with(False)
        sm.set_ai_mode.assert_called_with("off")
        assert settings_page.ai_mode_var.get() == "off"


# ---------------------------------------------------------------------------
# _apply_ai_mode_ui：根据模式显示/隐藏本地与云端配置区
# ---------------------------------------------------------------------------
class TestApplyAiModeUi:
    def test_本地模式显示本地框隐藏云端框(self, settings_page):
        settings_page.ai_mode_var.set("local")
        settings_page._apply_ai_mode_ui()
        assert settings_page.local_ai_frame.winfo_manager() == "pack"
        assert settings_page.cloud_frame.winfo_manager() == ""

    def test_云端模式显示云端框隐藏本地框(self, settings_page):
        settings_page.ai_mode_var.set("cloud")
        settings_page._apply_ai_mode_ui()
        assert settings_page.cloud_frame.winfo_manager() == "pack"
        assert settings_page.local_ai_frame.winfo_manager() == ""

    def test_关闭模式两者均隐藏(self, settings_page):
        settings_page.ai_mode_var.set("off")
        settings_page._apply_ai_mode_ui()
        assert settings_page.local_ai_frame.winfo_manager() == ""
        assert settings_page.cloud_frame.winfo_manager() == ""


# ---------------------------------------------------------------------------
# _on_save_cloud_config：必填校验与保存分支
# ---------------------------------------------------------------------------
class TestSaveCloudConfig:
    def test_启用但缺少api地址时警告且不保存(self, settings_page):
        settings_page.cloud_enabled_var.set(True)
        settings_page.cloud_api_url_var.set("")
        settings_page.cloud_api_key_var.set("k")
        settings_page.cloud_model_name_var.set("m")
        with patch("ui.settings_page.messagebox.showwarning") as warn:
            settings_page._on_save_cloud_config()
        warn.assert_called_once()
        settings_page.settings_manager.save_cloud_ai_config.assert_not_called()

    def test_启用但缺少api密钥时警告(self, settings_page):
        settings_page.cloud_enabled_var.set(True)
        settings_page.cloud_api_url_var.set("http://x")
        settings_page.cloud_api_key_var.set("")
        settings_page.cloud_model_name_var.set("m")
        with patch("ui.settings_page.messagebox.showwarning") as warn:
            settings_page._on_save_cloud_config()
        warn.assert_called_once()

    def test_字段齐全时保存成功(self, settings_page):
        settings_page.cloud_enabled_var.set(True)
        settings_page.cloud_api_url_var.set("example.com")  # 会被补全为 https://
        settings_page.cloud_api_key_var.set("k")
        settings_page.cloud_model_name_var.set("m")
        settings_page.settings_manager.save_cloud_ai_config.return_value = True
        with patch("ui.settings_page.messagebox.showinfo") as info:
            settings_page._on_save_cloud_config()
        # 保存时自动补全了 https:// 前缀
        args = settings_page.settings_manager.save_cloud_ai_config.call_args.args
        assert args[0] is True
        assert args[1] == "https://example.com"
        info.assert_called_once()

    def test_保存返回失败时报错(self, settings_page):
        settings_page.cloud_enabled_var.set(True)
        settings_page.cloud_api_url_var.set("http://x")
        settings_page.cloud_api_key_var.set("k")
        settings_page.cloud_model_name_var.set("m")
        settings_page.settings_manager.save_cloud_ai_config.return_value = False
        with patch("ui.settings_page.messagebox.showerror") as err:
            settings_page._on_save_cloud_config()
        err.assert_called_once()

    def test_未启用时跳过必填校验直接保存(self, settings_page):
        settings_page.cloud_enabled_var.set(False)
        settings_page.settings_manager.save_cloud_ai_config.return_value = True
        with patch("ui.settings_page.messagebox.showinfo") as info:
            settings_page._on_save_cloud_config()
        info.assert_called_once()
        # 关闭状态下依然以 enabled=False 调用保存
        assert settings_page.settings_manager.save_cloud_ai_config.call_args.args[0] is False


# ---------------------------------------------------------------------------
# _on_reset_settings：重置流程
# ---------------------------------------------------------------------------
class TestResetSettings:
    def test_确认后执行重置(self, settings_page):
        with patch("ui.settings_page.messagebox.askyesno", return_value=True), \
                patch("ui.settings_page.messagebox.showinfo") as info:
            settings_page._on_reset_settings()
        settings_page.settings_manager.reset_to_default.assert_called_once()
        info.assert_called_once()

    def test_取消时不重置(self, settings_page):
        with patch("ui.settings_page.messagebox.askyesno", return_value=False):
            settings_page._on_reset_settings()
        settings_page.settings_manager.reset_to_default.assert_not_called()
