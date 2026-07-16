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

        # 题目区域：所有题目 + 选项 一次性展示（类似完形填空的答题方式）
        qa_frame = tk.LabelFrame(content_frame, text="题目", font=self.font_config['normal'])
        qa_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        qa_scroll_frame, qa_inner, _, _ = create_scrollable_frame(qa_frame)
        qa_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.questions_inner = qa_inner

        # 已选答案汇总 + 提交按钮
        answer_frame = tk.Frame(content_frame)
        answer_frame.pack(fill=tk.X, pady=(0, 10))

        self.selected_answers_label = tk.Label(answer_frame, text="已选答案：",
                                               font=self.font_config['normal'], anchor=tk.W)
        self.selected_answers_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.submit_button = tk.Button(answer_frame, text="提交答案", command=self._submit_answer,
                                     font=self.font_config['button'], bg="#2196F3", fg="white",
                                     width=12, height=1, state=tk.DISABLED)
        self.submit_button.pack(side=tk.RIGHT, padx=10, pady=5)

        # 结果显示区域
        result_frame = tk.LabelFrame(content_frame, text="结果", font=self.font_config['normal'])
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                                    height=8, bg="#f0f0f0", state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 当前问题索引
        self.current_question_index = 0
        self.user_answers = []
        self.question_results = []
        self.question_vars = []
        self.question_result_labels = []
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

                    # 显示题目（所有题目 + 选项，类似完形填空）
                    questions = test_data.get('questions', [])
                    self._display_questions(questions)

                    # 初始化
                    self.current_question_index = 0
                    self.user_answers = ["" for _ in questions]
                    self.question_results = [None for _ in questions]

                    # 启用提交按钮
                    self.submit_button.config(state=tk.NORMAL)

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

    def _extract_options(self, question_text):
        """从题目文本中提取题干和 A/B/C/D 选项"""
        import re
        # 去除可能的 "Multiple Choice:" 前缀
        question_text = re.sub(r'Multiple Choice:\s*', '', question_text, flags=re.IGNORECASE).strip()
        # 按 A./B./C./D. 切分，保留选项字母
        parts = re.split(r'\s*([A-D])\.\s*', question_text)
        stem = parts[0].strip()
        options = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                options.append((parts[i], parts[i + 1].strip()))
        return stem, options

    def _display_questions(self, questions):
        """一次性展示全部题目，每题内嵌 A/B/C/D 单选按钮（类似完形填空）"""
        # 清空旧题目
        for widget in self.questions_inner.winfo_children():
            widget.destroy()
        self.question_vars = []
        self.question_result_labels = []

        for idx, question in enumerate(questions, 1):
            stem, options = self._extract_options(question)

            q_frame = tk.LabelFrame(self.questions_inner, text=f"第{idx}题",
                                    font=self.font_config['normal'])
            q_frame.pack(fill=tk.X, pady=5, padx=2)

            stem_label = tk.Label(q_frame, text=stem, font=self.font_config['normal'],
                                  wraplength=640, justify=tk.LEFT, anchor=tk.W)
            stem_label.pack(fill=tk.X, padx=8, pady=4)

            var = tk.StringVar(value="")
            self.question_vars.append(var)
            var.trace_add('write', lambda *args: self._update_selected_answers_label())

            opts_frame = tk.Frame(q_frame)
            opts_frame.pack(fill=tk.X, padx=8, pady=4)

            available_letters = {o[0] for o in options}
            for letter in ['A', 'B', 'C', 'D']:
                if letter in available_letters:
                    opt_text = next(o[1] for o in options if o[0] == letter)
                    text = f"{letter}. {opt_text}"
                    st = tk.NORMAL
                else:
                    text = f"{letter}. （无选项）"
                    st = tk.DISABLED
                rb = tk.Radiobutton(opts_frame, text=text, variable=var, value=letter,
                                   font=self.font_config['normal'], anchor=tk.W, state=st)
                rb.pack(fill=tk.X, pady=2)

            result_label = tk.Label(q_frame, text="", font=('SimHei', 11),
                                   justify=tk.LEFT, anchor=tk.W, wraplength=640)
            result_label.pack(fill=tk.X, padx=8, pady=4)
            self.question_result_labels.append(result_label)

        self._update_selected_answers_label()

    def _update_selected_answers_label(self):
        """更新已选答案显示"""
        if not hasattr(self, 'question_vars') or not self.question_vars:
            self.selected_answers_label.config(text="已选答案：")
            return
        selected = [v.get() if v.get() else "_" for v in self.question_vars]
        self.selected_answers_label.config(text=f"已选答案：{','.join(selected)}")

    def _submit_answer(self):
        """提交全部答案"""
        try:
            if not hasattr(self, 'question_vars') or not self.question_vars:
                messagebox.showwarning("提示", "没有可提交的题目")
                return

            selected = [v.get() for v in self.question_vars]
            if any(s == "" for s in selected):
                messagebox.showwarning("提示", "请回答所有题目后再提交")
                return

            self.user_answers = selected

            # 提交所有答案
            total_score, results = self.reading_module.submit_all_answers(self.user_answers)
            self.question_results = results

            # 更新每题结果
            for i, res in enumerate(results):
                if i < len(self.question_result_labels) and res:
                    is_correct = res.get('is_correct', False)
                    color = "#2e7d32" if is_correct else "#c62828"
                    mark = "✓ 正确" if is_correct else "✗ 错误"
                    text = f"{mark}\n解析：{res.get('explanation', '')}"
                    self.question_result_labels[i].config(text=text, fg=color)

            messagebox.showinfo("总分", f"测试完成！\n总分：{total_score:.1f}/100")

            # 禁用提交按钮
            self.submit_button.config(state=tk.DISABLED)

        except Exception as e:
            log_error(f"提交答案失败: {str(e)}")
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

        # 清空题目区
        if hasattr(self, 'questions_inner'):
            for widget in self.questions_inner.winfo_children():
                widget.destroy()
        self.question_vars = []
        self.question_result_labels = []

        # 重置已选答案显示
        if hasattr(self, 'selected_answers_label') and self.selected_answers_label:
            self.selected_answers_label.config(text="已选答案：")

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)

        # 禁用提交按钮
        self.submit_button.config(state=tk.DISABLED)

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
