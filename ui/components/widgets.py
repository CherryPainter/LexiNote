"""LexiNote 统一 UI 组件工厂。

解决审计发现的两类问题：
1. 62 个 ``tk.Button`` 直接硬编码、主操作绿有 ``#4CAF50/#2e7d32`` 两种、蓝有
   ``#2196F3/#1976D2`` 两种 —— 风格分裂；
2. 键盘焦点可见性几乎缺失（仅 dictation/translation 有） —— 违反 WCAG 2.4.7。

提供：
- ``create_button``：primary / secondary / ghost 三态，自带 hover / active /
  disabled 与**键盘焦点环**（highlightthickness + highlightcolor），全项目统一。
- ``create_card``：统一高程的浅底容器（FLAT + 细边框，替代原先 RAISED/SUNKEN/
  SOLID/FLAT 混用）。

所有颜色取自 ``ui.theme``，不在本文件写死。
"""

from __future__ import annotations

import tkinter as tk

from ui.theme import COLORS, SPACING, RADIUS
from ui.font_config import FontConfig

# 由 create_button 统一管理的样式键，不允许调用方通过 kwargs 覆盖，保证一致性
_RESERVED = {
    "bg", "fg", "activebackground", "activeforeground", "relief", "bd",
    "highlightthickness", "highlightcolor", "highlightbackground", "cursor",
    "takefocus", "font", "text", "command",
}

# 每种风格的基础配色（hover / active 由这里推导）
_STYLES: dict[str, dict[str, str]] = {
    "primary": {
        "bg": COLORS["primary"],
        "fg": COLORS["text_on_primary"],
        "hover": COLORS["primary_hover"],
        "active": COLORS["primary_active"],
    },
    "secondary": {
        "bg": COLORS["info"],
        "fg": COLORS["text_on_info"],
        "hover": COLORS["info_hover"],
        "active": COLORS["info_hover"],
    },
    "ghost": {
        "bg": COLORS["surface"],
        "fg": COLORS["text_primary"],
        "hover": COLORS["surface_alt"],
        "active": COLORS["surface_alt2"],
    },
    "warning": {
        "bg": COLORS["warning"],
        "fg": COLORS["text_on_primary"],
        "hover": COLORS["warning_hover"],
        "active": COLORS["warning_active"],
    },
    "danger": {
        "bg": COLORS["error"],
        "fg": COLORS["text_on_primary"],
        "hover": COLORS["error_hover"],
        "active": COLORS["error_active"],
    },
    "neutral": {
        "bg": COLORS["sidebar_btn"],
        "fg": COLORS["text_primary"],
        "hover": COLORS["sidebar_btn_hover"],
        "active": COLORS["sidebar_btn"],
    },
    "purple": {
        "bg": COLORS["purple"],
        "fg": COLORS["text_on_primary"],
        "hover": COLORS["purple_hover"],
        "active": COLORS["purple_active"],
    },
}


def create_button(
    master: tk.Widget,
    text: str,
    command=None,
    *,
    style: str = "primary",
    font_config: FontConfig | None = None,
    width: int | None = None,
    state: str = tk.NORMAL,
    **kwargs,
) -> tk.Button:
    """创建统一风格按钮。

    :param style: primary（绿填充）/ secondary（蓝填充）/ ghost（描边）
    :param font_config: 传入页面已有的 FontConfig 以保持字体一致；缺省自建
    :param width: 字符宽度（按钮内文字较短时建议显式给，避免长短不一）
    """
    spec = _STYLES.get(style, _STYLES["primary"])
    fc = font_config if font_config is not None else FontConfig()

    # 过滤掉会破坏统一风格的键
    for k in _RESERVED:
        kwargs.pop(k, None)

    btn = tk.Button(
        master,
        text=text,
        command=command,
        font=fc["button"],
        bg=spec["bg"],
        fg=spec["fg"],
        activebackground=spec["active"],
        activeforeground=spec["fg"],
        relief=tk.FLAT if style != "ghost" else tk.SOLID,
        bd=0 if style != "ghost" else 1,
        highlightthickness=2,
        # 未聚焦时用自身底色作 highlightbackground → 看不到边框；聚焦时显示蓝色焦点环
        highlightcolor=COLORS["info"],
        highlightbackground=spec["bg"],
        cursor="hand2" if state == tk.NORMAL else "arrow",
        takefocus=True,
        width=width,
        state=state,
        **kwargs,
    )

    # hover：仅正常态切换底色
    def _on_enter(e):
        if btn["state"] == tk.NORMAL:
            btn.config(bg=spec["hover"])

    def _on_leave(e):
        if btn["state"] == tk.NORMAL:
            btn.config(bg=spec["bg"])

    btn.bind("<Enter>", _on_enter)
    btn.bind("<Leave>", _on_leave)
    return btn


def create_card(master: tk.Widget, **kwargs) -> tk.Frame:
    """统一高程的浅底容器：FLAT + 细边框，替代原先 RAISED/SUNKEN/SOLID 混用。"""
    for k in ("bg", "relief", "bd", "highlightthickness", "highlightbackground"):
        kwargs.pop(k, None)
    return tk.Frame(
        master,
        bg=COLORS["surface_alt"],
        relief=tk.FLAT,
        bd=1,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        **kwargs,
    )
