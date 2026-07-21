import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 确定程序安装目录，兼容开发模式与 Nuitka 打包（含 onefile）
# - 开发：直接运行 main.py，__file__ 即项目根
# - PyInstaller 等：sys.frozen 为真，sys.executable 即原始 exe
# - Nuitka（含 onefile）：不设 sys.frozen，且 onefile 下 sys.executable
#   指向临时解压目录；sys.argv[0] 保留用户启动时的原始命令，用它解析安装目录
if getattr(sys, "frozen", False):
    _app_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    _app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# 切换到安装目录，使 data/、cache/、word_dict.json、app.ico 等
# 相对路径在分发后仍能定位（与开发时 cwd=项目根行为一致）
os.chdir(_app_dir)
os.environ["LEXINOTE_APP_DIR"] = _app_dir

# 版本信息
VERSION = "v2.7.2"

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
