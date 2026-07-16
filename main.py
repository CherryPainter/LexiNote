import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 打包为单文件 exe 后，将工作目录切换到可执行文件所在目录，
# 使 data/、cache/、word_dict.json 等相对路径在分发后仍能
# 定位到安装目录（与开发时 cwd=项目根的行为保持一致）
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# 版本信息
VERSION = "v2.7.1"

from logger import log_info, log_error


def main():
    """主程序入口"""
    try:
        log_info(f"程序启动 - LexiNote {VERSION}")

        # 导入主窗口类
        from ui.main_window import MainWindow

        # 创建并运行应用
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
        log_info("程序正常退出")

    except ImportError as e:
        error_msg = f"导入模块失败: {str(e)}"
        log_error(error_msg)
        messagebox.showerror("导入错误", error_msg)
        print(f"错误: {error_msg}")
        sys.exit(1)
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        log_error(error_msg)
        messagebox.showerror("运行错误", error_msg)
        print(f"错误: {error_msg}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
