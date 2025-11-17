import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_error
from ui.components.loading_dialog import LoadingDialog
from ui.components.scrollable_frame import create_scrollable_frame


class ReadingComprehensionPage(tk.Frame):
    """阅读理解页面"""

    def __init__(self, parent, controller):
        """初始化阅读理解页面

        Args:
            parent: 父窗口组件
            controller: 控制器（主窗口）
        """
        super().__init__(parent)
        self.controller = controller
        # 延迟初始化ReadingComprehensionModule，避免在页面加载时立即连接AI
        self.reading_module = None

        # 设置中文字体
        self.font_config = {
            'header': ('SimHei', 14, 'bold'),
            'normal': ('SimHei', 12),
            'button': ('SimHei', 12)
        }

        # 创建UI
        self._create_ui()

        # 页面显示时才刷新状态信息
        # 注册显示回调
        self.on_show = self._on_show_page

    def _on_show_page(self):
        """页面显示时执行的操作，延迟初始化模块"""
        # 延迟初始化模块，使用控制器提供的WordManager实例
        if self.reading_module is None:
            from modules.reading_comprehension import ReadingComprehensionModule
            self.reading_module = ReadingComprehensionModule(word_manager=self.controller.word_manager)

        # 刷新状态信息
        self._update_status()

    def _create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 顶部控制面板
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))

        # 模式选择
        mode_frame = tk.Frame(control_frame)
        mode_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(mode_frame, text="模式:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="auto")
        tk.Radiobutton(mode_frame, text="自动", variable=self.mode_var, value="auto",
                      font=self.font_config['normal']).grid(row=0, column=1, padx=5)
        tk.Radiobutton(mode_frame, text="在线", variable=self.mode_var, value="online",
                      font=self.font_config['normal']).grid(row=0, column=2, padx=5)
        tk.Radiobutton(mode_frame, text="离线", variable=self.mode_var, value="offline",
                      font=self.font_config['normal']).grid(row=0, column=3, padx=5)

        # 难度选择
        level_frame = tk.Frame(control_frame)
        level_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(level_frame, text="难度:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.level_var = tk.StringVar(value="高中")
        level_options = ["初中", "高中", "大学", "专升本", "考研"]
        level_combo = ttk.Combobox(level_frame, textvariable=self.level_var, values=level_options,
                                  font=self.font_config['normal'], width=8)
        level_combo.grid(row=0, column=1, padx=5)
        level_combo.current(1)

        # 长度选择
        length_frame = tk.Frame(control_frame)
        length_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(length_frame, text="长度:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.length_var = tk.StringVar(value="短篇")
        length_options = ["短篇", "长篇"]
        length_combo = ttk.Combobox(length_frame, textvariable=self.length_var, values=length_options,
                                  font=self.font_config['normal'], width=8)
        length_combo.grid(row=0, column=1, padx=5)
        length_combo.current(0)

        # 题目数量
        qty_frame = tk.Frame(control_frame)
        qty_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(qty_frame, text="题目数:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.qty_var = tk.StringVar(value="5")
        qty_options = ["3", "4", "5", "6", "7", "8", "9", "10"]
        qty_combo = ttk.Combobox(qty_frame, textvariable=self.qty_var, values=qty_options,
                                font=self.font_config['normal'], width=5)
        qty_combo.grid(row=0, column=1, padx=5)
        qty_combo.current(2)

        # 主题输入
        topic_frame = tk.Frame(control_frame)
        topic_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        tk.Label(topic_frame, text="主题:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.topic_entry = tk.Entry(topic_frame, font=self.font_config['normal'], width=30)
        self.topic_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.topic_entry.insert(0, "通用")

        # 开始按钮
        self.start_button = tk.Button(control_frame, text="开始新练习", command=self._start_new_test,
                                     font=self.font_config['button'], bg="#4CAF50", fg="white",
                                     width=12, height=1)
        self.start_button.pack(side=tk.RIGHT, padx=10)

        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = tk.Label(control_frame, textvariable=self.status_var, font=self.font_config['normal'])
        status_label.pack(side=tk.RIGHT, padx=10)

        # 内容区域 - 使用通用滚动框架
        content_scroll_frame, content_frame, _, _ = create_scrollable_frame(main_frame)
        content_scroll_frame.pack(fill=tk.BOTH, expand=True)

        # 文章标题框架
        title_frame = tk.Frame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # 标题左侧显示题目名称
        self.article_title = tk.Label(title_frame, text="阅读文章", font=self.font_config['header'], anchor=tk.W)
        self.article_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 标题右侧添加删除按钮
        self.delete_button = tk.Button(title_frame, text="🗑️删除", command=self._on_delete_question,
                                     font=self.font_config['button'], fg="#f44336", relief=tk.FLAT,
                                     state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=10)

        # 文章内容
        self.article_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                                     height=15, bg="#f5f5f5", state=tk.DISABLED)
        self.article_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 题目和答案区域
        qa_frame = tk.Frame(content_frame)
        qa_frame.pack(fill=tk.BOTH, expand=True)

        # 左半部分：题目
        questions_frame = tk.LabelFrame(qa_frame, text="题目", font=self.font_config['normal'])
        questions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.questions_text = scrolledtext.ScrolledText(questions_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                                      height=15, bg="#f0f0f0", state=tk.DISABLED)
        self.questions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 右半部分：答案输入和结果
        answers_frame = tk.LabelFrame(qa_frame, text="答案与结果", font=self.font_config['normal'])
        answers_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 当前问题标签
        self.current_question_var = tk.StringVar(value="请开始练习")
        current_question_label = tk.Label(answers_frame, textvariable=self.current_question_var,
                                        font=self.font_config['normal'], anchor=tk.W)
        current_question_label.pack(fill=tk.X, padx=5, pady=5)

        # 答案输入
        answer_input_frame = tk.Frame(answers_frame)
        answer_input_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(answer_input_frame, text="答案:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.answer_entry = tk.Entry(answer_input_frame, font=self.font_config['normal'], width=30)
        self.answer_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)

        # 按钮区域
        buttons_frame = tk.Frame(answers_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        self.prev_button = tk.Button(buttons_frame, text="上一题", command=self._prev_question,
                                   font=self.font_config['button'], width=10, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(buttons_frame, text="下一题", command=self._next_question,
                                   font=self.font_config['button'], width=10, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.submit_button = tk.Button(buttons_frame, text="提交当前题", command=self._submit_current_question,
                                     font=self.font_config['button'], bg="#2196F3", fg="white",
                                     width=12, state=tk.DISABLED)
        self.submit_button.pack(side=tk.RIGHT, padx=5)

        # 全部提交按钮
        self.submit_all_button = tk.Button(buttons_frame, text="全部提交", command=self._submit_all_questions,
                                         font=self.font_config['button'], bg="#FF9800", fg="white",
                                         width=12, state=tk.DISABLED)
        self.submit_all_button.pack(side=tk.RIGHT, padx=5)

        # 结果显示
        self.result_text = scrolledtext.ScrolledText(answers_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                                    height=6, bg="#e8f5e9", state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 当前问题索引
        self.current_question_index = 0
        self.user_answers = []
        self.question_results = []
        self.test_data = None

    # 滚动相关方法已通过create_scrollable_frame实现

    def _update_status(self):
        """更新状态信息"""
        try:
            stats = self.reading_module.get_test_statistics()
            mode = stats.get('current_mode', '未知')
            ai_available = "可用" if stats.get('ai_available', False) else "不可用"
            total_tests = stats.get('total_tests', 0)

            self.status_var.set(f"模式: {mode} | AI: {ai_available} | 离线题目: {total_tests}")

        except Exception as e:
            log_error(f"更新状态失败: {str(e)}")

    def _on_delete_question(self):
        """处理删除题目的逻辑"""
        if not hasattr(self, 'current_test_id') or self.current_test_id is None:
            messagebox.showwarning("提示", "没有可删除的题目")
            return

        # 弹出确认对话框
        confirm = messagebox.askyesno(
            "确认删除",
            "确定要删除这个阅读理解题目吗？此操作不可撤销，但数据会被记录以便恢复。"
        )

        if confirm:
            try:
                # 执行删除
                from modules.database import ComprehensionDatabase
                db = ComprehensionDatabase()
                success = db.delete_reading_comprehension(self.current_test_id)

                if success:
                    log_info(f"用户删除了阅读理解题目，ID: {self.current_test_id}")
                    messagebox.showinfo("成功", "题目已成功删除")
                    # 清空界面
                    self._clear_ui()
                else:
                    messagebox.showerror("错误", "删除题目失败，请重试")
                    log_error(f"删除阅读理解题目失败，ID: {self.current_test_id}")
            except Exception as e:
                messagebox.showerror("错误", f"删除题目时出错: {str(e)}")
                log_error(f"删除阅读理解题目时发生异常: {str(e)}")

    def _start_new_test(self):
        """开始新的测试"""
        try:
            # 获取用户设置
            mode = self.mode_var.get()
            level = self.level_var.get()
            length = self.length_var.get()
            question_count = int(self.qty_var.get())
            topic = self.topic_entry.get() or "通用"

            # 转换模式
            if mode == "auto":
                mode = None

            # 清空界面
            self._clear_ui()

            # 定义生成测试题目的任务函数
            def generate_test_task():
                # 在单独线程中调用AI功能
                return self.reading_module.start_new_test(
                    mode=mode, level=level, length=length, question_count=question_count, topic=topic
                )

            # 创建加载对话框
            loading_dialog = LoadingDialog(
                self.controller.root,
                title="正在生成题目",
                message="AI正在创建适合您的阅读理解题目，请稍候..."
            )

            # 运行异步任务
            try:
                test_data = loading_dialog.run_task(generate_test_task)

                if test_data:
                    self.test_data = test_data

                    # 更新标题和保存当前题目ID
                    self.article_title.config(text="阅读文章")
                    self.current_test_id = test_data.get('id')

                    # 启用删除按钮（只有离线模式下的题目可以删除）
                    if self.reading_module.get_mode() == 'offline':
                        self.delete_button.config(state=tk.NORMAL)
                    else:
                        self.delete_button.config(state=tk.DISABLED)

                    # 显示文章内容
                    article = test_data.get('article', '')
                    self.article_text.config(state=tk.NORMAL)
                    self.article_text.delete(1.0, tk.END)
                    self.article_text.insert(tk.END, article)
                    self.article_text.config(state=tk.DISABLED)

                    # 显示题目
                    questions = test_data.get('questions', [])
                    self.questions_text.config(state=tk.NORMAL)
                    self.questions_text.delete(1.0, tk.END)

                    for i, question in enumerate(questions, 1):
                        # 插入问题标题（只保留问题部分）
                        if "Multiple Choice:" in question:
                            # 提取问题部分
                            question_part = question.split("Multiple Choice:")[0].strip()
                            self.questions_text.insert(tk.END, f"第{i}题: {question_part}\n")

                            # 提取选项部分
                            options_part = question.split("Multiple Choice:")[1].strip()
                            # 分割选项 (A. B. C. D. 格式)
                            import re
                            options = re.split(r'([A-D]\.)', options_part)

                            # 处理分割后的选项，跳过空字符串
                            for j in range(1, len(options), 2):
                                if j+1 < len(options):
                                    self.questions_text.insert(tk.END, f"{options[j]} {options[j+1].strip()}\n")
                        else:
                            # 普通问题，直接显示
                            self.questions_text.insert(tk.END, f"第{i}题: {question}\n")

                        self.questions_text.insert(tk.END, "\n")

                    self.questions_text.config(state=tk.DISABLED)

                    # 初始化
                    self.current_question_index = 0
                    self.user_answers = ["" for _ in questions]
                    self.question_results = [None for _ in questions]

                    # 显示第一个问题
                    self._show_current_question()

                    # 启用按钮
                    self._update_buttons_state()

                    log_info(f"成功开始新的阅读理解练习，ID: {test_data.get('id')}")
                    messagebox.showinfo("提示", "题目已准备好，请开始答题！")
                else:
                    # 检查是否是离线模式且没有题目
                    if mode == "offline" or (mode is None and not self.reading_module.ai_service.is_ai_available()):
                        messagebox.showerror("错误", "离线模式下数据库中没有题目，请先联网生成内容！")
                    else:
                        messagebox.showerror("错误", "生成题目失败，请稍后重试！")

                    # 重置界面
                    self._clear_ui()
            except Exception as e:
                log_error(f"生成题目时出错: {str(e)}")
                messagebox.showerror("错误", f"生成题目失败: {str(e)}")
                # 重置界面
                self._clear_ui()
        except Exception as e:
            log_error(f"开始新测试失败: {str(e)}")
            messagebox.showerror("错误", f"开始新测试失败: {str(e)}")

    def _show_current_question(self):
        """显示当前问题"""
        if not self.test_data:
            return

        questions = self.test_data.get('questions', [])
        if 0 <= self.current_question_index < len(questions):
            question = questions[self.current_question_index]

            # 更新当前问题标签
            self.current_question_var.set(f"第{self.current_question_index + 1}题/{len(questions)}")

            # 显示用户之前的答案
            self.answer_entry.delete(0, tk.END)
            if self.user_answers[self.current_question_index]:
                self.answer_entry.insert(0, self.user_answers[self.current_question_index])

            # 显示结果（如果有）
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)

            if self.question_results[self.current_question_index]:
                result = self.question_results[self.current_question_index]
                self.result_text.insert(tk.END, f"评估: {result['evaluation']}\n\n")
                self.result_text.insert(tk.END, f"解析: {result['explanation']}")

            self.result_text.config(state=tk.DISABLED)

    def _prev_question(self):
        """上一题"""
        if self.current_question_index > 0:
            # 保存当前答案
            self.user_answers[self.current_question_index] = self.answer_entry.get().strip()

            self.current_question_index -= 1
            self._show_current_question()
            self._update_buttons_state()

    def _next_question(self):
        """下一题"""
        if self.test_data and self.current_question_index < len(self.test_data.get('questions', [])) - 1:
            # 保存当前答案
            self.user_answers[self.current_question_index] = self.answer_entry.get().strip()

            self.current_question_index += 1
            self._show_current_question()
            self._update_buttons_state()

    def _update_buttons_state(self):
        """更新按钮状态"""
        if not self.test_data:
            return

        total_questions = len(self.test_data.get('questions', []))

        # 更新导航按钮状态
        self.prev_button.config(state=tk.NORMAL if self.current_question_index > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_question_index < total_questions - 1 else tk.DISABLED)

        # 更新提交按钮状态
        self.submit_button.config(state=tk.NORMAL)
        self.submit_all_button.config(state=tk.NORMAL)

    def _submit_current_question(self):
        """提交当前问题的答案"""
        try:
            user_answer = self.answer_entry.get().strip()

            if not user_answer:
                messagebox.showwarning("提示", "请输入答案！")
                return

            # 提交答案
            is_correct, evaluation, explanation = self.reading_module.submit_question_answer(
                self.current_question_index, user_answer
            )

            # 保存结果
            self.question_results[self.current_question_index] = {
                'is_correct': is_correct,
                'evaluation': evaluation,
                'explanation': explanation
            }

            # 显示结果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"评估: {evaluation}\n\n")
            self.result_text.insert(tk.END, f"解析: {explanation}")
            self.result_text.config(state=tk.DISABLED)

            # 提示用户
            if is_correct:
                messagebox.showinfo("提示", "答案正确！")
            else:
                messagebox.showinfo("提示", "请查看解析")

        except Exception as e:
            log_error(f"提交当前问题答案失败: {str(e)}")
            messagebox.showerror("错误", f"提交答案失败: {str(e)}")

    def _submit_all_questions(self):
        """提交所有问题的答案"""
        try:
            # 检查是否所有问题都有答案
            self.user_answers[self.current_question_index] = self.answer_entry.get().strip()

            empty_indices = [i for i, ans in enumerate(self.user_answers) if not ans.strip()]

            if empty_indices:
                if messagebox.askyesno("确认", f"有{len(empty_indices)}道题未作答，是否继续提交？"):
                    # 未作答的题目填写默认值
                    for i in empty_indices:
                        self.user_answers[i] = "未作答"
                else:
                    return

            # 提交所有答案
            total_score, results = self.reading_module.submit_all_answers(self.user_answers)

            # 更新所有结果
            self.question_results = results

            # 显示总分
            messagebox.showinfo("总分", f"测试完成！\n总分: {total_score:.1f}/100")

            # 更新当前问题的结果显示
            self._show_current_question()

            # 禁用提交按钮
            self.submit_button.config(state=tk.DISABLED)
            self.submit_all_button.config(state=tk.DISABLED)

        except Exception as e:
            log_error(f"提交所有问题答案失败: {str(e)}")
            messagebox.showerror("错误", f"提交答案失败: {str(e)}")

    def _clear_ui(self):
        """清空界面"""
        # 清空标题和题目ID
        self.article_title.config(text="阅读文章")
        self.current_test_id = None

        # 禁用删除按钮
        self.delete_button.config(state=tk.DISABLED)

        self.article_text.config(state=tk.NORMAL)
        self.article_text.delete(1.0, tk.END)
        self.article_text.config(state=tk.DISABLED)

        # 清空题目
        self.questions_text.config(state=tk.NORMAL)
        self.questions_text.delete(1.0, tk.END)
        self.questions_text.config(state=tk.DISABLED)

        # 重置状态
        self.current_question_var.set("请开始练习")
        self.answer_entry.delete(0, tk.END)

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)

        # 禁用按钮
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)
        self.submit_all_button.config(state=tk.DISABLED)

        # 重置变量
        self.current_question_index = 0
        self.user_answers = []
        self.question_results = []
        self.test_data = None

    def on_show(self):
        """页面显示时的回调"""
        # 刷新状态信息
        self._update_status()
        # 清空界面
        self._clear_ui()
