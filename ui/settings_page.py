import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        
        # 创建滚动条和画布
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(self, bg="#f0f0f0", yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        self.scrollbar.config(command=self.canvas.yview)
        
        # 创建主框架
        main_frame = tk.Frame(self.canvas, bg="#f0f0f0", padx=30, pady=20)
        # 保存canvas窗口ID
        self.canvas_window = self.canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        
        # 更新画布滚动区域
        def _on_canvas_configure(event):
            # 调整canvas窗口宽度以匹配画布宽度
            self.canvas.itemconfig(self.canvas_window, width=event.width)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        def _on_main_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        main_frame.bind("<Configure>", _on_main_frame_configure)
        self.canvas.bind("<Configure>", _on_canvas_configure)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="应用设置",
            font=self.font_config['header'],
            bg="#f0f0f0",
            fg="#333333"
        )
        title_label.pack(pady=20)
        
        # 创建居中容器框架
        center_frame = tk.Frame(main_frame, bg="#f0f0f0")
        center_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建设置卡片，不再设置固定宽度
        settings_card = tk.Frame(center_frame, bg="white", bd=2, relief=tk.RAISED)
        settings_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
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

        # 新增：模块自动切换（手动/自动）控制
        module_auto_frame = tk.Frame(auto_next_frame, bg="white")
        module_auto_frame.pack(fill=tk.X, pady=10)

        # helper to create a labeled combobox
        def _make_mode_control(parent, label_text, module_key):
            lbl = tk.Label(parent, text=label_text, font=self.font_config['normal'], bg='white')
            lbl.pack(anchor=tk.W, pady=(6, 0))

            var = tk.StringVar()
            # 显示为中文：手动 / 自动
            combo = ttk.Combobox(parent, textvariable=var, values=["手动", "自动"], state='readonly')

            # 读取当前设置并设置显示值
            internal = self.settings_manager.get_setting(module_key, 'manual')
            display = '自动' if internal == 'auto' else '手动'
            combo.set(display)

            def _on_change(event=None, mk=module_key, v=var):
                sel = v.get()
                mode = 'auto' if sel == '自动' else 'manual'
                # module_key is the internal settings key
                self.settings_manager.set_setting(mk, mode)
                log_info(f"设置 {mk} 为 {mode}")

            combo.bind('<<ComboboxSelected>>', _on_change)
            combo.pack(fill=tk.X, pady=2)
            return combo

        # 为三个模块分别创建控制器（使用内部 key names）
        self.auto_word_learning_combo = _make_mode_control(module_auto_frame, "单词学习模块自动切换", 'auto_mode_word_learning')
        self.auto_translation_combo = _make_mode_control(module_auto_frame, "翻译练习模块自动切换", 'auto_mode_translation_practice')
        self.auto_review_combo = _make_mode_control(module_auto_frame, "单词复习模块自动切换", 'auto_mode_review')
        
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

        # 翻译判定模式设置
        translation_frame = tk.LabelFrame(
            settings_card,
            text="翻译判定模式",
            font=self.font_config['normal'],
            bg="white",
            padx=20,
            pady=15
        )
        translation_frame.pack(fill=tk.X, padx=20, pady=15)

        # 下拉选择 AI 优先 / 本地优先 / 仅本地
        self.translation_mode_var = tk.StringVar(
            value=self.settings_manager.get_setting("translation_mode", "ai_first")
        )
        self.translation_mode_combo = ttk.Combobox(
            translation_frame,
            textvariable=self.translation_mode_var,
            values=["ai_first", "local_first", "local_only"],
            state="readonly",
            font=self.font_config['normal']
        )
        # 为用户显示友好名称，同时内部使用键
        def _format_display(val):
            return {
                "ai_first": "AI 优先",
                "local_first": "本地优先",
                "local_only": "仅本地"
            }.get(val, val)

        # 设置显示为友好文本（但保留实际值）
        self.translation_mode_combo['values'] = ["AI 优先", "本地优先", "仅本地"]
        # 将当前内部值映射到显示值
        display_map = {"ai_first": "AI 优先", "local_first": "本地优先", "local_only": "仅本地"}
        current = self.settings_manager.get_setting("translation_mode", "ai_first")
        self.translation_mode_combo.set(display_map.get(current, current))

        def _on_translation_mode_change(event=None):
            # 反向映射
            rev = {v: k for k, v in display_map.items()}
            sel = self.translation_mode_combo.get()
            mode = rev.get(sel, sel)
            self.settings_manager.set_setting("translation_mode", mode)
            log_info(f"翻译判定模式已更新为: {mode}")

        self.translation_mode_combo.bind('<<ComboboxSelected>>', _on_translation_mode_change)
        self.translation_mode_combo.pack(fill=tk.X, pady=5)
        
        # 重置设置按钮，居中显示
        button_frame = tk.Frame(center_frame, bg="#f0f0f0")
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
            center_frame,
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
            # 使用 SettingsManager API 重置为默认
            try:
                self.settings_manager.reset_to_default()
                # 更新UI（使用 hasattr 以避免某些路径下未创建控件时报错）
                self.auto_next_correct_var.set(self.settings_manager.get_setting("auto_next_correct", False))
                self.auto_next_wrong_var.set(self.settings_manager.get_setting("auto_next_wrong", False))
                self.example_enabled_var.set(self.settings_manager.get_setting("example_enabled", True))
                self.voice_enabled_var.set(self.settings_manager.get_setting("voice_enabled", True))
                if hasattr(self, 'tts_provider_var'):
                    self.tts_provider_var.set(self.settings_manager.get_setting("tts_provider", "gTTS"))
                if hasattr(self, 'tts_cache_enabled_var'):
                    self.tts_cache_enabled_var.set(self.settings_manager.get_setting("tts_cache_enabled", True))
                if hasattr(self, 'tts_cache_max_var'):
                    self.tts_cache_max_var.set(self.settings_manager.get_setting("tts_cache_max_mb", 500))
                if hasattr(self, 'translation_mode_combo'):
                    # 把内部值映射回显示值
                    display_map = {"ai_first": "AI 优先", "local_first": "本地优先", "local_only": "仅本地"}
                    current = self.settings_manager.get_setting("translation_mode", "ai_first")
                    self.translation_mode_combo.set(display_map.get(current, current))
                if hasattr(self, 'auto_word_learning_combo'):
                    self.auto_word_learning_combo.set('自动' if self.settings_manager.get_setting('auto_mode_word_learning','manual')=='auto' else '手动')
                if hasattr(self, 'auto_translation_combo'):
                    self.auto_translation_combo.set('自动' if self.settings_manager.get_setting('auto_mode_translation_practice','manual')=='auto' else '手动')
                if hasattr(self, 'auto_review_combo'):
                    self.auto_review_combo.set('自动' if self.settings_manager.get_setting('auto_mode_review','manual')=='auto' else '手动')
                log_info("设置已重置为默认值")
                messagebox.showinfo("重置成功", "设置已成功重置为默认值")
            except Exception as e:
                log_info(f"重置设置失败: {str(e)}")
                messagebox.showerror("重置失败", f"重置设置时出错: {str(e)}")

    def _on_tts_provider_change(self):
        val = self.tts_provider_var.get()
        self.settings_manager.set_setting("tts_provider", val)
        log_info(f"TTS 提供商已更新为: {val}")

    def _on_tts_cache_enabled_change(self):
        val = self.tts_cache_enabled_var.get()
        self.settings_manager.set_setting("tts_cache_enabled", val)
        log_info(f"TTS 缓存开关已更新为: {val}")

    def _on_tts_cache_max_change(self):
        try:
            val = int(self.tts_cache_max_var.get())
            self.settings_manager.set_setting("tts_cache_max_mb", val)
            log_info(f"TTS 缓存上限已更新为: {val} MB")
        except Exception:
            messagebox.showwarning("输入错误", "请输入有效的数字")