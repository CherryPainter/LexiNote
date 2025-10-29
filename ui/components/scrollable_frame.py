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
    
    # 绑定鼠标滚轮事件
    widget.bind("<MouseWheel>", on_mousewheel)  # Windows
    widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
    widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux