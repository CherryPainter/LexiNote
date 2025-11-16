import tkinter as tk
from tkinter import messagebox, ttk
import threading
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_player import AudioPlayer
from logger import log_info, log_wrong_word, log_error
from core.dictation import DictationManager
from ui.components.scrollable_frame import create_scrollable_frame


class DictationPage(tk.Frame):
    """听写练习页面，支持单个听写和队列听写模式"""

    def __init__(self, parent, word_manager, settings_manager=None, font_config=None):
        """初始化听写页面"""
        super().__init__(parent, bg='white')
        self.parent = parent
        self.word_manager = word_manager
        from core.settings_manager import SettingsManager
        self.settings_manager = settings_manager or SettingsManager()
        self.font_config = font_config or {'header': ('SimHei', 16, 'bold'), 'normal': (
            'SimHei', 12), 'button': ('SimHei', 12, 'bold')}

        # 初始化听写管理器
        self.dictation_manager = DictationManager(word_manager)

        # 初始化音频播放器
        self.audio_player = AudioPlayer()

        # 检查音频播放功能
        self.audio_available = self.audio_player.is_available()
        if not self.audio_available:
            messagebox.showwarning("音频功能", "音频播放功能不可用。正在尝试安装必要组件...")
            # 尝试安装依赖
            if not self.audio_player.install_requirements():
                messagebox.showinfo("提示", "将继续运行，但无法播放音频。")

        # 当前状态
        self.current_word = None
        self.current_mode = "single"  # single 或 queue
        self.current_source = "today"  # today, library 或 familiar
        self.time_limit = 60  # 默认时间限制为60秒
        self.timer_id = None
        self.remaining_time = self.time_limit
        self.batch_size = 10  # 默认批量大小
        self.showing_summary = False
        self.session_results = []  # 记录本次练习结果
        self.auto_next = True  # 默认自动跳转到下一个单词
        self.word_start_time = None  # 记录当前单词开始的时间

        # 创建UI
        self._create_ui()

        # 注册设置监听器，实时响应自动/手动模式切换
        try:
            self.settings_manager.register_listener('auto_mode_word_learning', self._on_auto_mode_word_learning_change)
        except Exception:
            pass

        # 开始练习
        self.word_manager.start_exercise("听写")

    def _create_ui(self):
        """创建用户界面，支持模式选择和练习界面"""
        # 主框架 - 使用通用滚动框架
        content_scroll_frame, self.main_frame, _, _ = create_scrollable_frame(self, padx=50, pady=30)
        content_scroll_frame.pack(expand=True, fill=tk.BOTH)

        # 显示模式选择界面
        self._show_mode_selection()

    def _show_mode_selection(self):
        """显示模式选择界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # 标题
        title_label = tk.Label(
            self.main_frame, 
            text="听写模式选择", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=30)

        # 模式选择区域
        mode_frame = tk.Frame(self.main_frame, bg='white')
        mode_frame.pack(pady=20, fill=tk.X, expand=True)

        # 模式选择
        mode_label = tk.Label(
            mode_frame,
            text="选择听写模式:",
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        mode_label.pack(fill=tk.X, padx=50, pady=(10, 5))

        # 单选按钮变量
        self.mode_var = tk.StringVar(value="single")

        single_mode_frame = tk.Frame(mode_frame, bg='white')
        single_mode_frame.pack(fill=tk.X, padx=50, pady=5)

        single_radio = tk.Radiobutton(
            single_mode_frame,
            text="单个听写",
            variable=self.mode_var,
            value="single",
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        single_radio.pack(side=tk.LEFT)

        single_desc = tk.Label(
            single_mode_frame,
            text="一次练习一个单词",
            font=self.font_config['normal'],
            bg='white',
            fg='#666666'
        )
        single_desc.pack(side=tk.LEFT, padx=10)

        # 单个听写模式的自动跳转设置
        self.auto_next_var = tk.BooleanVar(value=True)
        self.auto_next_checkbox = tk.Checkbutton(
            single_mode_frame,
            text="自动跳转到下一个单词",
            variable=self.auto_next_var,
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        self.auto_next_checkbox.pack(side=tk.LEFT, padx=20)

        queue_mode_frame = tk.Frame(mode_frame, bg='white')
        queue_mode_frame.pack(fill=tk.X, padx=50, pady=5)

        queue_radio = tk.Radiobutton(
            queue_mode_frame,
            text="队列听写",
            variable=self.mode_var,
            value="queue",
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        queue_radio.pack(side=tk.LEFT)

        queue_desc = tk.Label(
            queue_mode_frame,
            text="连续练习多个单词，有时间限制",
            font=self.font_config['normal'],
            bg='white',
            fg='#666666'
        )
        queue_desc.pack(side=tk.LEFT, padx=10)

        # 单词来源选择
        source_label = tk.Label(
            mode_frame,
            text="单词来源:",
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        source_label.pack(fill=tk.X, padx=50, pady=(20, 5))

        # 来源选择下拉菜单
        self.source_var = tk.StringVar(value="today")

        source_frame = tk.Frame(mode_frame, bg='white')
        source_frame.pack(fill=tk.X, padx=50, pady=5)

        source_label2 = tk.Label(
            source_frame,
            text="选择来源:",
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        source_label2.pack(side=tk.LEFT, padx=5)

        source_option = ttk.Combobox(
            source_frame,
            textvariable=self.source_var,
            values=["今日学习单词", "全词库随机", "熟词库"],
            font=self.font_config['normal'],
            state="readonly",
            width=20
        )
        source_option.pack(side=tk.LEFT, padx=10, pady=5)
        source_option.current(0)

        # 队列大小设置（仅队列模式显示）
        self.batch_frame = tk.Frame(mode_frame, bg='white')

        batch_label = tk.Label(
            self.batch_frame,
            text="队列大小:",
            font=self.font_config['normal'],
            bg='white'
        )
        batch_label.pack(side=tk.LEFT, padx=5)

        self.batch_var = tk.StringVar(value="10")
        batch_entry = tk.Entry(
            self.batch_frame,
            textvariable=self.batch_var,
            font=self.font_config['normal'],
            width=5
        )
        batch_entry.pack(side=tk.LEFT, padx=5)

        # 时间限制设置（仅队列模式显示）
        self.time_frame = tk.Frame(mode_frame, bg='white')

        time_label = tk.Label(
            self.time_frame,
            text="每个单词时限(秒):",
            font=self.font_config['normal'],
            bg='white'
        )
        time_label.pack(side=tk.LEFT, padx=5)

        self.time_var = tk.StringVar(value="60")
        time_entry = tk.Entry(
            self.time_frame,
            textvariable=self.time_var,
            font=self.font_config['normal'],
            width=5
        )
        time_entry.pack(side=tk.LEFT, padx=5)

        # 难度级别选择
        difficulty_frame = tk.Frame(mode_frame, bg='white')
        difficulty_frame.pack(fill=tk.X, padx=50, pady=10)

        difficulty_label = tk.Label(
            difficulty_frame,
            text="难度级别:",
            font=self.font_config['normal'],
            bg='white'
        )
        difficulty_label.pack(side=tk.LEFT, padx=5)

        self.difficulty_var = tk.StringVar(value="medium")
        difficulty_option = ttk.Combobox(
            difficulty_frame,
            textvariable=self.difficulty_var,
            values=["简单", "中等", "困难"],
            font=self.font_config['normal'],
            state="readonly",
            width=10
        )
        difficulty_option.pack(side=tk.LEFT, padx=10, pady=5)
        difficulty_option.current(1)

        # 按钮区域
        buttons_frame = tk.Frame(self.main_frame, bg='white')
        buttons_frame.pack(pady=40)

        start_button = tk.Button(
            buttons_frame,
            text="开始听写",
            font=self.font_config['button'],
            width=20,
            height=2,
            command=self._start_dictation,
            bg='#4CAF50',
            fg='white'
        )
        start_button.pack(pady=10)

        # 绑定模式变化事件
        self.mode_var.trace_add("write", self._on_mode_change)

        # 初始化显示状态
        self._on_mode_change()

    def _on_mode_change(self, *args):
        """当模式变化时更新UI"""
        mode = self.mode_var.get()
        if mode == "queue":
            self.batch_frame.pack(fill=tk.X, padx=50, pady=5)
            self.time_frame.pack(fill=tk.X, padx=50, pady=5)
        else:
            self.batch_frame.pack_forget()
            self.time_frame.pack_forget()

    def _start_dictation(self):
        """开始听写练习"""
        # 获取选择的模式和参数
        self.current_mode = self.mode_var.get()

        # 获取用户设置的自动跳转选项（仅单个模式）
        if self.current_mode == "single":
            # 全局设置优先：如果模块被设置为 auto，则强制自动跳转并禁用本地开关
            try:
                mode = self.settings_manager.get_auto_mode('word_learning') if self.settings_manager else 'manual'
            except Exception:
                mode = 'manual'

            if mode == 'auto':
                self.auto_next = True
                try:
                    self.auto_next_var.set(True)
                    self.auto_next_checkbox.config(state=tk.DISABLED)
                except Exception:
                    pass
            else:
                # 手动模式：使用用户选择的本地开关
                self.auto_next = self.auto_next_var.get()
                try:
                    self.auto_next_checkbox.config(state=tk.NORMAL)
                except Exception:
                    pass

        # 获取来源
        source_text = self.source_var.get()

        # 设置当前来源
        if source_text == "今日学习单词":
            self.current_source = "today"
        elif source_text == "全词库随机":
            self.current_source = "library"
        else:
            self.current_source = "familiar"

        # 统一检查所选来源是否有可用单词（无则要求用户重新选择或去学习）
        if not self._ensure_source_has_words():
            return

        # 获取难度级别
        difficulty_text = self.difficulty_var.get()
        if difficulty_text == "简单":
            self.current_difficulty = "easy"
        elif difficulty_text == "中等":
            self.current_difficulty = "medium"
        else:
            self.current_difficulty = "hard"

        # 获取队列模式参数
        if self.current_mode == "queue":
            try:
                self.batch_size = int(self.batch_var.get())
                if self.batch_size <= 0 or self.batch_size > 50:
                    messagebox.showwarning("参数错误", "队列大小应在1-50之间")
                    return
            except ValueError:
                messagebox.showwarning("参数错误", "请输入有效的队列大小")
                return

            try:
                self.time_limit = int(self.time_var.get())
                if self.time_limit <= 0 or self.time_limit > 300:
                    messagebox.showwarning("参数错误", "时间限制应在1-300秒之间")
                    return
            except ValueError:
                messagebox.showwarning("参数错误", "请输入有效的时间限制")
                return

        # 创建练习界面
        self._create_exercise_ui()

        # 开始会话
        batch_size = self.batch_size if self.current_mode == "queue" else 1
        self.dictation_manager.start_session(
            mode=self.current_mode,
            source=self.current_source, 
            batch_size=batch_size,
            difficulty=self.current_difficulty
        )

        # 根据模式开始练习
        if self.current_mode == "single":
            self._next_word()
        else:
            # 构建队列（已在上方检查来源是否可用）
            self.dictation_manager.current_mode = "queue"
            self._next_word_in_queue()

    def _has_today_words(self):
        """检查是否有今日学习的单词"""
        # 获取今日学习的单词
        today_words = getattr(
            self.word_manager, 'get_today_learned_words', lambda: [])()
        has_words = len(today_words) > 0

        # 记录日志
        if has_words:
            log_info(f"发现今日学习的单词数量: {len(today_words)}")
        else:
            log_info("未发现今日学习的单词记录")

        return has_words

    def _ensure_source_has_words(self) -> bool:
        """检查当前选择的来源是否有单词；如果没有，提示用户并返回 False。

        返回:
            True: 可继续练习
            False: 需要用户重新选择来源或去学习
        """
        try:
            has_words = False
            if self.current_source == "today":
                has_words = self._has_today_words()
            elif self.current_source == "familiar":
                familiar_words = self.word_manager.get_familiar_words() if hasattr(self.word_manager, 'get_familiar_words') else []
                has_words = len(familiar_words) > 0
            elif self.current_source == "library":
                all_words = self.word_manager.get_all_words() if hasattr(self.word_manager, 'get_all_words') else []
                has_words = len(all_words) > 0

            if has_words:
                return True

            # 没有单词，提示并要求用户选择
            source_name = self.source_var.get()
            # 对于今日学习，额外询问是否跳转去学习
            if self.current_source == "today":
                resp = messagebox.askyesno(
                    "无可用单词",
                    f"系统未找到来自 '{source_name}' 的单词记录。\n\n是否现在去学习以生成今日学习单词？"
                )
                if resp:
                    # 获取MainWindow实例并调用正确的页面显示方法
                    # 假设parent的master是MainWindow实例
                    if hasattr(self.parent.master, '_show_learning_page'):
                        self.parent.master._show_learning_page()
                    elif hasattr(self.parent, '_show_learning_page'):
                        self.parent._show_learning_page()
                    else:
                        log_error("无法找到页面切换方法")
                return False

            # 其他来源直接提示用户选择其他来源
            messagebox.showinfo(
                "无可用单词",
                f"当前选择的来源 '{source_name}' 没有可用的单词。\n\n请在来源下拉中选择其他来源后重试。"
            )
            return False
        except Exception as e:
            log_error(f"检查单词来源时出错: {str(e)}")
            messagebox.showerror("错误", "检查单词来源时发生错误，请查看日志。")
            return False

    def _create_exercise_ui(self):
        """创建练习界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # 标题
        title_label = tk.Label(
            self.main_frame, 
            text="听写练习" if self.current_mode == "single" else f"队列听写 ({self.batch_size}个单词)", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=20)

        # 进度显示（仅队列模式）
        if self.current_mode == "queue":
            self.progress_var = tk.StringVar()
            self.progress_var.set("进度: 0/0")
            progress_label = tk.Label(
                self.main_frame,
                textvariable=self.progress_var,
                font=self.font_config['normal'],
                bg='white',
                fg='#333333'
            )
            progress_label.pack(pady=5)

        # 计时器显示（仅队列模式）
        if self.current_mode == "queue":
            self.timer_var = tk.StringVar()
            self.timer_var.set(f"剩余时间: {self.time_limit}s")
            timer_label = tk.Label(
                self.main_frame,
                textvariable=self.timer_var,
                font=self.font_config['normal'],
                bg='white',
                fg='#ff6600'
            )
            timer_label.pack(pady=5)

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
        
        # 退出按钮
        self.exit_button = tk.Button(
            buttons_frame,
            text="❌ 退出",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._exit_dictation,
            bg='#f44336',
            fg='white'
        )
        self.exit_button.pack(side=tk.LEFT, padx=10)

        # 下一个按钮（默认不显示，仅在手动模式下使用）
        self.next_button = tk.Button(
            buttons_frame,
            text="🔄 下一个",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._next_word,
            bg='#9C27B0',
            fg='white'
        )

        # 根据全局设置决定是否显示手动的下一个按钮（手动时显示）
        try:
            mode = self.settings_manager.get_auto_mode('word_learning') if self.settings_manager else 'manual'
            if mode == 'manual' and self.current_mode == 'single':
                self.next_button.pack(side=tk.LEFT, padx=10)
        except Exception:
            pass

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
        
    def _exit_dictation(self):
        """退出听写练习，返回模式选择界面"""
        # 停止计时器
        if self.timer_id:
            try:
                self.main_frame.after_cancel(self.timer_id)
                self.timer_id = None
            except Exception:
                pass
        
        # 结束会话
        try:
            self.dictation_manager.end_session()
        except Exception:
            pass
        
        # 重置状态
        self.current_word = None
        self.session_results = []
        
        # 返回模式选择界面
        self._show_mode_selection()
        
        # 记录日志
        log_info("用户退出听写练习")
        
    def _show_stats(self):
        """显示统计信息"""
        # 获取统计信息
        stats = self.dictation_manager.get_stats(days=7)
        
        # 创建统计信息窗口
        stats_window = tk.Toplevel(self)
        stats_window.title("听写统计信息")
        stats_window.geometry("600x400")
        stats_window.configure(bg='white')
        
        # 创建滚动框架
        from ui.components.scrollable_frame import create_scrollable_frame
        scroll_frame, content_frame, _, _ = create_scrollable_frame(stats_window)
        scroll_frame.pack(expand=True, fill=tk.BOTH)
        
        # 标题
        title_label = tk.Label(
            content_frame,
            text="听写统计信息",
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=20)
        
        # 总练习次数
        total_label = tk.Label(
            content_frame,
            text=f"总练习次数: {stats.get('total_sessions', 0)}次",
            font=self.font_config['normal'],
            bg='white'
        )
        total_label.pack(pady=5, padx=20, anchor='w')
        
        # 总练习单词数
        words_label = tk.Label(
            content_frame,
            text=f"总练习单词数: {stats.get('total_words', 0)}个",
            font=self.font_config['normal'],
            bg='white'
        )
        words_label.pack(pady=5, padx=20, anchor='w')
        
        # 平均正确率
        avg_accuracy = stats.get('average_accuracy', 0)
        accuracy_label = tk.Label(
            content_frame,
            text=f"平均正确率: {avg_accuracy * 100:.1f}%",
            font=self.font_config['normal'],
            bg='white'
        )
        accuracy_label.pack(pady=5, padx=20, anchor='w')
        
        # 最常错单词
        if stats.get('most_frequent_mistakes'):
            mistakes_label = tk.Label(
                content_frame,
                text="最常错单词:",
                bg='white',
                font=('SimHei', 12, 'bold')
            )
            mistakes_label.pack(pady=(15, 5), padx=20, anchor='w')
            
            mistakes_text = "、".join(stats['most_frequent_mistakes'][:10])  # 只显示前10个
            mistakes_words_label = tk.Label(
                content_frame,
                text=mistakes_text,
                font=self.font_config['normal'],
                bg='white',
                fg='#f44336',
                wraplength=550,
                justify=tk.LEFT
            )
            mistakes_words_label.pack(pady=5, padx=20, anchor='w')
        
        # 关闭按钮
        close_button = tk.Button(
            content_frame,
            text="关闭",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=stats_window.destroy,
            bg='#f44336',
            fg='white'
        )
        close_button.pack(pady=30)

    def _play_pronunciation(self):
        """播放单词发音"""
        if not self.current_word:
            return

        # 在后台线程播放，避免阻塞UI
        def _play():
            try:
                result = self.audio_player.play_pronunciation(self.current_word)
            except Exception as e:
                log_error(f"播放线程异常: {str(e)}")
                result = False

            # 在主线程中恢复UI状态并显示可能的错误信息
            def _on_done():
                try:
                    log_info("播放完成回调触发")
                    # 恢复播放按钮状态
                    try:
                        self.play_button.config(state=tk.NORMAL)
                    except Exception:
                        pass

                    if not result and self.audio_available:
                        messagebox.showerror("播放失败", "无法播放单词发音，请检查网络连接。")
                    elif not self.audio_available:
                        messagebox.showinfo("提示", f"当前单词: {self.current_word}")
                    else:
                        # 更新状态栏为已播放，但不显示单词内容
                        try:
                            self.status_var.set("已播放")
                        except Exception:
                            pass
                except Exception as e:
                    log_error(f"播放完成回调异常: {str(e)}")

            try:
                # 使用 after 将回调切回主线程
                self.main_frame.after(0, _on_done)
            except Exception:
                # 如果UI线程不可用，直接调用
                _on_done()

        # 禁用按钮以防重复点击
        try:
            self.play_button.config(state=tk.DISABLED)
            self.status_var.set("正在播放...")
        except Exception:
            pass

        t = threading.Thread(target=_play, daemon=True)
        t.start()

    def _on_auto_mode_word_learning_change(self, key, value):
        """设置变更回调：自动/手动切换变动时更新 UI 行为"""
        try:
            if value == 'auto':
                # 强制自动
                self.auto_next = True
                try:
                    self.auto_next_var.set(True)
                    self.auto_next_checkbox.config(state=tk.DISABLED)
                except Exception:
                    pass
                # 隐藏手动下一个按钮
                try:
                    self.next_button.pack_forget()
                except Exception:
                    pass
            else:
                # 手动模式
                try:
                    self.auto_next_checkbox.config(state=tk.NORMAL)
                except Exception:
                    pass
                # 显示下一个按钮仅在单个模式下
                try:
                    if self.current_mode == 'single':
                        self.next_button.pack(side=tk.LEFT, padx=10)
                except Exception:
                    pass
        except Exception:
            pass

    def _start_timer(self):
        """开始倒计时器"""
        self.remaining_time = self.time_limit
        self._update_timer()

    def _update_timer(self):
        """更新计时器显示"""
        if self.remaining_time <= 0:
            # 时间到，处理超时
            self._handle_timeout()
            return

        self.timer_var.set(f"剩余时间: {self.remaining_time}s")
        self.remaining_time -= 1
        self.timer_id = self.main_frame.after(1000, self._update_timer)

    def _stop_timer(self):
        """停止计时器"""
        if hasattr(self, 'timer_id') and self.timer_id:
            self.main_frame.after_cancel(self.timer_id)
            self.timer_id = None

    def _handle_timeout(self):
        """处理超时情况"""
        # 停止计时器
        self._stop_timer()

        # 计算超时所用时间
        from datetime import datetime
        time_spent = 0
        if self.word_start_time:
            time_spent = (datetime.now() - \
                          self.word_start_time).total_seconds()

        # 记录为错误（超时视为错误，会影响权重）
        self.dictation_manager.record_result(
            self.current_word, False, time_spent)

        # 显示超时信息
        self.result_var.set("⏰ 超时！正确答案: " + self.current_word)
        self.result_label.config(fg='#FF5722')
        log_info("超时单词: " + self.current_word)

        # 记录到本次练习结果
        self.session_results.append({
            'word': self.current_word,
            'input': 'timeout',
            'correct': False,
            'time_spent': time_spent,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 根据模式决定下一步
        if self.current_mode == "single":
            # 单个模式，显示下一个单词
            self.main_frame.after(1000, self._next_word)
        else:
            # 队列模式，需要先检查是否已经到达队列末尾
            # 使用队列索引进行精确判断，避免索引越界
            if self.dictation_manager.current_queue_index < len(self.dictation_manager.current_queue):
                self.main_frame.after(1000, self._next_word_in_queue)
            else:
                self.main_frame.after(1000, self._show_summary)

    def _next_word(self):
        """获取下一个单词（单个模式）"""
        self.current_word = self.dictation_manager.select_word(
            source=self.current_source)
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

    def _next_word_in_queue(self):
        """获取队列中的下一个单词"""
        # 停止之前的计时器
        self._stop_timer()

        # 先检查是否已经到达队列末尾，避免获取第11个单词
        if (not self.dictation_manager.current_queue or 
            self.dictation_manager.current_queue_index >= len(self.dictation_manager.current_queue)):
            # 已到达队列末尾，直接显示总结
            self._show_summary()
            return

        # 获取下一个单词
        self.current_word = self.dictation_manager.next_in_queue()

        # 记录单词开始时间
        if self.current_word:
            from datetime import datetime
            self.word_start_time = datetime.now()

        if not self.current_word:
            # 队列为空或已到达末尾，显示总结
            self._show_summary()
            return

        # 更新进度显示
        progress = self.dictation_manager.get_queue_progress()
        self.progress_var.set(f"进度: {progress['current']}/{progress['total']}")

        # 清空输入和结果
        self.word_entry.delete(0, tk.END)
        self.result_var.set("")



        self.status_var.set(f"请听发音并输入单词")

        # 自动播放发音
        self._play_pronunciation()

        # 开始计时
        self._start_timer()

        # 设置焦点到输入框
        self.word_entry.focus_set()

    def _show_summary(self):
        """显示听写总结"""
        self.showing_summary = True
        self._stop_timer()

        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # 标题
        title_label = tk.Label(
            self.main_frame, 
            text="听写完成！", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=30)

        # 结束会话并获取统计信息
        session_stats = self.dictation_manager.end_session()
        
        # 直接创建总结框架和基本信息
        self._create_summary_frame(session_stats)
        
        # 用于存储总结数据的变量
        self.summary_data = None
        self.session_stats = session_stats
        
        # 清除之前的suggestion_text引用
        if hasattr(self, 'suggestion_text'):
            del self.suggestion_text
        
        # 创建学习建议区域的占位符，显示"正在获取建议..."
        self._create_suggestion_placeholder()
        
        # 创建一个线程来获取总结，避免阻塞UI
        def get_summary_thread():
            # 获取总结数据
            summary = self.dictation_manager.summarize(callback=self._update_suggestion_stream)
            self.summary_data = summary
        
        # 启动线程
        thread = threading.Thread(target=get_summary_thread)
        thread.daemon = True
        thread.start()
    
    def _create_summary_frame(self, session_stats):
        """创建总结框架和基本信息"""
        # 创建总结信息框架
        self.summary_frame = tk.Frame(self.main_frame, bg='white')
        self.summary_frame.pack(pady=20, padx=50, fill=tk.X)
        
        # 会话基本信息卡片
        session_card = tk.LabelFrame(self.summary_frame, text="会话信息", font=self.font_config['normal'], bg='white')
        session_card.pack(fill=tk.X, pady=10, padx=5)
        
        session_label = tk.Label(
            session_card,
            text=f"{self.current_mode}模式 - {self.current_source}来源 - {self.difficulty_var.get()}难度",
            font=self.font_config['normal'],
            bg='white'
        )
        session_label.pack(anchor='w', pady=5, padx=5)
        
        # 统计信息卡片
        stats_card = tk.LabelFrame(self.summary_frame, text="统计数据", font=self.font_config['normal'], bg='white')
        stats_card.pack(fill=tk.X, pady=10, padx=5)
        
        # 正确率 - 使用session_stats中的数据，因为此时summary_data可能还没准备好
        accuracy = 0
        total = 0
        correct = 0
        if session_stats:
            accuracy = session_stats.get('accuracy', 0)
            total = session_stats.get('total_words', 0)
            correct = session_stats.get('correct_words', 0)
        accuracy_label = tk.Label(
            stats_card,
            text=f"正确率: {accuracy * 100:.1f}% ({correct}/{total})",
            font=self.font_config['normal'],
            bg='white'
        )
        accuracy_label.pack(pady=5, anchor='w', padx=5)
        
        # 会话时长
        if session_stats and 'duration' in session_stats:
            duration_label = tk.Label(
                stats_card,
                text=f"会话时长: {session_stats['duration']}秒",
                font=self.font_config['normal'],
                bg='white'
            )
            duration_label.pack(pady=5, anchor='w', padx=5)
        
        # 错词列表和恭喜信息将在_summary_data准备好后更新
        # AI建议区域将在收到第一个chunk时创建
    
    def _update_suggestion_stream(self, chunk, done):
        """处理流式输出的回调函数"""
        # 在主线程中更新UI
        self.after(0, lambda c=chunk, d=done: self._display_suggestion_chunk(c, d))
    
    def _display_suggestion_chunk(self, chunk, done):
        """显示建议的一部分"""
        # 确保错词列表或恭喜信息已显示
        if hasattr(self, 'summary_data') and self.summary_data and not hasattr(self, 'missed_words_displayed'):
            self._display_missed_words()
            self.missed_words_displayed = True
        
        # 临时设置为可编辑状态
        self.suggestion_text.config(state=tk.NORMAL)
        
        # 检查是否是第一个chunk，如果是则清除占位符文本
        if self.suggestion_text.get(1.0, tk.END).strip() == "正在获取建议...":
            self.suggestion_text.delete(1.0, tk.END)
        
        # 使用TextFormatter格式化chunk
        formatted_chunk = self.text_formatter.format_for_tkinter(chunk)
        self.suggestion_text.insert(tk.END, formatted_chunk)
        
        # 滚动到最新内容
        self.suggestion_text.see(tk.END)
        
        # 立即恢复为只读状态，防止用户编辑
        self.suggestion_text.config(state=tk.DISABLED)
        
        if done:
            self._show_summary_buttons()
    
    def _display_missed_words(self):
        """显示错过的单词或恭喜信息"""
        if not hasattr(self, 'summary_data') or not self.summary_data:
            return
            
        # 错词列表
        missed_words = self.summary_data['missed']
        
        if missed_words:
            missed_card = tk.LabelFrame(self.summary_frame, text="需要复习的单词", font=self.font_config['normal'], bg='white')
            missed_card.pack(fill=tk.X, pady=10, padx=5)
            
            missed_text = "、".join(missed_words)
            missed_words_label = tk.Label(
                missed_card,
                text=missed_text,
                font=self.font_config['normal'],
                bg='white',
                fg='#f44336',
                wraplength=600,
                justify=tk.LEFT
            )
            missed_words_label.pack(pady=5, anchor='w', padx=5)
        else:
            perfect_card = tk.LabelFrame(self.summary_frame, text="恭喜", font=self.font_config['normal'], bg='white')
            perfect_card.pack(fill=tk.X, pady=10, padx=5)
            
            perfect_label = tk.Label(
                perfect_card,
                text="太棒了！全部正确！",
                font=self.font_config['normal'],
                bg='white',
                fg='#4CAF50'
            )
            perfect_label.pack(pady=10, anchor='w', padx=5)
    
    def _create_suggestion_placeholder(self):
        """创建学习建议区域的占位符，显示"正在获取建议..."""
        # 导入TextFormatter
        from core.text_formatter import TextFormatter
        self.text_formatter = TextFormatter()
        
        # AI建议标签
        suggestion_label = tk.Label(
            self.summary_frame,
            text="学习建议:",
            font=self.font_config['normal'],
            bg='white',
            anchor='w'
        )
        suggestion_label.pack(pady=(15, 5), anchor='w', padx=5)
        
        # 创建ScrolledText组件作为占位符
        from tkinter import scrolledtext
        self.suggestion_text = scrolledtext.ScrolledText(
            self.summary_frame,
            height=20,
            wrap=tk.WORD,
            font=self.font_config['normal']
        )
        self.suggestion_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        # 显示"正在获取建议..."
        self.suggestion_text.insert(tk.END, "正在获取建议...")
        self.suggestion_text.config(state=tk.DISABLED)  # 设置为只读
    
    def _show_summary_buttons(self):
        """显示总结页面的按钮"""
        # 按钮区域
        buttons_frame = tk.Frame(self.main_frame, bg='white')
        buttons_frame.pack(pady=40)

        review_button = tk.Button(
            buttons_frame,
            text="复习错词",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._review_missed_words,
            bg='#FF9800',
            fg='white',
            state=tk.NORMAL if self.summary_data['missed'] else tk.DISABLED
        )
        review_button.pack(side=tk.LEFT, padx=10)

        new_button = tk.Button(
            buttons_frame,
            text="重新开始",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._show_mode_selection,
            bg='#4CAF50',
            fg='white'
        )
        new_button.pack(side=tk.LEFT, padx=10)

    def _review_missed_words(self):
        """复习错词"""
        summary = self.dictation_manager.summarize()
        if summary['missed']:
            # 设置为队列模式，使用错词列表
            self.current_mode = "queue"
            self.dictation_manager.current_queue = summary['missed']
            self.dictation_manager.current_queue_index = 0
            self.dictation_manager.current_mode = "queue"

            # 重新创建练习界面
            self._create_exercise_ui()
            self._next_word_in_queue()

    def _check_answer(self):
        """检查答案"""
        user_input = self.word_entry.get().strip()

        if not user_input:
            messagebox.showwarning("提示", "请输入单词后再检查。")
            return

        # 停止计时器
        if hasattr(self, 'timer_id'):
            self._stop_timer()

        # 检查拼写
        is_correct = self.word_manager.check_spelling(
            self.current_word, user_input)

        # 计算拼写所用时间
        from datetime import datetime
        time_spent = 0
        if self.word_start_time:
            time_spent = (datetime.now() - \
                          self.word_start_time).total_seconds()

        # 使用dictation_manager记录结果
        self.dictation_manager.record_result(
            self.current_word, is_correct, time_spent)

        # 记录到本次练习结果
        self.session_results.append({
            'word': self.current_word,
            'input': user_input,
            'correct': is_correct,
            'time_spent': time_spent,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 显示结果
        if is_correct:
            self.result_var.set(f"✓ 正确！")
            self.result_label.config(fg='#4CAF50')
            log_info(f"听写正确: {self.current_word}")
        else:
            # 使用兼容方法获取翻译（get_translation 接受单个参数）
            translation = self.word_manager.get_word_translation(self.current_word) or ""
            self.result_var.set(
                f"✗ 错误！正确答案: {self.current_word} ({translation})")
            self.result_label.config(fg='#f44336')
            # 记录并追踪错误单词
            try:
                if hasattr(self.word_manager, 'add_wrong_word'):
                    self.word_manager.add_wrong_word(self.current_word)
            except Exception:
                pass
            log_wrong_word(self.current_word, user_input)



        # 更新状态栏
        progress = self.word_manager.get_progress()
        self.status_var.set(
            f"正确率: {progress.get('correct_rate', 0) * 100:.1f}%")

        # 根据模式决定下一步
        if self.current_mode == "single":
            # 单个模式，根据全局/本地设置决定是否自动跳转
            try:
                mode = self.settings_manager.get_auto_mode('word_learning') if self.settings_manager else 'manual'
            except Exception:
                mode = 'manual'

            effective_auto = True if mode == 'auto' else self.auto_next

            if effective_auto:
                # 自动跳转到下一个单词
                self.main_frame.after(2000, self._next_word)
            else:
                # 手动模式，显示下一个按钮
                try:
                    self.next_button.pack(side=tk.LEFT, padx=10)
                except Exception:
                    pass
        else:
            # 队列模式，延迟显示下一个单词或总结
            # 使用队列索引进行精确判断，避免索引越界
            if self.dictation_manager.current_queue_index < len(self.dictation_manager.current_queue):
                self.main_frame.after(2000, self._next_word_in_queue)
            else:
                self.main_frame.after(2000, self._show_summary)

    def _skip_word(self):
        """跳过当前单词"""
        # 停止计时器
        if hasattr(self, 'timer_id'):
            self._stop_timer()

        # 计算跳过所用时间
        from datetime import datetime
        time_spent = 0
        if self.word_start_time:
            time_spent = (datetime.now() - \
                          self.word_start_time).total_seconds()

        # 使用skip_current_word方法来处理跳过逻辑
        self.dictation_manager.skip_current_word(self.current_word, time_spent)

        self.result_var.set("⏭️ 已跳过: " + self.current_word)
        self.result_label.config(fg='#FF9800')
        log_info("跳过单词: " + self.current_word)

        # 记录到本次练习结果
        self.session_results.append({
            'word': self.current_word,
            'input': 'skipped',
            'correct': False,
            'time_spent': time_spent,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 根据模式决定下一步
        if self.current_mode == "single":
            # 单个模式，显示下一个单词
            self.main_frame.after(1000, self._next_word)
        else:
            # 队列模式，直接获取下一个单词
            self.main_frame.after(1000, self._next_word_in_queue)