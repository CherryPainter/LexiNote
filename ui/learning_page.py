"""
学习模式用户界面

实现学习模式的单词学习界面，包括单词展示、发音播放、掌握度标记等功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional
import threading
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_wrong_word
from audio_player import AudioPlayer
from ui.components.scrollable_frame import create_scrollable_frame


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
        self.font_config = font_config or {'title': ("Arial", 48, "bold"), 'header': ("Arial", 24), 'normal': ("Arial", 12), 'button': ("Arial", 12)}
        
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
        self.configure(bg="#f0f0f0")
        
        # 创建进度条框架
        progress_frame = tk.Frame(self, bg="#f0f0f0", padx=20, pady=10)
        progress_frame.pack(fill=tk.X, side=tk.TOP)
        
        # 进度标签
        self.progress_label = tk.Label(
            progress_frame, 
            text="进度: 0/0", 
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#333333"
        )
        self.progress_label.pack(side=tk.LEFT)
        
        # 批次大小选择
        batch_frame = tk.Frame(progress_frame, bg="#f0f0f0")
        batch_frame.pack(side=tk.RIGHT)
        
        tk.Label(batch_frame, text="批次大小:", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
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
        self.start_button = tk.Button(
            batch_frame,
            text="开始学习",
            command=self.start_learning,
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # 创建单词卡片框架 - 使用通用滚动框架
        content_scroll_frame, card_frame, _, _ = create_scrollable_frame(self, padx=40, pady=20)
        content_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置内部框架样式
        card_frame.configure(
            bg="white",
            relief=tk.RAISED,
            bd=2,
            padx=40,
            pady=60
        )
        
        # 单词展示标签
        self.word_label = tk.Label(
            card_frame,
            text="请点击开始学习",
            font=self.font_config.get('title', ("Arial", 48, "bold")),
            bg="white",
            fg="#333333"
        )
        self.word_label.pack(pady=(20, 10))
        
        # 释义标签
        self.definition_label = tk.Label(
            card_frame,
            text="",
            font=self.font_config.get('header', ("Arial", 24)),
            bg="white",
            fg="#666666"
        )
        self.definition_label.pack(pady=20)
        
        # 例句框架
        self.example_frame = tk.Frame(card_frame, bg="#f9f9f9", bd=1, relief=tk.SUNKEN)
        self.example_frame.pack(fill=tk.X, pady=15, padx=20, side=tk.BOTTOM)
        
        # 例句显示标签
        self.example_label = tk.Label(
            self.example_frame,
            text="",
            font=self.font_config.get('normal', ("Arial", 12)),
            bg="#f9f9f9",
            fg="#333333",
            wraplength=600,
            justify=tk.LEFT,
            padx=15,
            pady=10
        )
        self.example_label.pack(fill=tk.X)
        
        # 发音播放按钮
        self.pronounce_button = tk.Button(
            card_frame,
            text="🔊 播放发音",
            command=self.play_pronunciation,
            font=self.font_config.get('button', ("Arial", 12)),
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED,
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.pronounce_button.pack(pady=20)
        
        # 创建操作按钮框架
        action_frame = tk.Frame(self, bg="#f0f0f0", pady=20)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 例句按钮
        self.example_button = tk.Button(
            action_frame,
            text="📝 显示例句",
            command=self.toggle_example,
            font=self.font_config.get('button', ("Arial", 12)),
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED,
            padx=15,
            pady=10,
            state=tk.DISABLED
        )
        self.example_button.pack(side=tk.LEFT, padx=10)
        
        # 需复习按钮
        self.review_button = tk.Button(
            action_frame,
            text="需复习",
            command=self.mark_review,
            font=self.font_config.get('button', ("Arial", 14)),
            bg="#FF9800",
            fg="white",
            relief=tk.RAISED,
            padx=40,
            pady=15,
            state=tk.DISABLED
        )
        self.review_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=20)
        
        # 已掌握按钮
        self.mastered_button = tk.Button(
            action_frame,
            text="已掌握",
            command=self.mark_mastered,
            font=self.font_config.get('button', ("Arial", 14)),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            padx=40,
            pady=15,
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
                messagebox.showwarning("提示", "请先在词库管理中选择一个词库")
                return
            
            # 获取学习单词
            if self.learning_manager:
                self.current_batch = self.learning_manager.get_batch(batch_size)
            else:
                # 直接从word_manager获取单词
                words = self.word_manager.get_words_from_active_set()
                if not words:
                    messagebox.showinfo("提示", f"词库 '{active_set['name']}' 中没有单词")
                    return
                # 取指定数量的单词
                import random
                self.current_batch = random.sample(words, min(batch_size, len(words)))
            
            if not self.current_batch:
                messagebox.showinfo("提示", f"词库 '{active_set['name']}' 中没有可学习的单词")
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
                definition = self.current_word['translation']
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
            
            # 显示释义和音标
            display_text = definition or "无释义"
            if phonetic:
                display_text = f"{phonetic}\n{display_text}"
            self.definition_label.config(text=display_text)
            
            # 重置例句状态
            self.is_example_visible = False
            self.current_example = ""
            self.example_label.config(text="")
            if hasattr(self, 'example_button'):
                self.example_button.config(text="📝 显示例句")
            
            # 如果例句功能启用且有单词管理器，异步获取例句
            if self.word_manager and self.settings_manager and self.settings_manager.get_setting("example_enabled", True):
                threading.Thread(target=self._fetch_example_async, daemon=True).start()
    
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
                            messagebox.showinfo("提示", "发音播放失败，请检查网络连接")
                        except Exception:
                            pass

                try:
                    self.main_frame.after(0, _on_done)
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
    
    def _fetch_example_async(self):
        """
        异步获取单词例句
        """
        log_info(f"_fetch_example_async called, current_word: {self.current_word}, word_manager: {self.word_manager}")
        if self.current_word and self.word_manager:
            # 确保传递的是单词字符串而不是字典
            word_str = self.current_word['word'] if isinstance(self.current_word, dict) else self.current_word
            log_info(f"_fetch_example_async: calling get_word_example with word_str={word_str}")
            # 使用WordManager的异步API获取例句
            self.word_manager.get_word_example(
                word_str, 
                async_mode=True, 
                callback=self._on_example_fetched
            )
            
    def _on_example_fetched(self, example):
        """
        例句获取完成后的回调处理
        
        Args:
            example: 获取到的例句文本
        """
        log_info(f"_on_example_fetched called, example: {example}")
        try:
            self.current_example = example
            log_info(f"_on_example_fetched: current_example updated to {example}, is_example_visible={self.is_example_visible}")
            # 如果用户已经点击显示例句，自动更新UI
            if self.is_example_visible:
                log_info(f"_on_example_fetched: updating example_label with text={example}")
                self.master.after(0, lambda: self.example_label.config(text=example))
        except Exception as e:
            log_error(f"_on_example_fetched error: {str(e)}")
            pass  # 忽略UI更新错误
    
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
                # 如果还没有例句，异步获取（先检查数据库，没有则AI补全）
                self.master.after(0, lambda: self.example_label.config(text="正在获取例句..."))
                self.is_example_visible = True
                
                # 异步获取例句的回调函数
                def on_example_ready(example):
                    try:
                        self.current_example = example
                        self.master.after(0, lambda: self.example_label.config(
                            text=example if example else "无法获取例句"
                        ))
                        self.master.after(0, lambda: self.example_button.config(
                            text="📝 隐藏例句"
                        ))
                    except Exception:
                        pass  # 忽略UI更新错误
                
                try:
                    # 调用重构后的get_word_example方法（自动处理数据库检查和AI补全）
                    self.word_manager.get_word_example(
                        word_str, 
                        async_mode=True, 
                        callback=on_example_ready
                    )
                except Exception:
                    pass  # 忽略获取例句时的错误
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