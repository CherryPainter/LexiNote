"""LexiNote 轻量 toast 提示。

解决审计发现的反馈机制问题：此前 129 处反馈全用模态 ``messagebox``（57 error /
30 info / 34 warning），非破坏性提示也弹窗打断操作流。本组件把**非关键**反馈
（info / success / warning）改为右下角自动消失的瞬时提示，仅保留 error / askyesno
等破坏性操作为模态。

用法::

    from ui.components.toast import show_toast
    show_toast(self, "已保存到本地", kind="success")
"""

from __future__ import annotations

import tkinter as tk

from ui.theme import COLORS, SPACING, RADIUS

# kind -> (色条色, 文字色)
_KIND_COLORS: dict[str, tuple[str, str]] = {
    "info": (COLORS["info"], COLORS["text_primary"]),
    "success": (COLORS["success"], COLORS["text_primary"]),
    "warning": (COLORS["warning"], COLORS["text_primary"]),
    "error": (COLORS["error"], COLORS["text_primary"]),
}


def show_toast(master: tk.Widget, message: str, kind: str = "info", duration: int = 2600) -> None:
    """在 master 右下角弹出一个自动消失的提示。

    :param master: 参照窗口（通常是页面根 Frame 或主窗口）
    :param message: 提示文字
    :param kind: info / success / warning / error
    :param duration: 显示毫秒数，超时自动销毁
    """
    bar_color, text_color = _KIND_COLORS.get(kind, _KIND_COLORS["info"])

    top = tk.Toplevel(master)
    top.wm_overrideredirect(True)
    top.attributes("-topmost", True)
    top.configure(bg=COLORS["surface"], relief=tk.FLAT,
                  highlightthickness=1, highlightbackground=COLORS["border"])

    # 左侧语义色条
    bar = tk.Frame(top, bg=bar_color, width=6)
    bar.pack(side=tk.LEFT, fill=tk.Y)

    label = tk.Label(
        top,
        text=message,
        bg=COLORS["surface"],
        fg=text_color,
        font=("SimHei", 11),
        padx=SPACING["lg"],
        pady=SPACING["md"],
        wraplength=320,
        justify=tk.LEFT,
    )
    label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 定位到 master 右下角（留出边距）
    top.update_idletasks()
    mw = master.winfo_width()
    mh = master.winfo_height()
    mx = master.winfo_rootx()
    my = master.winfo_rooty()
    tw = top.winfo_width()
    th = top.winfo_height()
    x = mx + max(SPACING["lg"], mw - tw - SPACING["lg"])
    y = my + max(SPACING["lg"], mh - th - SPACING["lg"] - 40)
    top.geometry(f"+{x}+{y}")

    # 自动消失
    top.after(duration, lambda: top.destroy())
