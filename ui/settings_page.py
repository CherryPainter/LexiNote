import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings_manager import SettingsManager
from logger import log_info


class SettingsPage(tk.Frame):
    """设置页面，用于管理应用程序的各种设置"""
    
    def __init__(self, parent, settings_manager=None, word_manager=None, font_config=None, **kwargs):
        """初始化设置页面
        
        Args:
            parent: 父窗口组件
            settings_manager: 设置管理器实例
            word_manager: 单词管理器实例
            font_config: 字体配置字典
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        
        # 使用传入的settings_manager或创建新实例
        if settings_manager:
            self.settings_manager = settings_manager
        else:
            from core.settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
        
        self.word_manager = word_manager
        
        # 确保font_config有效
        if font_config:
            self.font_config = font_config
        else:
            self.font_config = {'normal': ('Arial', 12), 'header': ('Arial', 16, 'bold'), 'button': ('Arial', 12)}
        
        # 创建UI组件
        self._create_widgets()
        
        log_info("设置页面加载完成")
    
    def _create_widgets(self):
        """创建页面组件"""
        # 设置页面背景
        self.configure(bg="#f0f0f0")
        
        # 创建主框架
        main_frame = tk.Frame(self, bg="#f0f0f0", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="应用设置",
            font=self.font_config['header'],
            bg="#f0f0f0",
            fg="#333333"
        )
        title_label.pack(pady=20)
        
        # 创建设置卡片
        settings_card = tk.Frame(main_frame, bg="white", bd=2, relief=tk.RAISED)
        settings_card.pack(fill=tk.X, pady=10)
        
        # 自动切换设置
        auto_next_frame = tk.LabelFrame(
            settings_card,
            text="自动切换设置",
            font=self.font_config['normal'],
            bg="white",
            padx=20,
            pady=15
        )
        auto_next_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 答对后自动下一个
        self.auto_next_correct_var = tk.BooleanVar(
            value=self.settings_manager.get_setting("auto_next_correct", False)
        )
        auto_next_correct_checkbox = tk.Checkbutton(
            auto_next_frame,
            text="答对后自动跳转到下一个单词",
            variable=self.auto_next_correct_var,
            command=self._on_auto_next_correct_change,
            font=self.font_config['normal'],
            bg="white",
            anchor=tk.W
        )
        auto_next_correct_checkbox.pack(fill=tk.X, pady=5)
        
        # 答错后自动下一个
        self.auto_next_wrong_var = tk.BooleanVar(
            value=self.settings_manager.get_setting("auto_next_wrong", False)
        )
        auto_next_wrong_checkbox = tk.Checkbutton(
            auto_next_frame,
            text="答错后自动跳转到下一个单词",
            variable=self.auto_next_wrong_var,
            command=self._on_auto_next_wrong_change,
            font=self.font_config['normal'],
            bg="white",
            anchor=tk.W
        )
        auto_next_wrong_checkbox.pack(fill=tk.X, pady=5)
        
        # 功能设置
        features_frame = tk.LabelFrame(
            settings_card,
            text="功能设置",
            font=self.font_config['normal'],
            bg="white",
            padx=20,
            pady=15
        )
        features_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 例句功能
        self.example_enabled_var = tk.BooleanVar(
            value=self.settings_manager.get_setting("example_enabled", True)
        )
        example_enabled_checkbox = tk.Checkbutton(
            features_frame,
            text="启用例句功能",
            variable=self.example_enabled_var,
            command=self._on_example_enabled_change,
            font=self.font_config['normal'],
            bg="white",
            anchor=tk.W
        )
        example_enabled_checkbox.pack(fill=tk.X, pady=5)
        
        # 发音功能
        self.voice_enabled_var = tk.BooleanVar(
            value=self.settings_manager.get_setting("voice_enabled", True)
        )
        voice_enabled_checkbox = tk.Checkbutton(
            features_frame,
            text="启用发音功能",
            variable=self.voice_enabled_var,
            command=self._on_voice_enabled_change,
            font=self.font_config['normal'],
            bg="white",
            anchor=tk.W
        )
        voice_enabled_checkbox.pack(fill=tk.X, pady=5)
        
        # 重置设置按钮
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        reset_button = tk.Button(
            button_frame,
            text="重置为默认设置",
            command=self._on_reset_settings,
            font=self.font_config['button'],
            bg="#f44336",
            fg="white",
            padx=20,
            pady=10
        )
        reset_button.pack(pady=10)
        
        # 保存提示
        save_hint = tk.Label(
            main_frame,
            text="设置将自动保存",
            font=(self.font_config['normal'][0], 10, 'italic'),
            bg="#f0f0f0",
            fg="#666666"
        )
        save_hint.pack(pady=10)
    
    def _on_auto_next_correct_change(self):
        """处理答对后自动下一个设置变更"""
        value = self.auto_next_correct_var.get()
        self.settings_manager.set_setting("auto_next_correct", value)
        log_info(f"答对后自动下一个设置已更新为: {value}")
    
    def _on_auto_next_wrong_change(self):
        """处理答错后自动下一个设置变更"""
        value = self.auto_next_wrong_var.get()
        self.settings_manager.set_setting("auto_next_wrong", value)
        log_info(f"答错后自动下一个设置已更新为: {value}")
    
    def _on_example_enabled_change(self):
        """处理例句功能设置变更"""
        value = self.example_enabled_var.get()
        self.settings_manager.set_setting("example_enabled", value)
        log_info(f"例句功能设置已更新为: {value}")
    
    def _on_voice_enabled_change(self):
        """处理发音功能设置变更"""
        value = self.voice_enabled_var.get()
        self.settings_manager.set_setting("voice_enabled", value)
        log_info(f"发音功能设置已更新为: {value}")
    
    def _on_reset_settings(self):
        """重置设置为默认值"""
        if messagebox.askyesno("确认重置", "确定要将所有设置重置为默认值吗？"):
            # 删除设置文件，然后重新加载
            if os.path.exists(self.settings_manager.settings_file):
                try:
                    os.remove(self.settings_manager.settings_file)
                    # 重新加载设置
                    self.settings_manager.settings = self.settings_manager._load_settings()
                    # 更新UI
                    self.auto_next_correct_var.set(self.settings_manager.get_setting("auto_next_correct", False))
                    self.auto_next_wrong_var.set(self.settings_manager.get_setting("auto_next_wrong", False))
                    self.example_enabled_var.set(self.settings_manager.get_setting("example_enabled", True))
                    self.voice_enabled_var.set(self.settings_manager.get_setting("voice_enabled", True))
                    log_info("设置已重置为默认值")
                    messagebox.showinfo("重置成功", "设置已成功重置为默认值")
                except Exception as e:
                    log_info(f"重置设置失败: {str(e)}")
                    messagebox.showerror("重置失败", f"重置设置时出错: {str(e)}")