"""
学习模式用户界面

实现学习模式的单词学习界面，包括单词展示、发音播放、掌握度标记等功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional


class LearningPage(tk.Frame):
    """
    学习模式页面，用于用户主动学习单词
    """
    
    def __init__(self, parent, learning_manager, **kwargs):
        """
        初始化学习页面
        
        Args:
            parent: 父窗口组件
            learning_manager: 学习管理器实例
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.learning_manager = learning_manager
        
        # 学习状态
        self.current_batch = []  # 当前学习批次的单词列表
        self.current_index = -1  # 当前单词索引
        self.current_word = None  # 当前单词
        self.is_playing = False  # 发音播放状态
        
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
        
        # 创建单词卡片框架
        card_frame = tk.Frame(
            self, 
            bg="white", 
            relief=tk.RAISED, 
            bd=2,
            padx=40,
            pady=60
        )
        card_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=40,
            pady=20
        )
        
        # 单词展示标签
        self.word_label = tk.Label(
            card_frame,
            text="请点击开始学习",
            font=("Arial", 48, "bold"),
            bg="white",
            fg="#333333"
        )
        self.word_label.pack(pady=(20, 10))
        
        # 释义标签
        self.definition_label = tk.Label(
            card_frame,
            text="",
            font=("Arial", 24),
            bg="white",
            fg="#666666"
        )
        self.definition_label.pack(pady=20)
        
        # 发音播放按钮
        self.pronounce_button = tk.Button(
            card_frame,
            text="🔊 播放发音",
            command=self.play_pronunciation,
            font=("Arial", 12),
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
        
        # 需复习按钮
        self.review_button = tk.Button(
            action_frame,
            text="需复习",
            command=self.mark_review,
            font=("Arial", 14),
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
            font=("Arial", 14),
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
            # 获取批次大小
            batch_size = int(self.batch_size_var.get())
            
            # 从学习管理器获取单词批次
            self.current_batch = self.learning_manager.get_batch(batch_size)
            
            if not self.current_batch:
                messagebox.showinfo("提示", "没有可学习的单词，请先添加单词")
                return
            
            # 开始学习第一个单词
            self.current_index = 0
            self._show_current_word()
            
            # 更新进度
            self._update_progress()
            
            # 启用按钮
            self._enable_buttons()
            
        except Exception as e:
            messagebox.showerror("错误", f"开始学习失败: {str(e)}")
    
    def _show_current_word(self):
        """
        显示当前单词和释义
        """
        if 0 <= self.current_index < len(self.current_batch):
            self.current_word = self.current_batch[self.current_index]
            
            # 更新单词标签
            self.word_label.config(text=self.current_word)
            
            # 获取并显示释义
            definition = self.learning_manager.get_word_definition(self.current_word)
            self.definition_label.config(text=definition or "无释义")
    
    def _update_progress(self):
        """
        更新进度显示
        """
        if self.current_batch:
            stats = self.learning_manager.get_current_stats()
            progress_text = f"进度: {self.current_index + 1}/{len(self.current_batch)}  |  "
            progress_text += f"掌握: {stats['mastered']}  |  "
            progress_text += f"需复习: {stats['review']}"
            self.progress_label.config(text=progress_text)
    
    def _enable_buttons(self):
        """
        启用所有操作按钮
        """
        self.pronounce_button.config(state=tk.NORMAL)
        self.review_button.config(state=tk.NORMAL)
        self.mastered_button.config(state=tk.NORMAL)
    
    def _disable_buttons(self):
        """
        禁用所有操作按钮
        """
        self.pronounce_button.config(state=tk.DISABLED)
        self.review_button.config(state=tk.DISABLED)
        self.mastered_button.config(state=tk.DISABLED)
    
    def play_pronunciation(self):
        """
        播放当前单词发音
        """
        if self.current_word and not self.is_playing:
            try:
                # 设置播放状态
                self.is_playing = True
                self.pronounce_button.config(text="🔊 播放中...")
                
                # 播放发音
                success = self.learning_manager.play_pronunciation(self.current_word)
                
                if not success:
                    messagebox.showinfo("提示", "发音播放失败，请检查网络连接")
                    
            except Exception as e:
                messagebox.showerror("错误", f"播放发音失败: {str(e)}")
            finally:
                # 恢复按钮状态
                self.is_playing = False
                self.pronounce_button.config(text="🔊 播放发音")
    
    def mark_mastered(self):
        """
        标记当前单词为已掌握
        """
        if self.current_word:
            self.learning_manager.mark_mastered(self.current_word)
            self._move_to_next_word()
    
    def mark_review(self):
        """
        标记当前单词需要复习
        """
        if self.current_word:
            self.learning_manager.mark_review(self.current_word)
            self._move_to_next_word()
    
    def _move_to_next_word(self):
        """
        移动到下一个单词
        """
        self.current_index += 1
        
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
        # 保存进度
        if self.learning_manager.save_progress():
            # 获取统计信息
            stats = self.learning_manager.get_current_stats()
            
            # 显示学习总结
            summary = f"学习完成！\n\n"
            summary += f"总学习单词: {stats['total']}\n"
            summary += f"掌握单词: {stats['mastered']}\n"
            summary += f"需复习单词: {stats['review']}"
            
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
        
        self.word_label.config(text="请点击开始学习")
        self.definition_label.config(text="")
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