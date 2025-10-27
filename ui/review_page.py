import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os
import threading
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_player import AudioPlayer
from logger import log_info, log_error


class ReviewPage(tk.Frame):
    """单词复习页面"""
    
    def __init__(self, parent, word_manager, settings_manager, font_config):
        """初始化单词复习页面"""
        super().__init__(parent, bg='white')
        self.parent = parent
        self.word_manager = word_manager
        self.settings_manager = settings_manager
        self.font_config = font_config
        
        # 初始化音频播放器
        self.audio_player = AudioPlayer()
        self.audio_available = self.audio_player.is_available()
        
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
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        self.main_frame = tk.Frame(self, bg='white')
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)
        
        # 标题
        title_label = tk.Label(
            self.main_frame, 
            text="单词复习", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=20)
        
        # 过滤选项
        filter_frame = tk.Frame(self.main_frame, bg='white')
        filter_frame.pack(pady=10, fill=tk.X)
        
        self.filter_var = tk.StringVar(value="all")
        
        tk.Label(filter_frame, text="过滤:", font=self.font_config['normal'], bg='white').pack(side=tk.LEFT, padx=10)
        
        all_radio = tk.Radiobutton(
            filter_frame,
            text="全部单词",
            variable=self.filter_var,
            value="all",
            font=self.font_config['normal'],
            bg='white',
            command=self._on_filter_change
        )
        all_radio.pack(side=tk.LEFT, padx=10)
        
        familiar_radio = tk.Radiobutton(
            filter_frame,
            text="熟词",
            variable=self.filter_var,
            value="familiar",
            font=self.font_config['normal'],
            bg='white',
            command=self._on_filter_change
        )
        familiar_radio.pack(side=tk.LEFT, padx=10)
        
        difficult_radio = tk.Radiobutton(
            filter_frame,
            text="难词",
            variable=self.filter_var,
            value="difficult",
            font=self.font_config['normal'],
            bg='white',
            command=self._on_filter_change
        )
        difficult_radio.pack(side=tk.LEFT, padx=10)
        
        # 单词卡片
        self.card_frame = tk.Frame(self.main_frame, bg='#f5f5f5', bd=3, relief=tk.RAISED)
        self.card_frame.pack(pady=30, fill=tk.BOTH, expand=True, padx=50)
        
        # 单词显示
        self.word_var = tk.StringVar()
        self.word_label = tk.Label(
            self.card_frame,
            textvariable=self.word_var,
            font=self.font_config['header'],
            bg='#f5f5f5',
            wraplength=600
        )
        self.word_label.pack(pady=40)
        
        # 翻译显示
        self.translation_var = tk.StringVar()
        self.translation_label = tk.Label(
            self.card_frame,
            textvariable=self.translation_var,
            font=self.font_config['normal'],
            bg='#f5f5f5',
            fg='#666666',
            wraplength=600
        )
        self.translation_label.pack(pady=20)
        
        # 按钮区域
        buttons_frame = tk.Frame(self.main_frame, bg='white')
        buttons_frame.pack(pady=30)
        
        # 控制按钮
        control_buttons_frame = tk.Frame(buttons_frame, bg='white')
        control_buttons_frame.pack(side=tk.LEFT)
        
        self.prev_button = tk.Button(
            control_buttons_frame,
            text="◀ 上一个",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._prev_word,
            bg='#2196F3',
            fg='white'
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.show_button = tk.Button(
            control_buttons_frame,
            text="👁️ 显示翻译",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._toggle_translation,
            bg='#FF9800',
            fg='white'
        )
        self.show_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(
            control_buttons_frame,
            text="下一个 ▶",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._next_word,
            bg='#2196F3',
            fg='white'
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # 发音和操作按钮
        action_buttons_frame = tk.Frame(buttons_frame, bg='white')
        action_buttons_frame.pack(side=tk.LEFT, padx=20)
        
        self.pronounce_button = tk.Button(
            action_buttons_frame,
            text="🔊 发音",
            font=self.font_config['button'],
            width=10,
            height=2,
            command=self._play_pronunciation,
            bg='#4CAF50',
            fg='white'
        )
        self.pronounce_button.pack(side=tk.LEFT, padx=5)
        
        self.familiar_button = tk.Button(
            action_buttons_frame,
            text="✅ 标记熟悉",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._mark_as_familiar,
            bg='#4CAF50',
            fg='white'
        )
        self.familiar_button.pack(side=tk.LEFT, padx=5)
        
        self.difficult_button = tk.Button(
            action_buttons_frame,
            text="❌ 标记困难",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._mark_as_difficult,
            bg='#F44336',
            fg='white'
        )
        self.difficult_button.pack(side=tk.LEFT, padx=5)
        
        # 例句按钮
        self.example_button = tk.Button(
            action_buttons_frame,
            text="📝 显示例句",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._toggle_example,
            bg='#2196F3',
            fg='white'
        )
        self.example_button.pack(side=tk.LEFT, padx=5)
        
        # 复习总结按钮
        summary_frame = tk.Frame(self.main_frame, bg='white')
        summary_frame.pack(pady=10)
        
        self.summary_button = tk.Button(
            summary_frame,
            text="📊 复习总结",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._show_summary,
            bg='#FF9800',
            fg='white'
        )
        self.summary_button.pack()
        
        # 进度信息
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(
            self.main_frame,
            textvariable=self.progress_var,
            font=self.font_config['normal'],
            bg='white',
            fg='#666666'
        )
        self.progress_label.pack(pady=10)
    
    def _load_words(self):
        """加载单词列表"""
        filter_type = self.filter_var.get()
        # 获取单词列表和翻译信息
        word_list = self.word_manager.get_all_words()
        # 为每个单词获取对应的翻译
        all_words_dict = {word: self.word_manager.get_word_translation(word) or "" for word in word_list}
        wrong_words = self.word_manager.get_wrong_words()
        weights = getattr(self.word_manager, 'word_weights', {})
        
        if filter_type == "all":
            # 所有单词，格式为(单词, 翻译)的列表
            self.review_words = list(all_words_dict.items())
        elif filter_type == "familiar":
            # 熟词：熟悉度高于阈值的单词
            self.review_words = [(word, all_words_dict.get(word, "")) 
                                for word in word_list 
                                if word in self.word_familiarity and self.word_familiarity[word] >= self.familiar_threshold]
            # 如果没有熟词数据，使用权重较低的单词作为备选
            if not self.review_words:
                self.review_words = [(word, all_words_dict.get(word, "")) 
                                    for word in word_list 
                                    if word in weights and weights[word] < 1.5]
        elif filter_type == "difficult":
            # 难词：熟悉度低于阈值或者权重高的单词
            # 先收集熟悉度低的单词
            familiarity_difficult = [(word, all_words_dict.get(word, "")) 
                                   for word in word_list 
                                   if word in self.word_familiarity and self.word_familiarity[word] < self.familiar_threshold]
            # 再收集高权重单词
            weight_difficult = [(word, all_words_dict.get(word, "")) 
                               for word in word_list 
                               if word in weights and weights[word] > 1.5]
            # 合并并去重
            difficult_words = dict(familiarity_difficult + weight_difficult)
            self.review_words = list(difficult_words.items())
            # 如果还没有难词，就使用错误单词列表
            if not self.review_words:
                self.review_words = [(word, all_words_dict.get(word, "")) for word in wrong_words.keys()]
        
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
        """更新单词显示"""
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
        
        # 显示当前单词
        word, translation = self.review_words[self.current_index]
        self.word_var.set(word)
        
        # 获取例句
        # 使用word_manager的get_word_example方法获取例句
        self.current_example = getattr(self.word_manager, "get_word_example", lambda x: "")(word)
        
        # 根据模式显示翻译和例句
        if self.show_translation:
            display_text = f"翻译: {translation}"
            if self.is_example_visible and self.current_example:
                display_text += f"\n\n📝 例句: {self.current_example}"
            self.translation_var.set(display_text)
            self.show_button.config(text="🙈 隐藏翻译")
        else:
            if self.is_example_visible and self.current_example:
                self.translation_var.set(f"📝 例句: {self.current_example}")
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
        """显示上一个单词"""
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
            
        self.is_example_visible = not self.is_example_visible
        self._update_word_display()
        
        # 检查是否需要自动下一个单词
        auto_next = self.settings_manager.get_setting("auto_next_example", False)
        if auto_next and self.is_example_visible:
            # 延迟一段时间后自动切换到下一个单词
            self.after(self.settings_manager.get_setting("auto_next_delay", 2000), self._next_word)
    
    def _next_word(self):
        """显示下一个单词"""
        if self.current_index < len(self.review_words) - 1:
            self.current_index += 1
            self.show_translation = False
            self.is_example_visible = False
            self._update_word_display()
            self._update_progress()
            log_info(f"显示下一个单词: {self.review_words[self.current_index][0]}")
    
    def _play_pronunciation(self):
        """播放单词发音"""
        if not self.review_words:
            return
        
        word, _ = self.review_words[self.current_index]
        success = self.audio_player.play_pronunciation(word)
        if not success and self.audio_available:
            messagebox.showerror("播放失败", "无法播放单词发音，请检查网络连接。")
    
    def _mark_as_important(self):
        """标记为重点单词（增加权重）"""
        if not self.review_words:
            return
        
        word, _ = self.review_words[self.current_index]
        # 直接修改权重，增加1.0
        if word in self.word_manager.word_weights:
            self.word_manager.word_weights[word] += 1.0
            self.word_manager._save_data(
                self.word_manager.word_weights_file, 
                {word: self.word_manager.word_weights[word]}
            )
        else:
            self.word_manager.word_weights[word] = 2.0
            self.word_manager._save_data(
                self.word_manager.word_weights_file, 
                {word: 2.0}
            )
        
        messagebox.showinfo("成功", f"已将 '{word}' 标记为重点单词")
        log_info(f"标记重点单词: {word}")
    
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
        """将当前单词标记为熟悉"""
        if not self.review_words:
            return
        
        word, _ = self.review_words[self.current_index]
        
        # 更新熟悉度数据
        self.word_familiarity[word] = min(self.word_familiarity.get(word, 0) + 0.2, 1.0)
        self.session_stats["familiar"] += 1
        
        # 调用word_manager更新熟悉度
        if hasattr(self.word_manager, 'update_word_familiarity'):
            try:
                self.word_manager.update_word_familiarity(word, self.word_familiarity[word])
            except Exception as e:
                log_error(f"更新单词熟悉度失败: {str(e)}")
        
        # 显示提示并自动下一个单词
        self.translation_var.set(f"✓ 已将 '{word}' 标记为熟悉")
        log_info(f"标记熟悉单词: {word}, 熟悉度: {self.word_familiarity[word]:.2f}")
        
        # 检查是否需要自动下一个单词
        auto_next = self.settings_manager.get_setting("auto_next_familiar", False)
        if auto_next:
            delay = self.settings_manager.get_setting("auto_next_delay", 1000)
            self.after(delay, self._next_word)
    
    def _mark_as_difficult(self):
        """将当前单词标记为困难"""
        if not self.review_words:
            return
        
        word, _ = self.review_words[self.current_index]
        
        # 更新熟悉度数据
        self.word_familiarity[word] = max(self.word_familiarity.get(word, 1.0) - 0.3, 0.0)
        self.session_stats["difficult"] += 1
        
        # 调用word_manager更新熟悉度
        if hasattr(self.word_manager, 'update_word_familiarity'):
            try:
                self.word_manager.update_word_familiarity(word, self.word_familiarity[word])
            except Exception as e:
                log_error(f"更新单词熟悉度失败: {str(e)}")
        
        # 同时标记为高权重（需要复习）
        if hasattr(self.word_manager, 'update_word_weight'):
            try:
                current_weight = getattr(self.word_manager, 'word_weights', {}).get(word, 1.0)
                self.word_manager.update_word_weight(word, False)  # False表示不认识，增加权重
            except Exception as e:
                log_error(f"更新单词权重失败: {str(e)}")
        
        # 显示提示并自动下一个单词
        self.translation_var.set(f"! 已将 '{word}' 标记为困难，需要加强复习")
        log_info(f"标记困难单词: {word}, 熟悉度: {self.word_familiarity[word]:.2f}")
        
        # 检查是否需要自动下一个单词
        auto_next = self.settings_manager.get_setting("auto_next_difficult", False)
        if auto_next:
            delay = self.settings_manager.get_setting("auto_next_delay", 1000)
            self.after(delay, self._next_word)
    
    def _show_summary(self):
        """显示复习总结"""
        # 创建新窗口显示总结
        summary_window = tk.Toplevel(self)
        summary_window.title("复习总结")
        summary_window.geometry("500x400")
        summary_window.configure(bg='white')
        summary_window.transient(self.parent)
        summary_window.grab_set()
        
        # 标题
        title_label = tk.Label(
            summary_window,
            text="复习总结",
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=20)
        
        # 统计信息框架
        stats_frame = tk.Frame(summary_window, bg='white')
        stats_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)
        
        # 总单词数
        total_words = len(self.review_words)
        tk.Label(
            stats_frame,
            text=f"本次复习单词总数: {total_words}",
            font=self.font_config['normal'],
            bg='white'
        ).pack(anchor='w', pady=5)
        
        # 熟悉单词数
        familiar_count = self.session_stats["familiar"]
        familiar_percent = (familiar_count / total_words * 100) if total_words > 0 else 0
        tk.Label(
            stats_frame,
            text=f"熟悉单词: {familiar_count} ({familiar_percent:.1f}%)",
            font=self.font_config['normal'],
            bg='white',
            fg='#4CAF50'
        ).pack(anchor='w', pady=5)
        
        # 困难单词数
        difficult_count = self.session_stats["difficult"]
        difficult_percent = (difficult_count / total_words * 100) if total_words > 0 else 0
        tk.Label(
            stats_frame,
            text=f"困难单词: {difficult_count} ({difficult_percent:.1f}%)",
            font=self.font_config['normal'],
            bg='white',
            fg='#F44336'
        ).pack(anchor='w', pady=5)
        
        # 获取熟悉度低于阈值的单词列表
        difficult_words = [word for word, familiarity in self.word_familiarity.items() 
                          if familiarity < self.familiar_threshold]
        
        # 复习建议
        tk.Label(
            stats_frame,
            text="复习建议:",
            font=self.font_config['normal'],
            bg='white',
            fg='#2196F3'
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
            bg='white',
            fg='#333333',
            wraplength=400,
            justify=tk.LEFT
        )
        advice_label.pack(anchor='w', pady=5)
        
        # 按钮
        button_frame = tk.Frame(summary_window, bg='white')
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="关闭",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=summary_window.destroy,
            bg='#9E9E9E',
            fg='white'
        ).pack(pady=10)