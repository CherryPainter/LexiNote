import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_player import AudioPlayer
from logger import log_info, log_wrong_word, log_error
from core.dictation import DictationManager


class DictationPage(tk.Frame):
    """听写练习页面，支持单个听写和队列听写模式"""

    def __init__(self, parent, word_manager, settings_manager=None, font_config=None):
        """初始化听写页面"""
        super().__init__(parent, bg='white')
        self.parent = parent
        self.word_manager = word_manager
        self.settings_manager = settings_manager
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

        # 开始练习
        self.word_manager.start_exercise("听写")

    def _create_ui(self):
        """创建用户界面，支持模式选择和练习界面"""
        # 主框架
        self.main_frame = tk.Frame(self, bg='white')
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)

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

        # 过滤选项
        filter_frame = tk.Frame(mode_frame, bg='white')
        filter_frame.pack(fill=tk.X, padx=50, pady=10)

        self.filter_var = tk.BooleanVar(value=False)
        filter_check = tk.Checkbutton(
            filter_frame,
            text="只练习熟词",
            variable=self.filter_var,
            font=self.font_config['normal'],
            bg='white'
        )
        filter_check.pack(side=tk.LEFT, padx=5)

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
            self.auto_next = self.auto_next_var.get()

        # 获取来源
        source_text = self.source_var.get()

        # 设置当前来源
        if source_text == "今日学习单词":
            self.current_source = "today"

            # 检查是否有今日学习的单词
            has_today_words = self._has_today_words()

            # 如果没有今日学习单词，则提示用户
            if not has_today_words:
                # 检查是否完成了今日学习进度（即使没有单词记录）
                progress_completed = False
                if hasattr(self.word_manager, 'check_today_progress_completed'):
                    progress_completed = self.word_manager.check_today_progress_completed()

                # 如果完成了进度但没有单词，可能是系统记录问题
                if progress_completed:
                    response = messagebox.askyesno("学习记录问题", 
                                                  "系统显示您已完成今日学习，但未找到今日学习的单词记录。\n\n建议：\n1. 重新学习少量单词以更新记录\n2. 或选择其他来源进行听写\n\n是否现在去学习？")
                    if response:
                        # 如果用户选择去学习，切换到学习页面
                        self.parent.show_page("learning")
                else:
                    response = messagebox.askyesno("学习进度提醒", 
                                                  "您今天似乎还没有学习单词或学习记录未保存。\n\n建议：\n1. 先去学习单词\n2. 或选择其他来源进行听写\n\n是否现在去学习？")
                    if response:
                        # 如果用户选择去学习，切换到学习页面
                        self.parent.show_page("learning")
                        return
                    else:
                        # 如果用户不选择学习，不阻止其选择其他来源
                        return

            # 如果有今日学习单词，但未完成进度，则给予友好提示但不阻止
            elif has_today_words and hasattr(self.word_manager, 'check_today_progress_completed'):
                if not self.word_manager.check_today_progress_completed():
                    messagebox.showinfo(
                        "提示", "您今天已学习了一些单词，但可能尚未完成所有计划的学习内容。\n\n您可以继续进行听写练习。")
        elif source_text == "全词库随机":
            self.current_source = "library"
        else:
            self.current_source = "familiar"

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

        # 根据模式开始练习
        if self.current_mode == "single":
            self._next_word()
        else:
            # 构建队列
            filter_familiar = self.filter_var.get()
            self.dictation_manager.build_queue(
                source=self.current_source,
                limit=self.batch_size,
                filter_familiar=filter_familiar
            )
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

        # 例句显示区域
        self.example_var = tk.StringVar(value="")
        self.example_label = tk.Label(
            input_frame,
            textvariable=self.example_var,
            font=self.font_config['normal'],
            bg='white',
            fg='#666666',
            wraplength=600,
            justify=tk.LEFT
        )

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

        # 隐藏例句
        if hasattr(self, 'example_label'):
            self.example_var.set("")
            self.example_label.pack_forget()

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

        # 隐藏例句
        if hasattr(self, 'example_label'):
            self.example_var.set("")
            self.example_label.pack_forget()

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

        # 获取总结数据
        summary = self.dictation_manager.summarize()

        # 总结信息框架
        summary_frame = tk.Frame(self.main_frame, bg='white')
        summary_frame.pack(pady=20, padx=50, fill=tk.X)

        # 正确率
        accuracy_label = tk.Label(
            summary_frame,
            text=f"正确率: {summary['accuracy'] * 100:.1f}% ({summary['correct']}/{summary['total']})",
            font=self.font_config['normal'],
            bg='white'
        )
        accuracy_label.pack(pady=10, anchor='w')

        # 错词列表
        if summary['missed']:
            missed_label = tk.Label(
                summary_frame,
                text="需要复习的单词:",
                font=self.font_config['normal'],
                bg='white',
                anchor='w'
            )
            missed_label.pack(pady=(15, 5), anchor='w')

            missed_text = "、".join(summary['missed'])
            missed_words_label = tk.Label(
                summary_frame,
                text=missed_text,
                font=self.font_config['normal'],
                bg='white',
                fg='#f44336',
                wraplength=600,
                justify=tk.LEFT
            )
            missed_words_label.pack(pady=5, anchor='w')
        else:
            perfect_label = tk.Label(
                summary_frame,
                text="太棒了！全部正确！",
                font=self.font_config['normal'],
                bg='white',
                fg='#4CAF50'
            )
            perfect_label.pack(pady=10, anchor='w')

        # AI建议
        if summary['suggestion']:
            suggestion_label = tk.Label(
                summary_frame,
                text="学习建议:",
                font=self.font_config['normal'],
                bg='white',
                anchor='w'
            )
            suggestion_label.pack(pady=(15, 5), anchor='w')

            suggestion_text_label = tk.Label(
                summary_frame,
                text=summary['suggestion'],
                font=self.font_config['normal'],
                bg='white',
                fg='#2196F3',
                wraplength=600,
                justify=tk.LEFT
            )
            suggestion_text_label.pack(pady=5, anchor='w')

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
            state=tk.NORMAL if summary['missed'] else tk.DISABLED
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
            translation = self.word_manager.word_dict.get(
                self.current_word, "")
            self.result_var.set(
                f"✗ 错误！正确答案: {self.current_word} ({translation})")
            self.result_label.config(fg='#f44336')
            log_wrong_word(self.current_word, user_input)

        # 显示例句（如果有）
        if hasattr(self, 'example_var'):
            example = self.word_manager.get_word_example(self.current_word)
            if example:
                self.example_var.set(f"例句: {example}")
                self.example_label.pack(pady=10)
            else:
                self.example_var.set("")
                self.example_label.pack_forget()

        # 更新状态栏
        progress = self.word_manager.get_progress()
        self.status_var.set(
            f"正确率: {progress.get('correct_rate', 0) * 100:.1f}%")

        # 根据模式决定下一步
        if self.current_mode == "single":
            # 单个模式，根据用户设置决定是否自动跳转
            if self.auto_next:
                # 自动跳转到下一个单词
                self.main_frame.after(2000, self._next_word)
            else:
                # 手动模式，显示下一个按钮
                self.next_button.pack(side=tk.LEFT, padx=10)
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