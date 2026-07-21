"""
滚动功能辅助模块

提供通用的滚动区域实现，用于在 Tkinter 应用中创建可滚动的内容区域。

关键改进：
- 鼠标滚轮绑定支持「动态添加的内容」：通过 refresh_mousewheel(scroll_frame)
  在填充完选项 / 题目等内容后重新绑定，避免动态控件无法滚动。
- 绑定幂等：重复绑定不会让滚动速度翻倍。
- canvas 的 yscrollincrement 设为合理像素值，滚轮一次滚动一屏的一小段而非 1 像素。
"""
import tkinter as tk


def create_scrollable_frame(parent, *args, **kwargs):
    """创建一个可滚动的框架

    Args:
        parent: 父窗口组件
        *args: 传递给内部框架的位置参数
        **kwargs: 传递给内部框架的关键字参数

    Returns:
        tuple: (scroll_frame, inner_frame, on_configure_callback, on_canvas_configure_callback)
    """
    # 创建滚动框架容器
    scroll_frame = tk.Frame(parent)
    scroll_frame.pack(fill=tk.BOTH, expand=True)

    # 创建滚动条
    scrollbar = tk.Scrollbar(scroll_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 创建 Canvas 作为滚动容器（yscrollincrement 决定每次滚轮滚动的像素量）
    canvas = tk.Canvas(scroll_frame, yscrollcommand=scrollbar.set, yscrollincrement=30)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 配置滚动条
    scrollbar.config(command=canvas.yview)

    # 创建内部框架
    inner_frame = tk.Frame(canvas, *args, **kwargs)

    # 创建内部框架窗口
    canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # 定义配置回调函数
    def on_inner_configure(event):
        """当内部框架配置改变时更新 Canvas 滚动区域"""
        canvas.configure(scrollregion=canvas.bbox("all"))
        # 确保 Canvas 窗口宽度与 Canvas 一致
        width = event.width if event else canvas.winfo_width()
        if width > 0:
            canvas.itemconfig(canvas_window, width=width)

    def on_canvas_configure(event):
        """当 Canvas 配置改变时更新内部窗口宽度"""
        canvas.itemconfig(canvas_window, width=event.width)

    # 绑定事件
    inner_frame.bind("<Configure>", on_inner_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    # 把 canvas 挂到 scroll_frame / inner_frame 上，便于后续 refresh_mousewheel 查找
    scroll_frame._scroll_canvas = canvas
    inner_frame._scroll_canvas = canvas

    # 初始绑定（仅覆盖创建时已有的子组件；动态内容稍后通过 refresh_mousewheel 重新绑定）
    add_mousewheel_support(inner_frame, canvas)

    return scroll_frame, inner_frame, on_inner_configure, on_canvas_configure


def add_mousewheel_support(widget, canvas):
    """为窗口部件及其递归子组件添加鼠标滚轮支持（幂等，可重复调用）

    Args:
        widget: 要添加鼠标滚轮支持的窗口部件
        canvas: 关联的 Canvas 组件
    """
    def on_mousewheel(event):
        """处理鼠标滚轮事件（Windows）"""
        delta = -1 * int(event.delta / 120)
        canvas.yview_scroll(delta, "units")
        # 返回 "break" 防止事件继续传播到其它绑定
        return "break"

    def on_linux_up(e):
        canvas.yview_scroll(-1, "units")
        return "break"

    def on_linux_down(e):
        canvas.yview_scroll(1, "units")
        return "break"

    # 先解绑，避免重复绑定导致滚动速度叠加
    for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        try:
            widget.unbind(seq)
        except Exception:
            pass

    widget.bind("<MouseWheel>", on_mousewheel)
    widget.bind("<Button-4>", on_linux_up)
    widget.bind("<Button-5>", on_linux_down)

    # 递归为所有子组件添加鼠标滚轮支持（幂等）
    def bind_to_children(parent):
        for child in parent.winfo_children():
            for seq, handler in (("<MouseWheel>", on_mousewheel),
                                  ("<Button-4>", on_linux_up),
                                  ("<Button-5>", on_linux_down)):
                try:
                    child.unbind(seq)
                except Exception:
                    pass
                child.bind(seq, handler)
            bind_to_children(child)

    bind_to_children(widget)


def refresh_mousewheel(scroll_frame):
    """在动态添加内容（选项 / 题目等）后，重新把整棵组件树绑定到所属 canvas 的滚动。

    Args:
        scroll_frame: create_scrollable_frame 返回的第一个元素
    """
    canvas = getattr(scroll_frame, "_scroll_canvas", None)
    if canvas is None:
        return
    # 对整个 scroll_frame 子树重新递归绑定（幂等，不会叠加速度）
    add_mousewheel_support(scroll_frame, canvas)
