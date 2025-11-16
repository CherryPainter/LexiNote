import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info
from core.ai_interface import AIManager
from ui.components.scrollable_frame import create_scrollable_frame


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
        
        # 使用统一的滚动框架实现
        scroll_frame, main_frame, _, _ = create_scrollable_frame(self, padx=30, pady=20)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
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

        # AI总结功能
        self.ai_summary_enabled_var = tk.BooleanVar(
            value=self.settings_manager.get_setting("ai_summary_enabled", True)
        )
        ai_summary_enabled_checkbox = tk.Checkbutton(
            features_frame,
            text="启用听写AI总结功能",
            variable=self.ai_summary_enabled_var,
            command=self._on_ai_summary_enabled_change,
            font=self.font_config['normal'],
            bg="white",
            anchor=tk.W
        )
        ai_summary_enabled_checkbox.pack(fill=tk.X, pady=5)

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
        
        # AI模型设置
        ai_model_frame = tk.LabelFrame(
            settings_card,
            text="AI模型设置",
            font=self.font_config['normal'],
            bg="white",
            padx=20,
            pady=15
        )
        ai_model_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 初始化AI管理器
        self.ai_manager = AIManager()
        
        # 当前模型选择
        model_label = tk.Label(
            ai_model_frame,
            text="当前使用模型:",
            font=self.font_config['normal'],
            bg="white"
        )
        model_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 模型选择下拉框
        self.ai_model_var = tk.StringVar(value="加载中...")
        self.ai_model_combo = ttk.Combobox(
            ai_model_frame,
            textvariable=self.ai_model_var,
            values=[],
            state="disabled",
            font=self.font_config['normal']
        )
        
        # 异步加载可用模型，避免UI阻塞
        self.after(100, self._load_ai_models_async)
        
        # 选择事件处理
        def _on_model_change(event=None):
            selected_model = self.ai_model_var.get()
            if selected_model:
                self.settings_manager.set_ai_model(selected_model)
                log_info(f"AI模型已切换为: {selected_model}")
                messagebox.showinfo("切换成功", f"已成功切换到模型: {selected_model}\n应用重启后生效")
        
        self.ai_model_combo.bind('<<ComboboxSelected>>', _on_model_change)
        self.ai_model_combo.pack(fill=tk.X, pady=5)
        
        # 模型管理按钮框架
        model_buttons_frame = tk.Frame(ai_model_frame, bg="white")
        model_buttons_frame.pack(fill=tk.X, pady=10)
        
        # 添加模型按钮
        add_model_button = tk.Button(
            model_buttons_frame,
            text="添加模型",
            command=self._on_add_model,
            font=self.font_config['button'],
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )
        add_model_button.pack(side=tk.LEFT, padx=5)
        
        # 测试模型按钮
        test_model_button = tk.Button(
            model_buttons_frame,
            text="测试模型",
            command=self._on_test_model,
            font=self.font_config['button'],
            bg="#2196F3",
            fg="white",
            padx=10,
            pady=5
        )
        test_model_button.pack(side=tk.LEFT, padx=5)
        
        # 刷新模型列表按钮
        refresh_models_button = tk.Button(
            model_buttons_frame,
            text="刷新模型列表",
            command=self._refresh_ai_models,
            font=self.font_config['button'],
            bg="#FF9800",
            fg="white",
            padx=10,
            pady=5
        )
        refresh_models_button.pack(side=tk.LEFT, padx=5)
        
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
    
    def _on_ai_summary_enabled_change(self):
        """处理AI总结功能设置变更"""
        value = self.ai_summary_enabled_var.get()
        self.settings_manager.set_setting("ai_summary_enabled", value)
        log_info(f"AI总结功能设置已更新为: {value}")
    
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
                if hasattr(self, 'ai_summary_enabled_var'):
                    self.ai_summary_enabled_var.set(self.settings_manager.get_setting("ai_summary_enabled", True))
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
    
    def _load_ai_models_async(self):
        """异步加载可用的AI模型列表，避免阻塞UI"""
        def load_models():
            try:
                # 获取本地Ollama可用模型
                ollama_models = self.ai_manager._get_available_models()
                log_info(f"从Ollama获取到的模型: {ollama_models}")
                
                # 获取设置中保存的模型列表
                saved_models = self.settings_manager.get_available_ai_models()
                log_info(f"设置中保存的模型: {saved_models}")
                
                # 合并模型列表，去重
                all_models = list(set(ollama_models + saved_models))
                all_models.sort()
                log_info(f"合并后的模型列表: {all_models}")
                
                # 在主线程更新UI
                self.after(0, lambda: self._update_ai_model_combobox(all_models))
            except Exception as e:
                log_info(f"加载AI模型列表失败: {str(e)}")
                self.after(0, lambda: messagebox.showerror("加载失败", f"无法加载AI模型列表: {str(e)}"))
        
        # 在新线程中加载模型
        threading.Thread(target=load_models, daemon=True).start()
    
    def _update_ai_model_combobox(self, all_models):
        """更新AI模型下拉框"""
        # 更新下拉框选项
        self.ai_model_combo['values'] = all_models
        
        # 设置当前选中的模型
        current_model = self.settings_manager.get_ai_model()
        if current_model and current_model in all_models:
            self.ai_model_combo.set(current_model)
        elif all_models:
            # 如果当前模型不在列表中，选择第一个
            self.ai_model_combo.set(all_models[0])
        
        # 保存可用模型到设置
        self.settings_manager.set_available_ai_models(all_models)
        
        # 启用下拉框
        if all_models:
            self.ai_model_combo['state'] = "readonly"
    
    def _refresh_ai_models(self):
        """刷新AI模型列表"""
        # 禁用下拉框
        self.ai_model_combo['state'] = "disabled"
        self.ai_model_var.set("刷新中...")
        
        # 异步加载模型
        self._load_ai_models_async()
    
    def _on_add_model(self):
        """添加新的AI模型"""
        try:
            # 弹出输入框让用户输入模型名称
            model_name = simpledialog.askstring(
                "添加模型", 
                "请输入Ollama模型名称（如：gemma3n:latest）:",
                parent=self
            )
            
            if model_name and model_name.strip():
                model_name = model_name.strip()
                
                # 测试模型是否可用
                def test_and_add():
                    try:
                        # 显示加载提示
                        loading_window = tk.Toplevel(self)
                        loading_window.title("测试模型")
                        loading_window.geometry("300x100")
                        loading_window.resizable(False, False)
                        
                        # 居中显示
                        loading_window.update_idletasks()
                        x = (self.winfo_screenwidth() // 2) - (300 // 2)
                        y = (self.winfo_screenheight() // 2) - (100 // 2)
                        loading_window.geometry(f"300x100+{x}+{y}")
                        
                        loading_label = tk.Label(
                            loading_window,
                            text="正在测试模型...",
                            font=self.font_config['normal']
                        )
                        loading_label.pack(expand=True)
                        
                        # 强制更新UI
                        loading_window.update()
                        
                        # 测试模型
                        is_available = self.ai_manager._is_model_available(model_name)
                        
                        # 关闭加载窗口
                        loading_window.destroy()
                        
                        if is_available:
                            # 添加模型到设置
                            available_models = self.settings_manager.get_available_ai_models()
                            if model_name not in available_models:
                                available_models.append(model_name)
                                self.settings_manager.set_available_ai_models(available_models)
                            
                            # 更新模型列表
                            self._load_ai_models_async()
                            
                            log_info(f"成功添加AI模型: {model_name}")
                            messagebox.showinfo("添加成功", f"已成功添加并测试模型: {model_name}")
                        else:
                            messagebox.showerror("测试失败", f"模型 {model_name} 不可用，请检查模型名称和Ollama服务是否正常运行")
                    except Exception as e:
                        loading_window.destroy()
                        log_info(f"测试模型时出错: {str(e)}")
                        messagebox.showerror("测试失败", f"测试模型时出错: {str(e)}")
                
                # 在后台线程中测试模型，避免UI冻结
                threading.Thread(target=test_and_add, daemon=True).start()
        except Exception as e:
            log_info(f"添加模型时出错: {str(e)}")
            messagebox.showerror("添加失败", f"添加模型时出错: {str(e)}")
    
    def _on_test_model(self):
        """测试当前选中的模型是否可用"""
        try:
            selected_model = self.ai_model_var.get()
            if not selected_model:
                messagebox.showwarning("提示", "请先选择一个模型")
                return
            
            # 显示加载提示
            loading_window = tk.Toplevel(self)
            loading_window.title("测试模型")
            loading_window.geometry("300x100")
            loading_window.resizable(False, False)
            
            # 居中显示
            loading_window.update_idletasks()
            x = (self.winfo_screenwidth() // 2) - (300 // 2)
            y = (self.winfo_screenheight() // 2) - (100 // 2)
            loading_window.geometry(f"300x100+{x}+{y}")
            
            loading_label = tk.Label(
                loading_window,
                text="正在测试模型...",
                font=self.font_config['normal']
            )
            loading_label.pack(expand=True)
            
            # 强制更新UI
            loading_window.update()
            
            # 在后台线程中测试模型
            def test_model():
                try:
                    # 测试模型
                    is_available = self.ai_manager._is_model_available(selected_model)
                    
                    # 关闭加载窗口
                    loading_window.destroy()
                    
                    if is_available:
                        log_info(f"模型 {selected_model} 测试通过")
                        messagebox.showinfo("测试成功", f"模型 {selected_model} 可用")
                    else:
                        messagebox.showerror("测试失败", f"模型 {selected_model} 不可用")
                except Exception as e:
                    loading_window.destroy()
                    log_info(f"测试模型 {selected_model} 时出错: {str(e)}")
                    messagebox.showerror("测试失败", f"测试模型时出错: {str(e)}")
            
            threading.Thread(target=test_model, daemon=True).start()
        except Exception as e:
            log_info(f"测试模型时出错: {str(e)}")
            messagebox.showerror("测试失败", f"测试模型时出错: {str(e)}")
    
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
                # 更新AI模型相关UI
                if hasattr(self, 'ai_model_combo'):
                    self._load_ai_models_async()
                log_info("设置已重置为默认值")
                messagebox.showinfo("重置成功", "设置已成功重置为默认值")
            except Exception as e:
                log_info(f"重置设置失败: {str(e)}")
                messagebox.showerror("重置失败", f"重置设置时出错: {str(e)}")