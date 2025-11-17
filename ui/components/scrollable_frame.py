"""
滚动功能辅助模块

提供通用的滚动区域实现，用于在Tkinter应用中创建可滚动的内容区域
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

    # 创建Canvas作为滚动容器
    canvas = tk.Canvas(scroll_frame, yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 配置滚动条
    scrollbar.config(command=canvas.yview)

    # 创建内部框架
    inner_frame = tk.Frame(canvas, *args, **kwargs)

    # 创建内部框架窗口
    canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # 定义配置回调函数
    def on_inner_configure(event):
        """当内部框架配置改变时更新Canvas滚动区域"""
        canvas.configure(scrollregion=canvas.bbox("all"))
        # 确保Canvas窗口宽度与Canvas一致
        width = event.width if event else canvas.winfo_width()
        if width > 0:
            canvas.itemconfig(canvas_window, width=width)

    def on_canvas_configure(event):
        """当Canvas配置改变时更新内部窗口宽度"""
        canvas.itemconfig(canvas_window, width=event.width)

    # 绑定事件
    inner_frame.bind("<Configure>", on_inner_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    # 自动添加鼠标滚轮支持 - 同时绑定到内部框架和Canvas
    # 这样无论鼠标在内容区域还是Canvas上都能滚动
    add_mousewheel_support(inner_frame, canvas)
    add_mousewheel_support(canvas, canvas)

    # 注意：Tkinter标准库不支持ChildAdded和ChildRemoved事件
    # 以下代码被注释掉，因为会导致运行时错误
    # 如果需要动态组件支持，可以考虑使用其他方法，如定时检查或手动调用重新绑定函数
    # def on_inner_frame_change(event):
    #     """当内部框架的子组件发生变化时，重新绑定鼠标滚轮事件"""
    #     # 为新添加的组件重新绑定鼠标滚轮事件
    #     add_mousewheel_support(inner_frame, canvas)

    # inner_frame.bind("<ChildAdded>", on_inner_frame_change)
    # inner_frame.bind("<ChildRemoved>", on_inner_frame_change)

    return scroll_frame, inner_frame, on_inner_configure, on_canvas_configure


def add_mousewheel_support(widget, canvas):
    """为窗口部件添加鼠标滚轮支持

    Args:
        widget: 要添加鼠标滚轮支持的窗口部件
        canvas: 关联的Canvas组件
    """
    def on_mousewheel(event):
        """处理鼠标滚轮事件"""
        # 根据系统调整滚动方向
        delta = -1 * int(event.delta / 120)
        canvas.yview_scroll(delta, "units")
        # 返回"break"以防止事件继续传播
        return "break"

    # 绑定鼠标滚轮事件到指定部件
    widget.bind("<MouseWheel>", on_mousewheel)  # Windows
    widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
    widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux

    # 递归为所有子组件添加鼠标滚轮支持
    # 这样无论鼠标在哪个子组件上滚动，都会触发Canvas滚动
    def bind_to_children(parent):
        for child in parent.winfo_children():
            # 绑定到当前子组件
            child.bind("<MouseWheel>", on_mousewheel)
            child.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            child.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            # 递归绑定到子组件的子组件
            bind_to_children(child)

    # 绑定到所有子组件
    bind_to_children(widget)
