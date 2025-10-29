import tkinter as tk
from tkinter import ttk
import threading

class LoadingDialog:
    """加载对话框，用于异步操作时显示进度"""
    
    def __init__(self, parent, title="加载中...", message="正在处理请求，请稍候..."):
        self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("300x100")
        self.top.resizable(False, False)
        
        # 设置为模态对话框
        self.top.transient(parent)
        self.top.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 标签
        self.message_var = tk.StringVar(value=message)
        self.message_label = tk.Label(self.top, textvariable=self.message_var, font=('SimHei', 12))
        self.message_label.pack(pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(self.top, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=10)
        self.progress.start(10)
        
        # 结果和错误存储
        self.result = None
        self.error = None
        self.done = False
    
    def _center_window(self):
        """将窗口居中显示"""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.parent.winfo_width() // 2) - (width // 2) + self.parent.winfo_x()
        y = (self.parent.winfo_height() // 2) - (height // 2) + self.parent.winfo_y()
        self.top.geometry(f"{width}x{height}+{x}+{y}")
    
    def update_message(self, message):
        """更新提示消息"""
        self.message_var.set(message)
    
    def set_result(self, result):
        """设置操作结果"""
        self.result = result
        self.done = True
        self.close()
    
    def set_error(self, error):
        """设置错误信息"""
        self.error = error
        self.done = True
        self.close()
    
    def close(self):
        """关闭对话框"""
        self.progress.stop()
        self.top.destroy()
    
    def run_task(self, task_func, *args, **kwargs):
        """在单独线程中运行任务
        
        Args:
            task_func: 要执行的任务函数
            *args, **kwargs: 传递给任务函数的参数
        """
        def task_wrapper():
            try:
                result = task_func(*args, **kwargs)
                self.parent.after(0, lambda: self.set_result(result))
            except Exception as e:
                self.parent.after(0, lambda: self.set_error(str(e)))
        
        thread = threading.Thread(target=task_wrapper)
        thread.daemon = True
        thread.start()
        
        # 等待对话框关闭
        self.parent.wait_window(self.top)
        
        # 如果有错误，抛出异常
        if self.error:
            raise Exception(self.error)
        
        return self.result