import tkinter as tk
from tkinter import messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_player import AudioPlayer
from logger import log_info, log_wrong_word


class DictationPage(tk.Frame):
    """听写练习页面"""
    
    def __init__(self, parent, word_manager, settings_manager=None, font_config=None):
        """初始化听写页面"""
        super().__init__(parent, bg='white')
        self.parent = parent
        self.word_manager = word_manager
        self.settings_manager = settings_manager
        self.font_config = font_config or {'header': ('SimHei', 16, 'bold'), 'normal': ('SimHei', 12), 'button': ('SimHei', 12, 'bold')}
        
        # 初始化音频播放器
        self.audio_player = AudioPlayer()
        
        # 检查音频播放功能
        self.audio_available = self.audio_player.is_available()
        if not self.audio_available:
            messagebox.showwarning("音频功能", "音频播放功能不可用。正在尝试安装必要组件...")
            # 尝试安装依赖
            if not self.audio_player.install_requirements():
                messagebox.showinfo("提示", "将继续运行，但无法播放音频。")
        
        # 当前单词
        self.current_word = None
        
        # 创建UI
        self._create_ui()
        
        # 开始练习
        self.word_manager.start_exercise("听写")
        self._next_word()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        self.main_frame = tk.Frame(self, bg='white')
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)
        
        # 标题
        title_label = tk.Label(
            self.main_frame, 
            text="听写练习", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=20)
        
        # 提示信息
        hint_label = tk.Label(
            self.main_frame, 
            text="请点击播放按钮听单词发音，然后在下方输入单词", 
            font=self.font_config['normal'],
            bg='white',
            fg='#666666'
        )
        hint_label.pack(pady=10)
        
        # 播放区域
        play_frame = tk.Frame(self.main_frame, bg='white')
        play_frame.pack(pady=30)
        
        self.play_button = tk.Button(
            play_frame,
            text="🔊 播放发音",
            font=self.font_config['button'],
            width=20,
            height=3,
            command=self._play_pronunciation,
            bg='#4CAF50',
            fg='white',
            relief=tk.RAISED,
            bd=2
        )
        self.play_button.pack()
        
        # 输入区域
        input_frame = tk.Frame(self.main_frame, bg='white')
        input_frame.pack(pady=20)
        
        input_label = tk.Label(
            input_frame,
            text="请输入单词:",
            font=self.font_config['normal'],
            bg='white'
        )
        input_label.pack(anchor='w', pady=5)
        
        self.word_entry = tk.Entry(
            input_frame,
            font=self.font_config['normal'],
            width=40,
            bd=2,
            relief=tk.SUNKEN
        )
        self.word_entry.pack(pady=10, ipady=5)
        self.word_entry.bind('<Return>', lambda event: self._check_answer())
        
        # 按钮区域
        buttons_frame = tk.Frame(self.main_frame, bg='white')
        buttons_frame.pack(pady=30)
        
        self.check_button = tk.Button(
            buttons_frame,
            text="✓ 检查",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._check_answer,
            bg='#2196F3',
            fg='white'
        )
        self.check_button.pack(side=tk.LEFT, padx=10)
        
        self.skip_button = tk.Button(
            buttons_frame,
            text="⏭️ 跳过",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._skip_word,
            bg='#FF9800',
            fg='white'
        )
        self.skip_button.pack(side=tk.LEFT, padx=10)
        
        # 结果显示区域
        self.result_var = tk.StringVar()
        self.result_var.set("")
        self.result_label = tk.Label(
            self.main_frame,
            textvariable=self.result_var,
            font=self.font_config['normal'],
            bg='white',
            wraplength=600
        )
        self.result_label.pack(pady=20)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        self.status_bar = tk.Label(
            self.main_frame,
            textvariable=self.status_var,
            font=self.font_config['normal'],
            bg='#f0f0f0',
            anchor='w',
            bd=1,
            relief=tk.SUNKEN
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
    
    def _play_pronunciation(self):
        """播放单词发音"""
        if self.current_word:
            success = self.audio_player.play_pronunciation(self.current_word)
            if not success and self.audio_available:
                messagebox.showerror("播放失败", "无法播放单词发音，请检查网络连接。")
            elif not self.audio_available:
                messagebox.showinfo("提示", f"当前单词: {self.current_word}")
    
    def _next_word(self):
        """获取下一个单词"""
        self.current_word = self.word_manager.get_word_by_weight()
        if not self.current_word:
            messagebox.showinfo("提示", "没有可用的单词，请先添加单词。")
            return
        
        # 清空输入和结果
        self.word_entry.delete(0, tk.END)
        self.result_var.set("")
        self.status_var.set(f"请听发音并输入单词")
        
        # 自动播放发音
        self._play_pronunciation()
        
        # 设置焦点到输入框
        self.word_entry.focus_set()
    
    def _check_answer(self):
        """检查答案"""
        user_input = self.word_entry.get().strip()
        
        if not user_input:
            messagebox.showwarning("提示", "请输入单词后再检查。")
            return
        
        # 检查拼写
        is_correct = self.word_manager.check_spelling(self.current_word, user_input)
        
        # 更新单词权重
        self.word_manager.update_word_weight(self.current_word, is_correct)
        
        # 显示结果
        if is_correct:
            self.result_var.set(f"✓ 正确！")
            self.result_label.config(fg='#4CAF50')
            log_info(f"听写正确: {self.current_word}")
        else:
            translation = self.word_manager.word_dict.get(self.current_word, "")
            self.result_var.set(f"✗ 错误！正确答案: {self.current_word} ({translation})")
            self.result_label.config(fg='#f44336')
            log_wrong_word(self.current_word, user_input)
        
        # 更新状态栏
        progress = self.word_manager.get_progress()
        self.status_var.set(f"正确率: {progress.get('correct_rate', 0) * 100:.1f}%")
        
        # 延迟显示下一个单词
        self.main_frame.after(2000, self._next_word)
    
    def _skip_word(self):
        """跳过当前单词"""
        # 标记为错误
        self.word_manager.update_word_weight(self.current_word, False)
        self.result_var.set(f"⏭️ 已跳过: {self.current_word}")
        self.result_label.config(fg='#FF9800')
        log_info(f"跳过单词: {self.current_word}")
        
        # 显示下一个单词
        self.main_frame.after(1000, self._next_word)