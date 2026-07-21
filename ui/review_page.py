import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_error
from ui.font_config import FontConfig
from ui.theme import COLORS
from ui.components.widgets import create_button
from ui.components.toast import show_toast


class ReviewPage(tk.Frame):
    """单词复习页面"""

    def __init__(self, parent, settings_manager=None, word_manager=None, font_config=None, audio_player=None, **kwargs):
        """初始化复习页面"""
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.settings_manager = settings_manager
        self.word_manager = word_manager
        self.font_config = FontConfig.merge(font_config)
        self.audio_player = audio_player
        # 添加音频可用性标志
        self.audio_available = self.audio_player is not None

        # 注册设置监听器
        if self.settings_manager:
            self.settings_manager.register_listener(
                'auto_mode_review',
                self._on_auto_mode_review_change
            )

        # 当前显示模式
        self.show_translation = False
        self.is_example_visible = False
        self.current_example = ""

        # 当前单词列表和索引
        self.review_words = []
        self.current_index = 0

        # 熟悉度相关数据
        self.word_familiarity = {}
        self.session_stats = {"total": 0, "familiar": 0, "difficult": 0}
        self.familiar_threshold = 0.8  # 熟悉度阈值

        # 创建UI
        self._create_ui()

        # 加载熟悉度数据
        self._load_familiarity_data()

        # 加载单词列表
        self._load_words()
        # 注册设置监听器（用于未来扩展，使得运行时切换生效）
        try:
            self.settings_manager.register_listener('auto_mode_review', self._on_auto_mode_review_change)
        except Exception:
            pass

    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        self.main_frame = tk.Frame(self, bg=COLORS['surface'])
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)

        # 标题
        title_label = tk.Label(
            self.main_frame,
            text="单词复习",
            font=self.font_config['header'],
            bg=COLORS['surface']
        )
        title_label.pack(pady=20)

        # 过滤选项
        filter_frame = tk.Frame(self.main_frame, bg=COLORS['surface'])
        filter_frame.pack(pady=10, fill=tk.X)

        self.filter_var = tk.StringVar(value="all")

        tk.Label(filter_frame, text="过滤:", font=self.font_config['normal'], bg=COLORS['surface']).pack(side=tk.LEFT, padx=10)

        all_radio = tk.Radiobutton(
            filter_frame,
            text="全部单词",
            variable=self.filter_var,
            value="all",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            command=self._on_filter_change
        )
        all_radio.pack(side=tk.LEFT, padx=10)

        familiar_radio = tk.Radiobutton(
            filter_frame,
            text="熟词",
            variable=self.filter_var,
            value="familiar",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            command=self._on_filter_change
        )
        familiar_radio.pack(side=tk.LEFT, padx=10)

        difficult_radio = tk.Radiobutton(
            filter_frame,
            text="难词",
            variable=self.filter_var,
            value="difficult",
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            command=self._on_filter_change
        )
        difficult_radio.pack(side=tk.LEFT, padx=10)

        # 单词卡片
        self.card_frame = tk.Frame(self.main_frame, bg=COLORS['surface_alt'], bd=3, relief=tk.RAISED)
        self.card_frame.pack(pady=30, fill=tk.BOTH, expand=True, padx=50)

        # 单词和音标显示
        self.word_var = tk.StringVar()
        self.word_label = tk.Label(
            self.card_frame,
            textvariable=self.word_var,
            font=self.font_config['header'],
            bg=COLORS['surface_alt'],
            wraplength=600
        )
        self.word_label.pack(pady=(40, 5))

        self.phonetic_var = tk.StringVar()
        self.phonetic_label = tk.Label(
            self.card_frame,
            textvariable=self.phonetic_var,
            font=self.font_config['normal'],
            bg=COLORS['surface_alt'],
            fg=COLORS['text_tertiary'],  # 灰色
            wraplength=600
        )
        self.phonetic_label.pack(pady=(0, 10))

        # 翻译显示
        self.translation_var = tk.StringVar()
        self.translation_label = tk.Label(
            self.card_frame,
            textvariable=self.translation_var,
            font=self.font_config['normal'],
            bg=COLORS['surface_alt'],
            fg=COLORS['text_secondary'],
            wraplength=600
        )
        self.translation_label.pack(pady=20)

        # 按钮区域
        buttons_frame = tk.Frame(self.main_frame, bg=COLORS['surface'])
        buttons_frame.pack(pady=30)

        # 控制按钮
        control_buttons_frame = tk.Frame(buttons_frame, bg=COLORS['surface'])
        control_buttons_frame.pack(side=tk.LEFT)

        self.prev_button = create_button(
            control_buttons_frame,
            text="◀ 上一个",
            command=self._prev_word,
            style="secondary",
            font_config=self.font_config,
            width=12,
            height=2
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.show_button = create_button(
            control_buttons_frame,
            text="👁️ 显示翻译",
            command=self._toggle_translation,
            style="warning",
            font_config=self.font_config,
            width=12,
            height=2
        )
        self.show_button.pack(side=tk.LEFT, padx=5)

        self.next_button = create_button(
            control_buttons_frame,
            text="下一个 ▶",
            command=self._next_word,
            style="secondary",
            font_config=self.font_config,
            width=12,
            height=2
        )
        self.next_button.pack(side=tk.LEFT, padx=5)

        # 发音和操作按钮
        action_buttons_frame = tk.Frame(buttons_frame, bg=COLORS['surface'])
        action_buttons_frame.pack(side=tk.LEFT, padx=20)

        self.pronounce_button = create_button(
            action_buttons_frame,
            text="🔊 发音",
            command=self._play_pronunciation,
            style="primary",
            font_config=self.font_config,
            width=10,
            height=2
        )
        self.pronounce_button.pack(side=tk.LEFT, padx=5)

        self.familiar_button = create_button(
            action_buttons_frame,
            text="✅ 标记熟悉",
            command=self._mark_as_familiar,
            style="primary",
            font_config=self.font_config,
            width=12,
            height=2
        )
        self.familiar_button.pack(side=tk.LEFT, padx=5)

        self.difficult_button = create_button(
            action_buttons_frame,
            text="❌ 标记困难",
            command=self._mark_as_difficult,
            style="danger",
            font_config=self.font_config,
            width=12,
            height=2
        )
        self.difficult_button.pack(side=tk.LEFT, padx=5)

        # 例句按钮
        self.example_button = create_button(
            action_buttons_frame,
            text="📝 显示例句",
            command=self._toggle_example,
            style="secondary",
            font_config=self.font_config,
            width=12,
            height=2
        )
        self.example_button.pack(side=tk.LEFT, padx=5)

        # 复习总结按钮
        summary_frame = tk.Frame(self.main_frame, bg=COLORS['surface'])
        summary_frame.pack(pady=10)

        self.summary_button = create_button(
            summary_frame,
            text="📊 复习总结",
            command=self._show_summary,
            style="warning",
            font_config=self.font_config,
            width=15,
            height=2
        )
        self.summary_button.pack()

        # 进度信息
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(
            self.main_frame,
            textvariable=self.progress_var,
            font=self.font_config['normal'],
            bg=COLORS['surface'],
            fg=COLORS['text_secondary']
        )
        self.progress_label.pack(pady=10)

    def _load_words(self):
        """加载单词列表（重构版本，使用数据库结构）"""
        filter_type = self.filter_var.get()

        try:
            # 使用新的方法获取复习单词，直接从数据库获取完整信息
            words_data = self.word_manager.get_words_for_review(filter_type=filter_type)

            # 转换为复习页面需要的格式，保留完整数据以便后续使用
            self.review_words = []
            for word_data in words_data:
                # 确保必要字段存在
                word = word_data.get('word', '')
                # 通过word_manager获取格式化的翻译
                translation = self.word_manager.get_translation(word)
                # 保存完整的单词数据，而不仅仅是单词和翻译
                self.review_words.append((word, translation, word_data))

            log_info(f"加载复习单词完成: 类型={filter_type}, 数量={len(self.review_words)}")

        except Exception as e:
            log_error(f"加载复习单词失败: {str(e)}")
            # 发生错误时使用空列表
            self.review_words = []

        # 重置索引和状态
        self.current_index = 0
        self.show_translation = False
        self.is_example_visible = False
        self.current_example = ""

        # 更新显示
        self._update_word_display()
        self._update_progress()

        # 启用总结按钮
        self.summary_button.config(state=tk.NORMAL if self.review_words else tk.DISABLED)

    def _update_word_display(self):
        """更新单词显示（重构版本，使用完整单词数据）"""
        if not self.review_words:
            self.word_var.set("没有找到单词")
            self.translation_var.set("")
            self.show_button.config(state=tk.DISABLED)
            self.pronounce_button.config(state=tk.DISABLED)
            # 检查mark_button是否存在
            if hasattr(self, 'mark_button'):
                self.mark_button.config(state=tk.DISABLED)
            self.example_button.config(state=tk.DISABLED)
            return

        # 启用按钮
        self.show_button.config(state=tk.NORMAL)
        self.pronounce_button.config(state=tk.NORMAL)
        # 检查mark_button是否存在
        if hasattr(self, 'mark_button'):
            self.mark_button.config(state=tk.NORMAL)
        self.example_button.config(state=tk.NORMAL)

        # 显示当前单词和数据
        word, translation, word_data = self.review_words[self.current_index]

        # 直接从word_data获取例句和例句翻译
        example = word_data.get('example', '')
        example_translation = word_data.get('example_translation', '')
        self.current_example = example
        self.current_example_translation = example_translation

        # 显示单词和音标
        self.word_var.set(word)
        if 'phonetic' in word_data and word_data['phonetic']:
            self.phonetic_var.set(word_data['phonetic'])
            self.phonetic_label.pack(pady=(0, 10))
        else:
            self.phonetic_var.set("")
            self.phonetic_label.pack_forget()

        # 根据模式显示翻译和例句
        if self.show_translation:
            display_text = ""
            # 处理翻译显示 - 格式化列表或JSON字符串
            if translation:
                import json
                # 处理可能的JSON字符串
                if isinstance(translation, str) and (translation.startswith('[') or translation.startswith('{')):
                    try:
                        parsed = json.loads(translation)
                        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
                            # 处理多词性多义项结构
                            formatted_parts = []
                            for item in parsed:
                                tag = item.get('tag', '')
                                meanings = item.get('meaning_zh', [])
                                if meanings:
                                    if tag:
                                        formatted_parts.append(f"{tag}：{'；'.join(meanings)}")
                                    else:
                                        formatted_parts.append('；'.join(meanings))
                            translation_text = '\n'.join(formatted_parts)
                        elif isinstance(parsed, list):
                            translation_text = "、".join(parsed)
                        else:
                            translation_text = str(parsed)
                    except json.JSONDecodeError:
                        translation_text = translation
                elif isinstance(translation, list):
                    translation_text = "、".join(translation)
                else:
                    translation_text = translation
                display_text += f"翻译: {translation_text}"

            # 如果有英文解释，也显示出来
            if 'meaning_en' in word_data and word_data['meaning_en']:
                meaning_en = word_data['meaning_en']
                if isinstance(meaning_en, list):
                    meaning_en_text = "、".join(meaning_en)
                else:
                    meaning_en_text = meaning_en
                display_text += f"\n英文解释: {meaning_en_text}"

            # 显示例句
            if self.is_example_visible and example:
                display_text += "\n\n📝 例句:"
                if example_translation:
                    display_text += f"\n🌍 {example}\n📝 {example_translation}"
                elif '|' in example:  # 处理旧格式
                    parts = example.split('|', 1)
                    if len(parts) == 2:
                        display_text += f"\n🌍 {parts[0].strip()}\n📝 {parts[1].strip()}"
                    else:
                        display_text += f"\n🌍 {example}"
                else:
                    display_text += f"\n🌍 {example}"

            # 显示熟练度
            if 'proficiency' in word_data:
                proficiency = word_data['proficiency'] or 0.0
                display_text += f"\n\n📊 当前熟练度: {proficiency:.2f}"

            self.translation_var.set(display_text)
            self.show_button.config(text="🙈 隐藏翻译")
        else:
            if self.is_example_visible and example:
                if example_translation:
                    self.translation_var.set(f"📝 例句: {example}\n📝 翻译: {example_translation}")
                elif '|' in example:  # 处理旧格式
                    parts = example.split('|', 1)
                    if len(parts) == 2:
                        self.translation_var.set(f"📝 例句: {parts[0].strip()}\n📝 翻译: {parts[1].strip()}")
                    else:
                        self.translation_var.set(f"📝 例句: {example}")
                else:
                    self.translation_var.set(f"📝 例句: {example}")
            else:
                self.translation_var.set("点击显示按钮查看翻译")
            self.show_button.config(text="👁️ 显示翻译")

        # 更新例句按钮文本
        if self.is_example_visible:
            self.example_button.config(text="📝 隐藏例句")
        else:
            self.example_button.config(text="📝 显示例句")

    def _update_progress(self):
        """更新进度信息"""
        if self.review_words:
            self.progress_var.set(f"{self.current_index + 1} / {len(self.review_words)}")
        else:
            self.progress_var.set("0 / 0")

        # 更新按钮状态
        self.prev_button.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_index < len(self.review_words) - 1 else tk.DISABLED)

    def _toggle_translation(self):
        """切换翻译显示状态"""
        self.show_translation = not self.show_translation
        self._update_word_display()

    def _prev_word(self):
        """显示上一个单词（重构版本）"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_translation = False
            self.is_example_visible = False
            self._update_word_display()
            self._update_progress()
            log_info(f"显示上一个单词: {self.review_words[self.current_index][0]}")

    def _toggle_example(self):
        """切换例句显示状态"""
        if not self.review_words:
            return

        if not self.is_example_visible:
            # 显示例句
            word, translation, word_data = self.review_words[self.current_index]

            # 如果当前没有例句，使用WordManager的AI补全功能获取例句
            if not self.current_example and self.word_manager and self.settings_manager and self.settings_manager.get_setting("example_enabled", True):
                # 异步获取例句
                def on_example_ready(example):
                    try:
                        # 更新当前例句
                        self.current_example = example
                        # 更新显示
                        self._update_word_display()
                    except Exception as e:
                        log_error(f"例句更新失败: {str(e)}")

                try:
                    # 调用统一的词库管理AI补全模块获取例句
                    self.word_manager.get_word_example(
                        word,
                        async_mode=True,
                        callback=on_example_ready
                    )
                except Exception as e:
                    log_error(f"获取例句失败: {str(e)}")

        # 切换显示状态
        self.is_example_visible = not self.is_example_visible
        self._update_word_display()

        # 模块级别的自动/手动设置控制是否允许自动切换
        try:
            module_mode = self.settings_manager.get_setting('auto_mode_review', 'manual') if self.settings_manager else 'manual'
        except Exception:
            module_mode = 'manual'

        auto_next = False
        if module_mode == 'auto':
            auto_next = self.settings_manager.get_setting("auto_next_example", False)

        if auto_next and self.is_example_visible:
            # 延迟一段时间后自动切换到下一个单词
            self.after(self.settings_manager.get_setting("auto_next_delay", 2000), self._next_word)



    def _next_word(self):
        """显示下一个单词（重构版本）"""
        if self.current_index < len(self.review_words) - 1:
            self.current_index += 1
            self.show_translation = False
            self.is_example_visible = False
            self._update_word_display()
            self._update_progress()
            log_info(f"显示下一个单词: {self.review_words[self.current_index][0]}")

    def _on_auto_mode_review_change(self, key, value):
        """设置变更回调：自动/手动切换变动时更新 UI 行为"""
        try:
            # 检查当前页面是否已初始化完成
            if not hasattr(self, 'next_button'):
                return

            if value == 'auto':
                # 自动模式，根据是否显示了例句决定是否显示下一个按钮
                if self.is_example_visible:
                    # 例句已显示且是自动模式，隐藏按钮
                    try:
                        self.next_button.pack_forget()
                        # 设置延迟自动下一个
                        delay = self.settings_manager.get_setting("auto_next_delay", 1000)
                        self.after(delay, self._next_word)
                    except Exception:
                        pass
            else:
                # 手动模式时，如果例句已显示则显示下一个按钮
                if self.is_example_visible:
                    try:
                        self.next_button.pack(side=tk.LEFT, padx=10)
                    except Exception:
                        pass
        except Exception:
            pass

    def _play_pronunciation(self):
        """播放单词发音"""
        if not self.review_words:
            return
        word, _, _ = self.review_words[self.current_index]

        # 在后台线程播放，避免阻塞UI
        def _play():
            try:
                if self.audio_player is not None:
                    result = self.audio_player.play_pronunciation(word)
                else:
                    result = False
                    log_error("audio_player为None，无法播放发音")
            except Exception as e:
                log_error(f"播放线程异常: {str(e)}")
                result = False

            def _on_done():
                try:
                    self.pronounce_button.config(state=tk.NORMAL, text="🔊 发音")
                except Exception:
                    pass

                if not result and self.audio_available:
                    messagebox.showerror("播放失败", "无法播放单词发音，请检查网络连接。")
                else:
                    try:
                        self.progress_var.set(f"{self.current_index + 1} / {len(self.review_words)}")
                    except Exception:
                        pass

            try:
                self.main_frame.after(0, _on_done)
            except Exception:
                _on_done()

        try:
            self.pronounce_button.config(state=tk.DISABLED, text="🔊 播放中...")
            # 移除对未定义变量status_var的引用
        except Exception as e:
            log_error(f"更新发音按钮状态失败: {str(e)}")

        threading.Thread(target=_play, daemon=True).start()

    def _mark_as_important(self):
        """标记为重点单词（增加权重）"""
        if not self.review_words:
            return

        word, _ = self.review_words[self.current_index]

        try:
            # 优先使用word_manager的公开方法
            if hasattr(self.word_manager, 'update_word_weight'):
                # 使用update_word_weight方法更新权重
                self.word_manager.update_word_weight(word, True, 0)  # True表示认识，增加权重
            elif hasattr(self.word_manager, 'word_weights') and hasattr(self.word_manager, '_save_data'):
                # 如果没有公开方法但有权重字典，尝试直接修改
                if word in self.word_manager.word_weights:
                    self.word_manager.word_weights[word] += 1.0
                else:
                    self.word_manager.word_weights[word] = 2.0

                # 保存数据
                if hasattr(self.word_manager, 'word_weights_file'):
                    self.word_manager._save_data(
                        self.word_manager.word_weights_file,
                        {word: self.word_manager.word_weights[word]}
                    )

            show_toast(self, f"已将 '{word}' 标记为重点单词", kind="success")
            log_info(f"标记重点单词: {word}")
        except Exception as e:
            log_error(f"标记重点单词失败: {str(e)}")
            messagebox.showerror("错误", f"无法将 '{word}' 标记为重点单词: {str(e)}")

    def _on_filter_change(self):
        """过滤条件改变时重新加载单词"""
        self.show_translation = False
        self.is_example_visible = False
        self._load_words()

    def _load_familiarity_data(self):
        """加载单词熟悉度数据"""
        try:
            # 尝试从word_manager获取熟悉度数据
            if hasattr(self.word_manager, 'get_word_familiarity'):
                self.word_familiarity = self.word_manager.get_word_familiarity()
            else:
                # 如果word_manager没有提供熟悉度数据，使用空字典
                self.word_familiarity = {}
        except Exception as e:
            log_error(f"加载熟悉度数据失败: {str(e)}")
            self.word_familiarity = {}

    def _mark_as_familiar(self):
        """将当前单词标记为熟悉（重构版本，使用数据库中的proficiency字段）"""
        if not self.review_words:
            return

        word, _, word_data = self.review_words[self.current_index]

        # 获取当前熟练度
        current_proficiency = word_data.get('proficiency', 0.0)
        # 增加熟练度（最大到1.0）
        new_proficiency = min(current_proficiency + 0.2, 1.0)

        # 更新本地熟悉度数据
        self.word_familiarity[word] = new_proficiency
        self.session_stats["familiar"] += 1

        # 更新word_data中的值
        word_data['proficiency'] = new_proficiency

        # 调用word_manager更新数据库中的熟悉度
        try:
            self.word_manager.update_word_familiarity(word, new_proficiency)
            log_info(f"标记熟悉单词: {word}, 熟练度从 {current_proficiency:.2f} 提升到 {new_proficiency:.2f}")

            # 显示提示
            self.translation_var.set(f"✓ 已将 '{word}' 标记为熟悉\n\n📊 熟练度提升至: {new_proficiency:.2f}")
        except Exception as e:
            log_error(f"更新单词熟悉度失败: {str(e)}")
            self.translation_var.set(f"✓ 已将 '{word}' 标记为熟悉，但数据库更新失败")

        # 检查是否需要自动下一个单词
        try:
            auto_next = self.settings_manager.get_setting("auto_next_familiar", False) if self.settings_manager else False
            if auto_next:
                delay = self.settings_manager.get_setting("auto_next_delay", 1000) if self.settings_manager else 1000
                self.after(delay, self._next_word)
        except Exception:
            pass

    def _mark_as_difficult(self):
        """将当前单词标记为困难（重构版本，使用数据库中的proficiency字段）"""
        if not self.review_words:
            return

        word, _, word_data = self.review_words[self.current_index]

        # 获取当前熟练度
        current_proficiency = word_data.get('proficiency', 1.0)
        # 降低熟练度（最小到0.0）
        new_proficiency = max(current_proficiency - 0.3, 0.0)

        # 更新本地熟悉度数据
        self.word_familiarity[word] = new_proficiency
        self.session_stats["difficult"] += 1

        # 更新word_data中的值
        word_data['proficiency'] = new_proficiency

        # 调用word_manager更新数据库中的熟悉度
        try:
            self.word_manager.update_word_familiarity(word, new_proficiency)
            log_info(f"标记困难单词: {word}, 熟练度从 {current_proficiency:.2f} 降低到 {new_proficiency:.2f}")

            # 显示提示
            self.translation_var.set(f"❌ 已将 '{word}' 标记为困难\n\n📊 熟练度调整为: {new_proficiency:.2f}")
        except Exception as e:
            log_error(f"更新单词熟悉度失败: {str(e)}")
            self.translation_var.set(f"❌ 已将 '{word}' 标记为困难，但数据库更新失败")

        # 检查是否需要自动下一个单词
        try:
            auto_next = self.settings_manager.get_setting("auto_next_difficult", False) if self.settings_manager else False
            if auto_next:
                delay = self.settings_manager.get_setting("auto_next_delay", 1000) if self.settings_manager else 1000
                self.after(delay, self._next_word)
        except Exception as e:
            log_error(f"自动下一个单词设置检查失败: {str(e)}")

        # 如果word_manager支持update_word_weight，也更新单词权重
        if hasattr(self.word_manager, 'update_word_weight'):
            try:
                # 因为这里没有时间统计，使用0作为默认值
                self.word_manager.update_word_weight(word, False, 0)  # False表示不认识，增加权重
            except Exception as e:
                log_error(f"更新单词权重失败: {str(e)}")

    def _show_summary(self):
        """显示复习总结"""
        try:
            # 创建新窗口显示总结
            summary_window = tk.Toplevel(self)
            summary_window.title("复习总结")
            summary_window.geometry("500x400")
            summary_window.configure(bg=COLORS['surface'])
            if self.parent:
                summary_window.transient(self.parent)
            summary_window.grab_set()

            # 标题
            title_label = tk.Label(
                summary_window,
                text="复习总结",
                font=self.font_config['header'],
                bg=COLORS['surface']
            )
            title_label.pack(pady=20)

            # 统计信息框架
            stats_frame = tk.Frame(summary_window, bg=COLORS['surface'])
            stats_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)

            # 总单词数
            total_words = len(self.review_words)
            tk.Label(
                stats_frame,
                text=f"本次复习单词总数: {total_words}",
                font=self.font_config['normal'],
                bg=COLORS['surface']
            ).pack(anchor='w', pady=5)

            # 熟悉单词数
            familiar_count = self.session_stats["familiar"]
            familiar_percent = (familiar_count / total_words * 100) if total_words > 0 else 0
            tk.Label(
                stats_frame,
                text=f"熟悉单词: {familiar_count} ({familiar_percent:.1f}%)",
                font=self.font_config['normal'],
                bg=COLORS['surface'],
                fg=COLORS['primary']
            ).pack(anchor='w', pady=5)

            # 困难单词数
            difficult_count = self.session_stats["difficult"]
            difficult_percent = (difficult_count / total_words * 100) if total_words > 0 else 0
            tk.Label(
                stats_frame,
                text=f"困难单词: {difficult_count} ({difficult_percent:.1f}%)",
                font=self.font_config['normal'],
                bg=COLORS['surface'],
                fg=COLORS['error']
            ).pack(anchor='w', pady=5)

            # 获取熟悉度低于阈值的单词列表
            difficult_words = [word for word, familiarity in self.word_familiarity.items()
                              if familiarity < self.familiar_threshold]

            # 复习建议
            tk.Label(
                stats_frame,
                text="复习建议:",
                font=self.font_config['normal'],
                bg=COLORS['surface'],
                fg=COLORS['info']
            ).pack(anchor='w', pady=(15, 5))

            if not difficult_words:
                advice = "太棒了！所有单词都掌握得很好。"
            elif len(difficult_words) <= 5:
                advice = f"建议重点复习这些单词: {', '.join(difficult_words)}"
            else:
                advice = f"建议使用'难词'模式进行针对性复习，共有{len(difficult_words)}个单词需要加强。"

            advice_label = tk.Label(
                stats_frame,
                text=advice,
                font=self.font_config['normal'],
                bg=COLORS['surface'],
                fg=COLORS['text_primary'],
                wraplength=400,
                justify=tk.LEFT
            )
            advice_label.pack(anchor='w', pady=5)

            # 按钮
            button_frame = tk.Frame(summary_window, bg=COLORS['surface'])
            button_frame.pack(pady=20)

            create_button(
                button_frame,
                text="关闭",
                command=summary_window.destroy,
                style="ghost",
                font_config=self.font_config,
                width=15,
                height=2
            ).pack(pady=10)

        except Exception as e:
            log_error(f"显示复习总结失败: {str(e)}")
            messagebox.showerror("错误", f"无法显示复习总结: {str(e)}")
