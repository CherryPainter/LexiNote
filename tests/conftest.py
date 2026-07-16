"""白盒测试公共配置：将项目根目录加入 sys.path，并在每个测试前重置全局单例。"""
import os
import sys
from pathlib import Path

import pytest
import tkinter as tk

# 项目根目录（tests 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def tk_root():
    """整个测试会话共享单一 Tk 根。

    tkinter 在销毁首个 Tk() 后于同一进程内再创建 Tk() 容易触发 TclError
    （"tk wasn't installed properly"），故全程只建一个根，会话结束才销毁。
    """
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _reset_singletons():
    """重置 AIManager / SettingsManager 单例，避免测试间状态串扰。"""
    from core.ai_interface import AIManager
    from core.settings_manager import SettingsManager
    AIManager._instance = None
    AIManager._initialized = False
    SettingsManager._instance = None
    yield
    AIManager._instance = None
    AIManager._initialized = False
    SettingsManager._instance = None
