"""
学习模式用户界面

实现学习模式的单词学习界面，包括单词展示、发音播放、掌握度标记等功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_error, log_info
from ui.components.scrollable_frame import create_scrollable_frame, refresh_mousewheel
from ui.font_config import FontConfig
from ui.theme import COLORS
from ui.components.widgets import create_button
from ui.components.toast import show_toast


class LearningPage(tk.Frame):
    """
    学习模式页面，用于用户主动学习单词
    """

    def __init__(self, parent, word_manager=None, learning_manager=None, settings_manager=None, font_config=None, **kwargs):
        """注意：调整参数顺序，将word_manager设为主要参数"""
        """
        初始化学习页面

        Args:
            parent: 父窗口组件
            learning_manager: 学习管理器实例
            word_manager: 单词管理器实例
            settings_manager: 设置管理器实例
            font_config: 字体配置字典
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.learning_manager = learning_manager
        self.word_manager = word_manager
        self.settings_manager = settings_manager
        self.font_config = FontConfig.merge(font_config)

        # 学习状态
        self.current_batch = []  # 当前学习批次的单词列表
        self.current_index = -1  # 当前单词索引
        self.current_word = None  # 当前单词
        self.is_playing = False  # 发音播放状态
        self.current_example = ""  # 当前单词例句
        self.is_example_visible = False  # 例句是否可见

        # 创建UI组件
        self._create_widgets()

        # 绑定键盘事件
        self.bind_all("<Left>", self._handle_left_key)
        self.bind_all("<Right>", self._handle_right_key)
        self.bind_all("<Return>", self._handle_return_key)

    def _create_widgets(self):
        """
        创建页面组件
        """
        # 设置页面背景
        self.configure(bg=COLORS['sidebar'])

        # 创建进度条框架
        progress_frame = tk.Frame(self, bg=COLORS['sidebar'], padx=20, pady=10)
        progress_frame.pack(fill=tk.X, side=tk.TOP)

        # 进度标签
        self.progress_label = tk.Label(
            progress_frame,
            text="进度: 0/0",
            font=("Arial", 12),
            bg=COLORS['sidebar'],
            fg=COLORS['text_primary']
        )
        self.progress_label.pack(side=tk.LEFT)

        # 批次大小选择
        batch_frame = tk.Frame(progress_frame, bg=COLORS['sidebar'])
        batch_frame.pack(side=tk.RIGHT)

        tk.Label(batch_frame, text="批次大小:", font=("Arial", 10), bg=COLORS['sidebar']).pack(side=tk.LEFT, padx=5)

        self.batch_size_var = tk.StringVar(value="10")
        batch_size_options = ["5", "10", "15", "20", "30"]
        batch_size_combo = ttk.Combobox(
            batch_frame,
            textvariable=self.batch_size_var,
            values=batch_size_options,
            width=5,
            state="readonly"
        )
        batch_size_combo.pack(side=tk.LEFT, padx=5)

        # 开始学习按钮
        self.start_button = create_button(
            batch_frame,
            text="开始学习",
            command=self.start_learning,
            style="primary",
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        # 创建单词卡片框架 - 使用通用滚动框架
        content_scroll_frame, card_frame, _, _ = create_scrollable_frame(self, padx=40, pady=20)
        content_scroll_frame.pack(fill=tk.BOTH, expand=True)
        self.content_scroll_frame = content_scroll_frame

        # 设置内部框架样式（统一卡片高程：浅底 + 细边框）
        card_frame.configure(
            bg=COLORS['surface_alt'],
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            padx=40,
            pady=60
        )

        # 单词展示标签
        self.word_label = tk.Label(
            card_frame,
            text="请点击开始学习",
            font=self.font_config.get('title', ("Arial", 48, "bold")),
            bg=COLORS['surface_alt'],
            fg=COLORS['text_primary']
        )
        self.word_label.pack(pady=(20, 5))

        # 音标标签
        self.phonetic_label = tk.Label(
            card_frame,
            text="",
            font=self.font_config.get('normal', ("Arial", 18)),
            bg=COLORS['surface_alt'],
            fg=COLORS['text_tertiary'],  # 灰色
        )
        self.phonetic_label.pack(pady=(0, 15))

        # 释义标签
        self.definition_label = tk.Label(
            card_frame,
            text="",
            font=self.font_config.get('header', ("Arial", 24)),
            bg=COLORS['surface_alt'],
            fg=COLORS['text_secondary']
        )
        self.definition_label.pack(pady=20)

        # 例句框架
        self.example_frame = tk.Frame(card_frame, bg=COLORS['surface_alt2'], bd=1, relief=tk.SUNKEN)
        self.example_frame.pack(fill=tk.X, pady=15, padx=20, side=tk.BOTTOM)

        # 例句显示标签
        self.example_label = tk.Label(
            self.example_frame,
            text="",
            font=self.font_config.get('normal', ("Arial", 12)),
            bg=COLORS['surface_alt2'],
            fg=COLORS['text_primary'],
            wraplength=600,
            justify=tk.LEFT,
            padx=15,
            pady=10
        )
        self.example_label.pack(fill=tk.X)

        # 发音播放按钮
        self.pronounce_button = create_button(
            card_frame,
            text="🔊 播放发音",
            command=self.play_pronunciation,
            style="secondary",
            font_config=self.font_config,
            state=tk.DISABLED
        )
        self.pronounce_button.pack(pady=20)

        # 创建操作按钮框架
        action_frame = tk.Frame(self, bg=COLORS['sidebar'], pady=20)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 例句按钮
        self.example_button = create_button(
            action_frame,
            text="📝 显示例句",
            command=self.toggle_example,
            style="secondary",
            font_config=self.font_config,
            state=tk.DISABLED
        )
        self.example_button.pack(side=tk.LEFT, padx=10)

        # 需复习按钮
        self.review_button = create_button(
            action_frame,
            text="需复习",
            command=self.mark_review,
            style="warning",
            font_config=self.font_config,
            state=tk.DISABLED
        )
        self.review_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=20)

        # 已掌握按钮
        self.mastered_button = create_button(
            action_frame,
            text="已掌握",
            command=self.mark_mastered,
            style="primary",
            font_config=self.font_config,
            state=tk.DISABLED
        )
        self.mastered_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=20)

    def start_learning(self):
        """
        开始学习批次
        """
        try:
            # 尝试恢复今日进度
            if self.learning_manager.load_daily_progress():
                self.current_batch = self.learning_manager.current_batch
                self.current_index = self.learning_manager.current_index
                self._show_current_word()
                self._update_progress()
                self._enable_buttons()
                return

            # 如果没有进度可恢复，开始新的学习批次
            batch_size = int(self.batch_size_var.get())

            # 获取当前激活词库信息
            active_set = self.word_manager.get_active_word_set()
            if not active_set:
                show_toast(self, "请先在词库管理中选择一个词库", kind="warning")
                return

            # 获取学习单词
            if self.learning_manager:
                self.current_batch = self.learning_manager.get_batch(batch_size)
            else:
                # 直接从word_manager获取单词
                words = self.word_manager.get_words_from_active_set()
                if not words:
                    show_toast(self, f"词库 '{active_set['name']}' 中没有单词", kind="warning")
                    return
                # 取指定数量的单词
                import random
                self.current_batch = random.sample(words, min(batch_size, len(words)))

            if not self.current_batch:
                show_toast(self, f"词库 '{active_set['name']}' 中没有可学习的单词", kind="warning")
                return

            # 开始学习第一个单词
            self.current_index = 0
            self._show_current_word()
            self._update_progress()
            self._enable_buttons()

        except Exception as e:
            messagebox.showerror("错误", f"开始学习失败: {str(e)}")

    def _show_current_word(self):
        """
        显示当前单词和释义
        """
        if 0 <= self.current_index < len(self.current_batch):
            self.current_word = self.current_batch[self.current_index]

            # 获取并显示释义
            if isinstance(self.current_word, dict):
                # 如果是字典格式（从数据库获取）
                word_text = self.current_word['word']
                definition = self.word_manager.get_translation(word_text)
                phonetic = self.current_word.get('phonetic', '')
            else:
                # 字符串格式
                word_text = self.current_word
                if self.learning_manager:
                    definition = self.learning_manager.get_word_definition(self.current_word)
                else:
                    definition = self.word_manager.get_translation(self.current_word)
                # 尝试从数据库获取音标
                try:
                    # 获取当前激活词库ID
                    if self.word_manager.active_word_set_id:
                        words = self.word_manager.get_words_from_active_set(keyword=word_text)
                        phonetic = words[0].get('phonetic', '') if words else ''
                    else:
                        phonetic = ''
                except Exception:
                    phonetic = ''

            # 更新单词标签
            self.word_label.config(text=word_text)

            # 显示音标
            if phonetic:
                self.phonetic_label.config(text=phonetic)
                self.phonetic_label.pack(pady=(0, 15))
            else:
                self.phonetic_label.config(text="")
                self.phonetic_label.pack_forget()

            # 显示释义
            self.definition_label.config(text=definition or "无释义")

            # 重置例句状态
            self.is_example_visible = False
            self.current_example = ""
            self.example_label.config(text="")
            if hasattr(self, 'example_button'):
                self.example_button.config(text="📝 显示例句")

            # 如果例句功能启用且有单词管理器，异步补全例句 + 音标
            if self.word_manager and self.settings_manager and self.settings_manager.get_setting("example_enabled", True):
                threading.Thread(target=self._fetch_details_async, daemon=True).start()

            # 单词学习时自动发音（设置项开启时，切到该词后自动播放单词发音）
            try:
                auto_pronounce = (
                    self.settings_manager
                    and self.settings_manager.get_setting("learning_auto_pronounce", True)
                    and self.settings_manager.get_setting("voice_enabled", True)
                )
                if auto_pronounce:
                    # 稍作延迟，等界面渲染完成后再播放
                    self.after(300, self.play_pronunciation)
            except Exception as e:
                log_info(f"自动发音触发失败: {str(e)}")

        # 动态内容（单词卡 / 异步例句）填充后，重新绑定滚动滚轮
        try:
            refresh_mousewheel(self.content_scroll_frame)
        except Exception:
            pass

    def _update_progress(self):
        """
        更新进度显示
        """
        if self.current_batch:
            stats = self.learning_manager.get_current_stats()
            batch_stats = stats['batch']

            progress_text = f"进度: {self.current_index + 1}/{len(self.current_batch)}  |  "
            progress_text += f"掌握: {batch_stats['mastered']}  |  "
            progress_text += f"需复习: {batch_stats['review']}"
            self.progress_label.config(text=progress_text)

    def _enable_buttons(self):
        """
        启用所有操作按钮
        """
        self.pronounce_button.config(state=tk.NORMAL)
        self.review_button.config(state=tk.NORMAL)
        self.mastered_button.config(state=tk.NORMAL)
        if hasattr(self, 'example_button'):
            self.example_button.config(state=tk.NORMAL)

    def _disable_buttons(self):
        """
        禁用所有操作按钮
        """
        self.pronounce_button.config(state=tk.DISABLED)
        self.review_button.config(state=tk.DISABLED)
        self.mastered_button.config(state=tk.DISABLED)
        if hasattr(self, 'example_button'):
            self.example_button.config(state=tk.DISABLED)

    def play_pronunciation(self):
        """
        播放当前单词发音
        """
        if self.current_word and not self.is_playing:
            # 在后台线程播放以避免阻塞
            def _play():
                try:
                    self.is_playing = True
                    # 传递单词字符串而不是完整字典
                    result = self.learning_manager.play_pronunciation(self.current_word['word'])
                except Exception as e:
                    result = False
                    try:
                        messagebox.showerror("错误", f"播放发音失败: {str(e)}")
                    except Exception:
                        pass

                def _on_done():
                    try:
                        self.is_playing = False
                        self.pronounce_button.config(text="🔊 播放发音", state=tk.NORMAL)
                    except Exception:
                        pass

                    if not result:
                        try:
                            show_toast(self, "发音播放失败，请检查网络连接", kind="warning")
                        except Exception:
                            pass

                try:
                    self.after(0, _on_done)
                except Exception:
                    _on_done()

            try:
                self.pronounce_button.config(text="🔊 播放中...", state=tk.DISABLED)
            except Exception:
                pass

            threading.Thread(target=_play, daemon=True).start()

    def mark_mastered(self):
        """
        标记当前单词为已掌握
        """
        if self.current_word:
            # 传递单词字符串而不是完整字典
            self.learning_manager.mark_mastered(self.current_word['word'])

            # 检查是否需要自动下一个单词
            if self.settings_manager and self.settings_manager.get_setting("auto_next_correct", False):
                # 延迟一小段时间再自动下一个单词，让用户有时间看到反馈
                self.after(500, self._move_to_next_word)
            else:
                # 手动下一个单词
                self._move_to_next_word()

    def mark_review(self):
        """
        标记当前单词需要复习
        """
        if self.current_word:
            # 传递单词字符串而不是完整字典
            self.learning_manager.mark_review(self.current_word['word'])

            # 检查是否需要自动下一个单词
            if self.settings_manager and self.settings_manager.get_setting("auto_next_wrong", False):
                # 延迟一小段时间再自动下一个单词，让用户有时间看到反馈
                self.after(500, self._move_to_next_word)
            else:
                # 手动下一个单词
                self._move_to_next_word()

    def _move_to_next_word(self):
        """
        移动到下一个单词
        """
        self.current_index += 1

        # 保存当前进度
        self.learning_manager.save_progress(finished=False)

        # 检查是否完成批次
        if self.current_index >= len(self.current_batch):
            self._finish_batch()
        else:
            self._show_current_word()
            self._update_progress()

    def _finish_batch(self):
        """
        完成当前学习批次
        """
        # 保存进度并标记为完成
        if self.learning_manager.save_progress(finished=True):
            # 获取统计信息
            stats = self.learning_manager.get_current_stats()
            batch_stats = stats['batch']
            summary_stats = stats['summary']

            # 显示学习总结
            summary = f"学习完成！\n\n"
            summary += f"本次学习:\n"
            summary += f"- 总学习单词: {batch_stats['total']}\n"
            summary += f"- 掌握单词: {batch_stats['mastered']}\n"
            summary += f"- 需复习单词: {batch_stats['review']}\n\n"

            summary += f"学习统计:\n"
            summary += f"- 总单词数: {summary_stats['total_words']}\n"
            summary += f"- 已学习单词: {summary_stats['learned_words']}\n"
            summary += f"- 总体正确率: {summary_stats['overall_accuracy']:.2%}\n"
            summary += f"- 今日学习: {summary_stats['today_practices']}次练习\n"

            messagebox.showinfo("学习完成", summary)
        else:
            messagebox.showerror("错误", "保存学习进度失败")

        # 重置界面
        self._reset_page()

    def _reset_page(self):
        """
        重置页面状态
        """
        self.current_batch = []
        self.current_index = -1
        self.current_word = None
        self.current_example = ""
        self.is_example_visible = False

        self.word_label.config(text="请点击开始学习")
        self.definition_label.config(text="")
        if hasattr(self, 'example_label'):
            self.example_label.config(text="")
        self._update_progress()
        self._disable_buttons()

    def _handle_left_key(self, event):
        """
        处理左方向键事件
        """
        # 只有在焦点不在输入框时才响应
        if not isinstance(event.widget, (tk.Entry, ttk.Combobox)):
            self.mark_review()

    def _handle_right_key(self, event):
        """
        处理右方向键事件
        """
        # 只有在焦点不在输入框时才响应
        if not isinstance(event.widget, (tk.Entry, ttk.Combobox)):
            self.mark_mastered()

    def _handle_return_key(self, event):
        """
        处理回车键事件
        """
        # 只有在焦点不在输入框时才响应
        if not isinstance(event.widget, (tk.Entry, ttk.Combobox)):
            self.play_pronunciation()

    def _fetch_details_async(self):
        """异步补全当前单词详情：音标 + 例句（顺带补全，一次获取更多信息）。

        直接复用 WordManager.complete_word_details_single —— 即项目原有的综合 AI
        补全功能（一次 AI 调用返回音标/释义/词性/例句的完整 JSON），而非按字段逐个补。
        仅对数据库中缺失的字段发起请求，补全后回写数据库。
        """
        log_info(f"_fetch_details_async called, current_word: {self.current_word}")
        if self.current_word and self.word_manager:
            # 确保传递的是单词字符串而不是字典
            word_str = self.current_word['word'] if isinstance(self.current_word, dict) else self.current_word
            # 调用现有 AI 补全功能：一次综合请求拿全字段
            self.word_manager.complete_word_details_single(
                word_str,
                async_mode=True,
                callback=self._on_details_fetched
            )

    def _on_details_fetched(self, attributes):
        """例句 + 音标补全完成后的回调。

        Args:
            attributes: dict，可能含 'example' / 'example_translation' / 'phonetic'
        """
        log_info(f"_on_details_fetched called, attributes keys: {list(attributes.keys()) if attributes else None}")
        try:
            if not attributes:
                return
            # 刷新音标（补齐学习页缺失的音标，并同步内存以便下次直接显示）
            phonetic = (attributes.get('phonetic') or '').strip()
            if phonetic and isinstance(self.current_word, dict):
                self.current_word['phonetic'] = phonetic
                self.master.after(0, lambda p=phonetic: (
                    self.phonetic_label.config(text=p),
                    self.phonetic_label.pack(pady=(0, 15))
                ))
            # 组装例句文本
            example = attributes.get('example', '') or ''
            example_translation = attributes.get('example_translation', '') or ''
            if example and example_translation:
                formatted = f"🌍 {example}\n📝 {example_translation}"
            elif example:
                formatted = f"🌍 {example}"
            else:
                formatted = ""
            if formatted:
                self.current_example = formatted
                if self.is_example_visible:
                    self.master.after(0, lambda f=formatted: self.example_label.config(text=f))
        except Exception as e:
            log_error(f"_on_details_fetched error: {str(e)}")

    def toggle_example(self):
        """
        切换例句显示状态
        """
        if not self.current_word:
            return

        # 确保传递的是单词字符串而不是字典
        word_str = self.current_word['word'] if isinstance(self.current_word, dict) else self.current_word

        if not self.is_example_visible:
            # 显示例句
            if self.current_example:
                # 直接显示已缓存的例句
                self.master.after(0, lambda: self.example_label.config(text=self.current_example))
                self.is_example_visible = True
                self.master.after(0, lambda: self.example_button.config(text="📝 隐藏例句"))
            elif self.word_manager and self.settings_manager and self.settings_manager.get_setting("example_enabled", True):
                # 异步补全（例句 + 音标），结果在回调 _on_details_fetched 中显示
                self.master.after(0, lambda: self.example_label.config(text="正在获取例句..."))
                self.is_example_visible = True
                self._fetch_details_async()
        else:
            # 隐藏例句
            log_info(f"toggle_example: hiding example")
            self.master.after(0, lambda: self.example_label.config(text=""))
            self.is_example_visible = False
            self.master.after(0, lambda: self.example_button.config(text="📝 显示例句"))

    def on_leave(self):
        """
        离开页面时的清理工作
        """
        # 解绑键盘事件
        self.unbind_all("<Left>")
        self.unbind_all("<Right>")
        self.unbind_all("<Return>")

        # 重置状态
        self._reset_page()
