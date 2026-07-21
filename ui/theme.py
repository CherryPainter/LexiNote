"""LexiNote 设计 Token（唯一视觉来源）。

把原先散落在各页面、写成硬编码十六进制与裸 `bg='white'` 的颜色、间距、圆角
统一收敛到此处。所有 UI 组件与页面应**只从这里取值**，不要在业务代码里再写
死颜色，否则会重新制造视觉碎片化（此前审计发现 26 种不同 hex、164 处 white）。

使用方式::

    from ui.theme import COLORS, SPACING, RADIUS
    lbl = tk.Label(root, bg=COLORS['surface'], fg=COLORS['text_primary'])

字体仍由 ``ui.font_config.FontConfig`` 负责，本模块不重复定义。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 颜色 —— 语义化命名，避免“#4CAF50 到底是什么意思”的歧义
# 命名去重自既有实现（大小写不一致的 #FF9800/#ff9800 等已合并为一处）
# ---------------------------------------------------------------------------
COLORS: dict[str, str] = {
    # 品牌主色（绿）—— 主操作、选中态、成功
    "primary": "#4CAF50",
    "primary_hover": "#43A047",
    "primary_active": "#388E3C",
    "primary_tint": "#E8F5E9",   # 浅绿底，用于选中项背景
    # 次色（蓝）—— 次要操作、信息、焦点环
    "info": "#2196F3",
    "info_hover": "#1976D2",
    "info_tint": "#E3F2FD",
    # 语义状态色
    "success": "#4CAF50",
    "warning": "#FF9800",
    "warning_hover": "#FB8C00",
    "warning_active": "#F57C00",
    "warning_tint": "#FFF3E0",
    "error": "#F44336",
    "error_hover": "#E53935",
    "error_active": "#D32F2F",
    "error_tint": "#FFEBEE",
    "accent": "#4CAF50",         # 导航左侧色条
    # 紫色强调（仅用于“下一个”等操作按钮，避免与语义色混淆）
    "purple": "#9C27B0",
    "purple_hover": "#8E24AA",
    "purple_active": "#7B1FA2",
    "purple_tint": "#F3E5F5",
    # 表面 / 背景
    "sidebar": "#F0F0F0",
    "sidebar_btn": "#E0E0E0",
    "sidebar_btn_hover": "#D0D0D0",
    "surface": "#FFFFFF",        # 主内容区
    "surface_alt": "#F5F5F5",    # 卡片 / 区块底
    "surface_alt2": "#F9F9F9",
    "border": "#E0E0E0",
    # 文本
    "text_primary": "#333333",
    "text_secondary": "#666666",
    "text_tertiary": "#999999",
    "text_on_primary": "#FFFFFF",
    "text_on_info": "#FFFFFF",
}

# ---------------------------------------------------------------------------
# 间距尺度 —— 8pt 基线（4/8/12/16/24/32），统一视觉节奏
# ---------------------------------------------------------------------------
SPACING: dict[str, int] = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

# ---------------------------------------------------------------------------
# 圆角
# ---------------------------------------------------------------------------
RADIUS: dict[str, int] = {
    "sm": 4,
    "md": 6,
    "lg": 8,
}

# 统一高程：所有带边框/阴影的容器用同一种 relief + 边框色，避免 RAISED/SUNKEN/
# SOLID/FLAT 混用（审计发现 47 处混用）。卡片类用 FLAT + 细边框即可。
ELEVATION_BORDER = COLORS["border"]


def color(name: str) -> str:
    """按语义名取色，缺失返回 text_primary 兜底，绝不抛 KeyError。"""
    return COLORS.get(name, COLORS["text_primary"])


def space(name: str) -> int:
    """按语义名取间距，缺失返回 md(12)。"""
    return SPACING.get(name, SPACING["md"])
