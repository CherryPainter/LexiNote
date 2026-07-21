import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_warning
from core.ai_interface import AIManager
from ui.components.scrollable_frame import create_scrollable_frame, refresh_mousewheel
from ui.theme import COLORS
from ui.components.widgets import create_button, create_card
from ui.components.toast import show_toast
from ui.font_config import FontConfig


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

        # 字体配置：FontConfig 自带全部默认值，传入的字典仅用于覆盖
        self.font_config = FontConfig.merge(font_config)

        # 创建UI组件
        self._create_widgets()

        log_info("设置页面加载完成")

    def _create_widgets(self):
        """创建页面组件"""
        # 设置页面背景
        self.configure(bg=COLORS['sidebar'])

        # 使用统一的滚动框架实现
        scroll_frame, main_frame, _, _ = create_scrollable_frame(self, padx=30, pady=20)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        self.content_scroll_frame = scroll_frame

        # 标题
        title_label = tk.Label(
            main_frame,
            text="应用设置",
            font=self.font_config['header'],
            bg=COLORS['sidebar'],
            fg=COLORS['text_primary']
        )
        title_label.pack(pady=20)

        # 创建居中容器框架
        center_frame = tk.Frame(main_frame, bg=COLORS['sidebar'])
        center_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建设置卡片，不再设置固定宽度
        settings_card = create_card(center_frame)
        settings_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 自动切换设置
        auto_next_frame = tk.LabelFrame(
            settings_card,
            text="自动切换设置",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
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
            bg=COLORS['surface'],
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
            bg=COLORS['surface'],
            anchor=tk.W
        )
        auto_next_wrong_checkbox.pack(fill=tk.X, pady=5)

        # 新增：模块自动切换（手动/自动）控制
        module_auto_frame = tk.Frame(auto_next_frame, bg=COLORS['surface'])
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
            bg=COLORS['surface'],
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
            bg=COLORS['surface'],
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
            bg=COLORS['surface'],
            anchor=tk.W
        )
        voice_enabled_checkbox.pack(fill=tk.X, pady=5)

        # 单词学习时自动发音
        self.learning_auto_pronounce_var = tk.BooleanVar(
            value=self.settings_manager.get_setting(
                "learning_auto_pronounce", True)
        )
        learning_auto_pronounce_checkbox = tk.Checkbutton(
            features_frame,
            text="单词学习时自动发音",
            variable=self.learning_auto_pronounce_var,
            command=self._on_learning_auto_pronounce_change,
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            anchor=tk.W
        )
        learning_auto_pronounce_checkbox.pack(fill=tk.X, pady=5)

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
            bg=COLORS['surface'],
            anchor=tk.W
        )
        ai_summary_enabled_checkbox.pack(fill=tk.X, pady=5)

        # 翻译判定模式设置
        translation_frame = tk.LabelFrame(
            settings_card,
            text="翻译判定模式",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
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
            bg=COLORS['surface'],
            padx=20,
            pady=15
        )
        ai_model_frame.pack(fill=tk.X, padx=20, pady=15)

        # AI 总开关/模式：关闭 / 本地(Ollama) / 云端（渠道互斥，不跨渠道试探）
        mode_frame = tk.Frame(ai_model_frame, bg=COLORS['surface'])
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        mode_label = tk.Label(
            mode_frame, text="AI 功能模式：", font=self.font_config['normal'], bg=COLORS['surface']
        )
        mode_label.pack(anchor=tk.W, pady=(0, 5))

        self.ai_mode_var = tk.StringVar(value=self.settings_manager.get_ai_mode())

        def _on_ai_mode_change():
            mode = self.ai_mode_var.get()
            self.settings_manager.set_ai_mode(mode)
            # 同步云端开关状态，保证与旧版 cloud_ai_enabled 兼容
            self.cloud_enabled_var.set(mode == "cloud")
            self.settings_manager.set_cloud_ai_enabled(mode == "cloud")
            log_info(f"AI 模式已切换为: {mode}")
            self._apply_ai_mode_ui()
            # 切换后重新加载模型列表（按新模式只探测对应渠道）
            self._refresh_ai_models()

        for m, text in (("off", "关闭（纯本地，不使用 AI，核心学习功能不受影响）"),
                        ("local", "本地 (Ollama)"),
                        ("cloud", "云端")):
            tk.Radiobutton(
                mode_frame, text=text, value=m, variable=self.ai_mode_var,
                command=_on_ai_mode_change, font=self.font_config['normal'],
                bg=COLORS['surface'], anchor=tk.W
            ).pack(fill=tk.X, padx=10)

        # 初始化AI管理器
        self.ai_manager = AIManager()

        # 本地模型区域（仅在“本地”模式下显示）
        self.local_ai_frame = tk.LabelFrame(
            ai_model_frame,
            text="本地模型 (Ollama)",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            padx=15,
            pady=10
        )
        self.local_ai_frame.pack(fill=tk.X, pady=(0, 10))

        # 当前模型选择
        model_label = tk.Label(
            self.local_ai_frame,
            text="当前使用模型:",
            font=self.font_config['normal'],
            bg=COLORS['surface']
        )
        model_label.pack(anchor=tk.W, pady=(0, 5))

        # 模型选择下拉框
        self.ai_model_var = tk.StringVar(value="加载中...")
        self.ai_model_combo = ttk.Combobox(
            self.local_ai_frame,
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
                show_toast(self, f"已成功切换到模型: {selected_model}（重启后生效）", kind="success")

        self.ai_model_combo.bind('<<ComboboxSelected>>', _on_model_change)
        self.ai_model_combo.pack(fill=tk.X, pady=5)

        # 模型管理按钮框架
        model_buttons_frame = tk.Frame(self.local_ai_frame, bg=COLORS['surface'])
        model_buttons_frame.pack(fill=tk.X, pady=10)

        # 添加模型按钮
        add_model_button = create_button(
            model_buttons_frame,
            "添加模型",
            self._on_add_model,
            style="primary",
            font_config=self.font_config,
            padx=10,
            pady=5
        )
        add_model_button.pack(side=tk.LEFT, padx=5)

        # 测试模型按钮
        test_model_button = create_button(
            model_buttons_frame,
            "测试模型",
            self._on_test_model,
            style="secondary",
            font_config=self.font_config,
            padx=10,
            pady=5
        )
        test_model_button.pack(side=tk.LEFT, padx=5)

        # 刷新模型列表按钮
        refresh_models_button = create_button(
            model_buttons_frame,
            "刷新模型列表",
            self._refresh_ai_models,
            style="warning",
            font_config=self.font_config,
            padx=10,
            pady=5
        )
        refresh_models_button.pack(side=tk.LEFT, padx=5)

        # 云端模型设置区域
        cloud_frame = tk.LabelFrame(
            ai_model_frame,
            text="连接云端模型",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            padx=15,
            pady=10
        )
        self.cloud_frame = cloud_frame
        cloud_frame.pack(fill=tk.X, pady=(15, 5))

        # 云端启用开关
        self.cloud_enabled_var = tk.BooleanVar(
            value=self.settings_manager.get_cloud_ai_enabled()
        )
        cloud_enable_checkbox = tk.Checkbutton(
            cloud_frame,
            text="启用云端模型",
            variable=self.cloud_enabled_var,
            command=self._on_cloud_enabled_change,
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            anchor=tk.W
        )
        cloud_enable_checkbox.pack(fill=tk.X, pady=5)

        # API地址输入
        api_url_label = tk.Label(
            cloud_frame,
            text="API地址:",
            font=self.font_config['normal'],
            bg=COLORS['surface']
        )
        api_url_label.pack(anchor=tk.W, pady=(5, 0))
        self.cloud_api_url_var = tk.StringVar(
            value=self.settings_manager.get_cloud_ai_api_url()
        )
        self.cloud_api_url_entry = tk.Entry(
            cloud_frame,
            textvariable=self.cloud_api_url_var,
            font=self.font_config['normal'],
            bd=1,
            relief=tk.SOLID
        )
        self.cloud_api_url_entry.pack(fill=tk.X, pady=2)
        api_url_hint = tk.Label(
            cloud_frame,
            text="例如: https://api.openai.com/v1/chat/completions",
            font=(self.font_config['normal'][0], 9),
            bg=COLORS['surface'],
            fg=COLORS['text_tertiary']
        )
        api_url_hint.pack(anchor=tk.W)

        # API密钥输入
        api_key_label = tk.Label(
            cloud_frame,
            text="API密钥:",
            font=self.font_config['normal'],
            bg=COLORS['surface']
        )
        api_key_label.pack(anchor=tk.W, pady=(5, 0))
        self.cloud_api_key_var = tk.StringVar(
            value=self.settings_manager.get_cloud_ai_api_key()
        )
        self.cloud_api_key_entry = tk.Entry(
            cloud_frame,
            textvariable=self.cloud_api_key_var,
            font=self.font_config['normal'],
            bd=1,
            relief=tk.SOLID,
            show="*"
        )
        self.cloud_api_key_entry.pack(fill=tk.X, pady=2)

        # 模型名称输入
        cloud_model_label = tk.Label(
            cloud_frame,
            text="模型名称:",
            font=self.font_config['normal'],
            bg=COLORS['surface']
        )
        cloud_model_label.pack(anchor=tk.W, pady=(5, 0))
        self.cloud_model_name_var = tk.StringVar(
            value=self.settings_manager.get_cloud_ai_model_name()
        )
        self.cloud_model_name_entry = tk.Entry(
            cloud_frame,
            textvariable=self.cloud_model_name_var,
            font=self.font_config['normal'],
            bd=1,
            relief=tk.SOLID
        )
        self.cloud_model_name_entry.pack(fill=tk.X, pady=2)
        cloud_model_hint = tk.Label(
            cloud_frame,
            text="例如: gpt-4o, gpt-3.5-turbo, claude-3-sonnet",
            font=(self.font_config['normal'][0], 9),
            bg=COLORS['surface'],
            fg=COLORS['text_tertiary']
        )
        cloud_model_hint.pack(anchor=tk.W)

        # 云端模型操作按钮
        cloud_buttons_frame = tk.Frame(cloud_frame, bg=COLORS['surface'])
        cloud_buttons_frame.pack(fill=tk.X, pady=10)

        save_cloud_button = create_button(
            cloud_buttons_frame,
            "保存云端配置",
            self._on_save_cloud_config,
            style="primary",
            font_config=self.font_config,
            padx=10,
            pady=5
        )
        save_cloud_button.pack(side=tk.LEFT, padx=5)

        test_cloud_button = create_button(
            cloud_buttons_frame,
            "测试云端连接",
            self._on_test_cloud_connection,
            style="secondary",
            font_config=self.font_config,
            padx=10,
            pady=5
        )
        test_cloud_button.pack(side=tk.LEFT, padx=5)

        # 根据当前启用状态更新控件可用性
        self._update_cloud_ui_state()
        # 根据 AI 模式显示/隐藏 本地 与 云端 配置区域
        self._apply_ai_mode_ui()

        # 重置设置按钮，居中显示
        button_frame = tk.Frame(center_frame, bg=COLORS['sidebar'])
        button_frame.pack(pady=20)

        reset_button = create_button(
            button_frame,
            "重置为默认设置",
            self._on_reset_settings,
            style="danger",
            font_config=self.font_config,
            padx=20,
            pady=10
        )
        reset_button.pack(pady=10)

        # 保存提示
        save_hint = tk.Label(
            center_frame,
            text="设置将自动保存",
            font=(self.font_config['normal'][0], 10, 'italic'),
            bg=COLORS['sidebar'],
            fg=COLORS['text_secondary']
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

    def _on_learning_auto_pronounce_change(self):
        """处理“单词学习时自动发音”设置变更"""
        value = self.learning_auto_pronounce_var.get()
        self.settings_manager.set_setting("learning_auto_pronounce", value)
        log_info(f"单词学习时自动发音设置已更新为: {value}")

    def _apply_ai_mode_ui(self):
        """根据当前 AI 模式显示/隐藏 本地 与 云端 配置区域（渠道互斥）"""
        mode = self.ai_mode_var.get() if hasattr(self, 'ai_mode_var') else "off"
        # 同步云端开关状态，保证与旧版 cloud_ai_enabled 兼容
        if hasattr(self, 'cloud_enabled_var'):
            self.cloud_enabled_var.set(mode == "cloud")
        if hasattr(self, 'local_ai_frame'):
            self.local_ai_frame.pack_forget()
        if hasattr(self, 'cloud_frame'):
            self.cloud_frame.pack_forget()
        if mode == "local" and hasattr(self, 'local_ai_frame'):
            self.local_ai_frame.pack(fill=tk.X, pady=(0, 10))
        elif mode == "cloud" and hasattr(self, 'cloud_frame'):
            self.cloud_frame.pack(fill=tk.X, pady=(15, 5))
        # off：两者均隐藏

        # 显示/隐藏区块改变了内容高度，刷新滚轮绑定确保可滚动
        refresh_mousewheel(self.content_scroll_frame)

    def _on_cloud_enabled_change(self):
        """处理云端模型启用状态变更（同步切换 AI 模式）"""
        enabled = self.cloud_enabled_var.get()
        self.settings_manager.set_cloud_ai_enabled(enabled)
        mode = "cloud" if enabled else "off"
        self.settings_manager.set_ai_mode(mode)
        if hasattr(self, 'ai_mode_var'):
            self.ai_mode_var.set(mode)
        log_info(f"云端模型已{'启用' if enabled else '禁用'}，AI 模式: {mode}")
        self._apply_ai_mode_ui()
        self._update_cloud_ui_state()

    def _update_cloud_ui_state(self):
        """根据云端启用状态更新UI控件可用性"""
        enabled = self.cloud_enabled_var.get()
        state = tk.NORMAL if enabled else tk.DISABLED
        self.cloud_api_url_entry.config(state=state)
        self.cloud_api_key_entry.config(state=state)
        self.cloud_model_name_entry.config(state=state)

    @staticmethod
    def _normalize_url(url: str) -> str:
        """自动补全 https:// 前缀，避免 requests 报 "No scheme supplied" """
        url = (url or "").strip()
        if url and "://" not in url:
            return "https://" + url
        return url

    def _on_save_cloud_config(self):
        """保存云端模型配置"""
        try:
            enabled = self.cloud_enabled_var.get()
            # 自动补全 https:// 前缀，避免用户漏写协议头
            api_url = self._normalize_url(self.cloud_api_url_var.get())
            api_key = self.cloud_api_key_var.get().strip()
            model_name = self.cloud_model_name_var.get().strip()

            # 如果启用云端，验证必填项
            if enabled:
                if not api_url:
                    show_toast(self, "请填写API地址", kind="warning")
                    return
                if not api_key:
                    show_toast(self, "请填写API密钥", kind="warning")
                    return
                if not model_name:
                    show_toast(self, "请填写模型名称", kind="warning")
                    return

            # 保存配置
            success = self.settings_manager.save_cloud_ai_config(
                enabled, api_url, api_key, model_name
            )

            if success:
                log_info("云端模型配置已保存")
                show_toast(self, "云端模型配置已保存", kind="success")
                # 立即刷新 AIManager 单例配置，使云端/本地切换在已运行的程序中即时生效
                try:
                    # 保存时确保 AI 模式与云端开关一致
                    self.settings_manager.set_ai_mode("cloud" if enabled else "off")
                    if hasattr(self, 'ai_mode_var'):
                        self.ai_mode_var.set("cloud" if enabled else "off")
                    self._apply_ai_mode_ui()
                    self.ai_manager._load_cloud_config()
                    self.ai_manager.ai_mode = self.settings_manager.get_ai_mode()
                    if enabled and self.ai_manager.cloud_model_name:
                        # 让单例当前模型对齐到云端模型（异步执行，避免网络探测卡住界面）
                        threading.Thread(
                            target=self.ai_manager.set_model,
                            args=(self.ai_manager.cloud_model_name,),
                            daemon=True
                        ).start()
                except Exception as e:
                    log_warning(f"刷新 AIManager 云端配置失败: {str(e)}")
                # 刷新模型列表，让云端模型出现在下拉框中
                self._refresh_ai_models()
            else:
                messagebox.showerror("保存失败", "保存云端配置时出错")
        except Exception as e:
            log_info(f"保存云端配置失败: {str(e)}")
            messagebox.showerror("保存失败", f"保存云端配置时出错: {str(e)}")

    def _on_test_cloud_connection(self):
        """测试云端模型连接"""
        try:
            # 自动补全 https:// 前缀，避免用户漏写协议头
            api_url = self._normalize_url(self.cloud_api_url_var.get())
            api_key = self.cloud_api_key_var.get().strip()
            model_name = self.cloud_model_name_var.get().strip()

            if not api_url or not api_key or not model_name:
                show_toast(self, "请填写完整的API地址、密钥和模型名称", kind="warning")
                return

            # 显示加载提示
            loading_window = tk.Toplevel(self)
            loading_window.title("测试云端连接")
            loading_window.geometry("300x100")
            loading_window.resizable(False, False)
            loading_window.update_idletasks()
            x = (self.winfo_screenwidth() // 2) - (300 // 2)
            y = (self.winfo_screenheight() // 2) - (100 // 2)
            loading_window.geometry(f"300x100+{x}+{y}")

            loading_label = tk.Label(
                loading_window,
                text="正在测试云端连接...",
                font=self.font_config['normal']
            )
            loading_label.pack(expand=True)
            loading_window.update()

            def do_test():
                try:
                    import requests
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": model_name,
                        "messages": [{"role": "user", "content": "hello"}],
                        "max_tokens": 5
                    }
                    response = requests.post(api_url, headers=headers, json=data, timeout=15)
                    loading_window.destroy()

                    if response.status_code == 200:
                        log_info(f"云端模型 {model_name} 连接测试成功")
                        self.after(0, lambda: show_toast(self, f"云端模型 {model_name} 连接成功！", kind="success"))
                    else:
                        log_info(f"云端模型连接测试失败，状态码: {response.status_code}")
                        messagebox.showerror("测试失败", f"连接失败，状态码: {response.status_code}\n请检查配置信息")
                except Exception as e:
                    loading_window.destroy()
                    log_info(f"云端模型连接测试失败: {str(e)}")
                    messagebox.showerror("测试失败", f"连接测试失败: {str(e)}")

            threading.Thread(target=do_test, daemon=True).start()
        except Exception as e:
            log_info(f"测试云端连接时出错: {str(e)}")
            messagebox.showerror("测试失败", f"测试云端连接时出错: {str(e)}")

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
                if hasattr(self, 'learning_auto_pronounce_var'):
                    self.learning_auto_pronounce_var.set(self.settings_manager.get_setting("learning_auto_pronounce", True))
                if hasattr(self, 'ai_summary_enabled_var'):
                    self.ai_summary_enabled_var.set(self.settings_manager.get_setting("ai_summary_enabled", True))
                if hasattr(self, 'tts_provider_var'):
                    self.tts_provider_var.set(self.settings_manager.get_setting("tts_provider", "edge-tts"))
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
                # 更新云端模型UI
                if hasattr(self, 'cloud_enabled_var'):
                    self.cloud_enabled_var.set(self.settings_manager.get_cloud_ai_enabled())
                if hasattr(self, 'cloud_api_url_var'):
                    self.cloud_api_url_var.set(self.settings_manager.get_cloud_ai_api_url())
                if hasattr(self, 'cloud_api_key_var'):
                    self.cloud_api_key_var.set(self.settings_manager.get_cloud_ai_api_key())
                if hasattr(self, 'cloud_model_name_var'):
                    self.cloud_model_name_var.set(self.settings_manager.get_cloud_ai_model_name())
                if hasattr(self, '_update_cloud_ui_state'):
                    self._update_cloud_ui_state()
                # 更新AI模型相关UI
                if hasattr(self, 'ai_model_combo'):
                    self._load_ai_models_async()
                # 重置 AI 模式（默认关闭），并同步模式选择器与区域显示
                if hasattr(self, 'ai_mode_var'):
                    self.ai_mode_var.set(self.settings_manager.get_ai_mode())
                if hasattr(self, '_apply_ai_mode_ui'):
                    self._apply_ai_mode_ui()
                log_info("设置已重置为默认值")
                show_toast(self, "设置已成功重置为默认值", kind="success")
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
            show_toast(self, "请输入有效的数字", kind="warning")

    def _load_ai_models_async(self):
        """异步加载可用的AI模型列表，避免阻塞UI

        仅在「本地(Ollama)」模式下才探测并填充本地模型下拉框。
        「关闭」与「云端」模式不触碰任何渠道、不重写 available_ai_models，
        避免无谓的联网探测和把写死的旧模型列表重新提交回设置。
        """
        if self.settings_manager.get_ai_mode() != "local":
            log_info("AI 功能非本地模式，跳过本地模型列表加载（不探测、不重写模型列表）")
            self.after(0, lambda: self.ai_model_combo.config(state="disabled"))
            return

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
                            self.after(0, lambda: show_toast(self, f"已成功添加并测试模型: {model_name}", kind="success"))
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
                show_toast(self, "请先选择一个模型", kind="warning")
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
                        self.after(0, lambda: show_toast(self, f"模型 {selected_model} 可用", kind="success"))
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
