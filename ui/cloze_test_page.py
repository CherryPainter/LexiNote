import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.components.scrollable_frame import create_scrollable_frame, refresh_mousewheel
from ui.components.toast import show_toast
from ui.font_config import FontConfig

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_error
from ui.components.loading_dialog import LoadingDialog


class ClozeTestPage(tk.Frame):
    """完形填空页面"""

    def __init__(self, parent, controller):
        """初始化完形填空页面

        Args:
            parent: 父窗口组件
            controller: 控制器（主窗口）
        """
        super().__init__(parent)
        self.controller = controller
        # 延迟初始化ClozeTestModule，避免在页面加载时立即连接AI
        self.cloze_module = None

        # 设置中文字体（统一使用 FontConfig，自带全部默认值）
        self.font_config = FontConfig()

        # 创建UI
        self._create_ui()

        # 页面显示时才刷新状态信息
        # 注册显示回调
        self.on_show = self._on_show_page

    def _on_show_page(self):
        """页面显示时执行的操作，延迟初始化模块"""
        # 延迟初始化模块，使用控制器提供的WordManager实例
        if self.cloze_module is None:
            # 在后台线程中初始化ClozeTestModule，避免UI阻塞
            def init_cloze_module():
                from modules.cloze_test import ClozeTestModule
                self.cloze_module = ClozeTestModule(word_manager=self.controller.word_manager)
                # 初始化完成后，在主线程中更新状态
                self.after(0, self._update_status)

            # 创建并启动后台线程
            import threading
            init_thread = threading.Thread(target=init_cloze_module, daemon=True)
            init_thread.start()
        else:
            # 模块已初始化，直接刷新状态信息
            self._update_status()

    def _create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 顶部控制面板（分成「设置行」与「操作行」，避免横向空间不足时控件被截断）
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 16))

        # 设置行：模式 / 难度 / 主题
        settings_row = tk.Frame(control_frame)
        settings_row.pack(side=tk.TOP, fill=tk.X)

        # 模式选择
        mode_frame = tk.Frame(settings_row)
        mode_frame.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(mode_frame, text="模式:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="auto")
        tk.Radiobutton(mode_frame, text="自动", variable=self.mode_var, value="auto",
                       font=self.font_config['normal']).grid(row=0, column=1, padx=5)
        tk.Radiobutton(mode_frame, text="在线", variable=self.mode_var, value="online",
                       font=self.font_config['normal']).grid(row=0, column=2, padx=5)
        tk.Radiobutton(mode_frame, text="离线", variable=self.mode_var, value="offline",
                       font=self.font_config['normal']).grid(row=0, column=3, padx=5)

        # 难度选择
        level_frame = tk.Frame(settings_row)
        level_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(level_frame, text="难度:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.level_var = tk.StringVar(value="高中")
        level_options = ["初中", "高中", "大学", "专升本", "考研"]
        level_combo = ttk.Combobox(level_frame, textvariable=self.level_var, values=level_options,
                                   font=self.font_config['normal'], width=8)
        level_combo.grid(row=0, column=1, padx=5)
        level_combo.current(1)

        # 主题输入
        topic_frame = tk.Frame(settings_row)
        topic_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        tk.Label(topic_frame, text="主题:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W)
        self.topic_entry = tk.Entry(topic_frame, font=self.font_config['normal'])
        self.topic_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.topic_entry.insert(0, "通用")

        # 操作行：开始按钮 + 状态
        action_row = tk.Frame(control_frame)
        action_row.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))

        # 开始按钮
        self.start_button = tk.Button(action_row, text="开始新练习", command=self._start_new_test,
                                       font=self.font_config['button'], bg="#4CAF50", fg="white",
                                       width=12, height=1)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = tk.Label(action_row, textvariable=self.status_var, font=self.font_config['normal'])
        status_label.pack(side=tk.RIGHT, padx=10)

        # 内容区域 - 使用通用滚动框架为整个完型填空元素区添加滑动条
        content_scroll_frame, content_frame, _, _ = create_scrollable_frame(main_frame)
        content_scroll_frame.pack(fill=tk.BOTH, expand=True)
        self.content_scroll_frame = content_scroll_frame

        # 标题显示
        title_frame = tk.Frame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # 标题左侧显示题目名称
        self.title_label = tk.Label(title_frame, text="完形填空", font=self.font_config['header'], anchor=tk.W)
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 标题右侧添加删除按钮
        self.delete_button = tk.Button(title_frame, text="🗑️ 删除", command=self._on_delete_question,
                                       font=self.font_config['button'], fg="#f44336", relief=tk.FLAT,
                                       state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=10)

        # 文章内容（自适应高度，无自带滚动条，整页统一滚动）
        self.article_text = tk.Text(content_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                    height=8, bg="#f5f5f5", state=tk.DISABLED, relief=tk.FLAT)
        self.article_text.pack(fill=tk.X, expand=False, pady=(0, 10))

        # 选项区域
        options_frame = tk.LabelFrame(content_frame, text="选项", font=self.font_config['header'])
        options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 选项内容
        self.options_frame = tk.Frame(options_frame)
        self.options_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 答案输入和提交
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

        self.result_text = tk.Text(result_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                    height=4, bg="#f0f0f0", state=tk.DISABLED, relief=tk.FLAT)
        self.result_text.pack(fill=tk.X, expand=False, padx=5, pady=5)

    def _fit_text_height(self, text_widget, max_height=40, min_height=4):
        """根据内容行数自适应文本框高度（避免内部滚动条，整页统一滚动）"""
        try:
            lines = int(text_widget.index("end-1c").split(".")[0])
        except Exception:
            lines = 0
        height = max(min_height, min(lines + 1, max_height))
        text_widget.config(height=height)

    def _set_text_content(self, text_widget, content, max_height=40, min_height=4):
        """写入文本框内容并自适应高度（内容区域为只读）"""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        self._fit_text_height(text_widget, max_height, min_height)

    def _update_status(self):
        """更新状态信息"""
        try:
            stats = self.cloze_module.get_test_statistics()
            mode = stats.get('current_mode', '未知')
            ai_available = "可用" if stats.get('ai_available', False) else "不可用"
            total_tests = stats.get('total_tests', 0)

            self.status_var.set(f"模式: {mode} | AI: {ai_available} | 离线题目: {total_tests}")

        except Exception as e:
            log_error(f"更新状态失败: {str(e)}")

    def _start_new_test(self):
        """开始新的测试"""
        try:
            # 获取用户设置
            mode = self.mode_var.get()
            level = self.level_var.get()
            topic = self.topic_entry.get().strip()

            # 转换模式
            if mode == "auto":
                mode = None

            # 清空界面
            self._clear_ui()

            # 定义生成测试题目的任务函数
            def generate_test_task():
                # 在单独线程中调用AI功能
                return self.cloze_module.start_new_test(mode=mode, level=level, topic=topic)

            # 创建加载对话框
            loading_dialog = LoadingDialog(
                self.controller.root,
                title="正在生成题目",
                message="AI正在创建适合您的完形填空题目，请稍候..."
            )

            # 运行异步任务
            try:
                test_data = loading_dialog.run_task(generate_test_task)

                if test_data:
                    # 更新标题和保存当前题目ID
                    self.title_label.config(text=test_data.get('title', '完形填空'))
                    self.current_test_id = test_data.get('id')

                    # 启用删除按钮（只有离线模式下的题目可以删除）
                    if self.cloze_module.get_mode() == 'offline':
                        self.delete_button.config(state=tk.NORMAL)
                    else:
                        self.delete_button.config(state=tk.DISABLED)

                    # 显示文章内容
                    content = test_data.get('content', '')
                    self._set_text_content(self.article_text, content, max_height=40, min_height=8)

                    # 显示选项
                    self._display_options(test_data.get('options', []))

                    # 启用提交按钮
                    self.submit_button.config(state=tk.NORMAL)

                    log_info(f"成功开始新的完形填空练习，ID: {test_data.get('id')}")
                    show_toast(self, "题目已准备好，请开始答题！", kind="info")
                else:
                    log_error("未能获取测试数据")
                    messagebox.showerror("错误", "无法生成题目，请检查AI服务是否可用或尝试使用离线模式")
                    # 显示默认提示
                    self._set_text_content(self.article_text, "请点击'开始新练习'按钮生成题目", min_height=8)
            except Exception as e:
                log_error(f"生成题目时出错: {str(e)}")
                messagebox.showerror("错误", f"生成题目失败: {str(e)}")
                # 显示默认提示
                self._set_text_content(self.article_text, "请点击'开始新练习'按钮生成题目", min_height=8)
                # 检查是否是离线模式且没有题目
                if mode == "offline" or (mode is None and not self.cloze_module.ai_service.is_ai_available()):
                    messagebox.showerror("错误", "离线模式下数据库中没有题目，请先联网生成内容！")
                else:
                    messagebox.showerror("错误", "生成题目失败，请稍后重试！")

                # 重置界面
                self._clear_ui()

        except Exception as e:
            log_error(f"开始新测试失败: {str(e)}")
            messagebox.showerror("错误", f"开始新测试失败: {str(e)}")

    def _display_options(self, options):
        """显示选项

        Args:
            options: 选项列表
        """
        # 清空选项区域
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # 显示每个空格的选项
        self.blank_vars = []
        for opt in sorted(options, key=lambda x: x['blank']):
            blank_num = opt['blank']
            opts = opt['options']

            # 创建空格选项框架
            blank_frame = tk.LabelFrame(self.options_frame, text=f"第{blank_num}空",
                                       font=self.font_config['normal'])
            blank_frame.pack(fill=tk.X, pady=5)

            # 该空的单选值
            var = tk.StringVar(value="")
            self.blank_vars.append(var)
            var.trace_add('write', lambda *args, v=var: self._update_selected_answers_label())

            # 显示选项 - 水平排列，每个选项之间有间距
            options_frame = tk.Frame(blank_frame)
            options_frame.pack(anchor=tk.W, padx=10, pady=5, fill=tk.X)

            for i, opt in enumerate(opts, 1):
                letter = chr(64 + i)
                option_text = f"{letter}. {opt}"
                tk.Radiobutton(options_frame, text=option_text, variable=var, value=letter,
                               font=self.font_config['normal']).pack(side=tk.LEFT, padx=15)

        self._update_selected_answers_label()

        # 选项为动态生成的内容，重新绑定鼠标滚轮，保证整页可平滑滚动
        refresh_mousewheel(self.content_scroll_frame)

    def _update_selected_answers_label(self):
        """更新已选答案显示"""
        if not hasattr(self, 'blank_vars') or not self.blank_vars:
            self.selected_answers_label.config(text="已选答案：")
            return
        selected = [v.get() if v.get() else "_" for v in self.blank_vars]
        self.selected_answers_label.config(text=f"已选答案：{','.join(selected)}")

    def _submit_answer(self):
        """提交答案"""
        try:
            if not self.blank_vars:
                show_toast(self, "没有可提交的选项", kind="warning")
                return

            selected = [var.get() for var in self.blank_vars]
            if any(v == "" for v in selected):
                show_toast(self, "请为所有空格选择答案", kind="warning")
                return

            user_answer = ",".join(selected)

            # 提交答案
            is_correct, evaluation, explanation = self.cloze_module.submit_answer(user_answer)

            # 显示结果
            result_parts = ["评估结果:\n", f"{evaluation}\n\n", "解析:\n", explanation]
            self._set_text_content(self.result_text, "".join(result_parts), max_height=30, min_height=4)

            # 禁用提交按钮
            self.submit_button.config(state=tk.DISABLED)

            # 提示用户
            if is_correct:
                show_toast(self, "全部答对了！", kind="success")
            else:
                show_toast(self, "答题完成，请查看解析", kind="info")

        except Exception as e:
            log_error(f"提交答案失败: {str(e)}")
            messagebox.showerror("错误", f"提交答案失败: {str(e)}")

    def _clear_ui(self):
        """清空界面"""
        # 清空标题和题目ID
        self.title_label.config(text="完形填空")
        self.current_test_id = None

        # 禁用删除按钮
        self.delete_button.config(state=tk.DISABLED)

        # 清空文章内容
        self._set_text_content(self.article_text, "", min_height=8)

        # 清空选项区域
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.blank_vars = []

        # 清空已选答案显示
        if hasattr(self, 'selected_answers_label') and self.selected_answers_label:
            self.selected_answers_label.config(text="已选答案：")

        # 清空结果显示
        self._set_text_content(self.result_text, "", min_height=4)

        # 禁用提交按钮
        self.submit_button.config(state=tk.DISABLED)

    # 滚动相关方法已通过create_scrollable_frame实现

    def _on_delete_question(self):
        """处理删除题目的逻辑"""
        if not hasattr(self, 'current_test_id') or self.current_test_id is None:
            show_toast(self, "没有可删除的题目", kind="warning")
            return

        # 弹出确认对话框
        confirm = messagebox.askyesno(
            "确认删除",
            "确定要删除这个完形填空题目吗？此操作不可撤销，但数据会被记录以便恢复。"
        )

        if confirm:
            try:
                # 执行删除
                from modules.database import ComprehensionDatabase
                db = ComprehensionDatabase()
                success = db.delete_cloze_test(self.current_test_id)

                if success:
                    log_info(f"用户删除了完形填空题目，ID: {self.current_test_id}")
                    show_toast(self, "题目已成功删除", kind="success")
                    # 清空界面
                    self._clear_ui()
                else:
                    messagebox.showerror("错误", "删除题目失败，请重试")
                    log_error(f"删除完形填空题目失败，ID: {self.current_test_id}")
            except Exception as e:
                messagebox.showerror("错误", f"删除题目时出错: {str(e)}")
                log_error(f"删除完形填空题目时发生异常: {str(e)}")

    def on_show(self):
        """页面显示时的回调"""
        # 刷新状态信息
        self._update_status()
        # 清空界面
        self._clear_ui()
