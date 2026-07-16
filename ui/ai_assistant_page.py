import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ai_service import AIService
from core.text_formatter import TextFormatter
from logger import log_info, log_error


class AIAssistantPage(tk.Frame):
    """AI英语学习助手页面"""

    def __init__(self, parent, main_window):
        """初始化AI助手页面

        Args:
            parent: 父窗口组件
            main_window: 主窗口实例
        """
        super().__init__(parent, bg='white')
        self.parent = parent
        self.main_window = main_window
        self.font_config = main_window.font_config

        # 初始化文本格式化器，用于处理AI返回的富文本格式
        self.text_formatter = TextFormatter()

        # 延迟初始化AI服务，避免在页面加载时阻塞UI
        self.ai_service = None

        # 任务类型和提示模板
        self.task_types = [
            "单词解释与例句",
            "语法讲解",
            "写作批改",
            "口语练习",
            "阅读理解辅导",
            "听力练习建议",
            "词汇量测试",
            "英语知识点总结"
        ]

        # 创建UI
        self._create_ui()

        # 注册页面显示回调
        self.on_show = self._on_show_page

    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="AI英语学习助手",
            font=self.font_config['title'],
            bg='white'
        )
        title_label.pack(pady=20)

        # 状态显示
        self.status_var = tk.StringVar(value="连接中...")
        status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=self.font_config['normal'],
            bg='white',
            fg='#666'
        )
        status_label.pack(pady=10)

        # 功能区域
        content_frame = tk.Frame(main_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 左侧配置面板
        config_frame = tk.Frame(content_frame, width=250, bg='white')
        config_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 任务类型选择
        task_label = tk.Label(
            config_frame,
            text="选择任务类型:",
            font=self.font_config['normal'],
            bg='white'
        )
        task_label.pack(anchor='w', pady=(10, 5))

        self.task_combobox = ttk.Combobox(
            config_frame,
            values=self.task_types,
            font=self.font_config['normal'],
            state='readonly',
            width=25
        )
        self.task_combobox.current(0)  # 默认选择第一个
        self.task_combobox.pack(anchor='w', pady=5)

        # 难度选择
        difficulty_label = tk.Label(
            config_frame,
            text="难度级别:",
            font=self.font_config['normal'],
            bg='white'
        )
        difficulty_label.pack(anchor='w', pady=(10, 5))

        difficulty_frame = tk.Frame(config_frame, bg='white')
        difficulty_frame.pack(anchor='w')

        self.difficulty_var = tk.StringVar(value="高中")
        difficulty_options = ["初中", "高中", "大学", "专升本", "考研"]
        difficulty_combo = ttk.Combobox(
            difficulty_frame,
            textvariable=self.difficulty_var,
            values=difficulty_options,
            font=self.font_config['normal'],
            width=10
        )
        difficulty_combo.pack(side=tk.LEFT, padx=5)
        difficulty_combo.current(1)

        # 输入提示
        input_label = tk.Label(
            config_frame,
            text="请输入您的问题或内容:",
            font=self.font_config['normal'],
            bg='white'
        )
        input_label.pack(anchor='w', pady=(10, 5))

        # 问题输入框
        self.input_text = scrolledtext.ScrolledText(
            config_frame,
            font=self.font_config['normal'],
            width=30,
            height=8,
            wrap=tk.WORD
        )
        self.input_text.pack(pady=5, fill=tk.BOTH, expand=True)

        # 生成按钮
        self.generate_button = tk.Button(
            config_frame,
            text="获取AI辅导",
            font=self.font_config['button'],
            width=20,
            command=self._on_generate,
            bg='#4CAF50',
            fg='white',
            state=tk.DISABLED
        )
        self.generate_button.pack(pady=15)

        # 右侧结果显示区域
        result_frame = tk.Frame(content_frame, bg='white')
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 结果标题
        result_title = tk.Label(
            result_frame,
            text="AI辅导结果:",
            font=self.font_config['normal'],
            bg='white'
        )
        result_title.pack(anchor='w', pady=(0, 5))

        # 结果显示框
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            font=self.font_config['normal'],
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 清空按钮
        button_frame = tk.Frame(result_frame, bg='white')
        button_frame.pack(side=tk.RIGHT, pady=10)

        self.clear_button = tk.Button(
            button_frame,
            text="清空结果",
            font=self.font_config['button'],
            command=self._clear_result
        )
        self.clear_button.pack(side=tk.RIGHT)

    def _check_ai_connection(self):
        """检查AI连接状态"""
        def check_connection():
            try:
                is_available = self.ai_service.is_ai_available()
                if is_available:
                    self.status_var.set("AI连接正常，您可以开始学习了！")
                    self.generate_button.config(state=tk.NORMAL, bg='#4CAF50')
                    log_info("AI助手连接正常")
                else:
                    # 不可用：区分“主动关闭”与“所选渠道未就绪”
                    mode = getattr(self.ai_service.ai_manager, "ai_mode", "off")
                    if mode == "off":
                        self.status_var.set("AI 功能未启用，请在设置中开启本地或云端模式")
                    else:
                        self.status_var.set("AI连接失败，请确认所选渠道（Ollama/云端）可用")
                    self.generate_button.config(state=tk.DISABLED, bg='#cccccc')
                    log_warning(f"AI助手连接失败（模式: {mode}）")
            except Exception as e:
                self.status_var.set(f"检查连接时出错: {str(e)}")
                log_error(f"检查AI连接时出错: {str(e)}")

        # 在单独的线程中检查，避免阻塞UI
        threading.Thread(target=check_connection, daemon=True).start()

    def _on_generate(self):
        """处理生成请求"""
        task_type = self.task_combobox.get()
        difficulty = self.difficulty_var.get()
        user_input = self.input_text.get("1.0", tk.END).strip()

        if not user_input:
            messagebox.showwarning("提示", "请输入您的问题或内容")
            return

        # 禁用按钮，防止重复点击
        self.generate_button.config(state=tk.DISABLED, text="AI思考中...")

        # 清空结果
        self._clear_result()

        # 构建提示词
        prompt = self._build_prompt(task_type, difficulty, user_input)

        # 在单独的线程中处理AI请求
        def process_ai_request():
            try:
                # 显示正在生成的提示
                self._append_to_result(f"AI正在为您分析{task_type}...\n\n")

                # 使用AI服务获取响应
                self.ai_service.ai_manager._ask_sync(prompt, callback=self._stream_response)

                # 确保响应完成
                self._append_to_result("")
                log_info(f"AI助手生成{task_type}完成")
            except Exception as e:
                error_msg = f"生成时出错: {str(e)}"
                self._append_to_result(f"\n\n{error_msg}")
                log_error(error_msg)
            finally:
                # 恢复按钮状态
                self.after(0, lambda: self.generate_button.config(
                    state=tk.NORMAL,
                    text="获取AI辅导"
                ))

        threading.Thread(target=process_ai_request, daemon=True).start()

    def _build_prompt(self, task_type, difficulty, user_input):
        """构建AI提示词

        Args:
            task_type: 任务类型
            difficulty: 难度级别
            user_input: 用户输入

        Returns:
            构建好的提示词
        """
        templates = {
            "单词解释与例句": f"""
请作为一名英语老师，为{difficulty}水平的学生解释以下单词或短语：
{user_input}

要求：
1. 提供准确的中文解释
2. 给出2-3个实用例句（包含中文翻译）
3. 说明使用场景和搭配
4. 如果是容易混淆的单词，请提供辨析
            """,

            "语法讲解": f"""
请作为一名英语老师，为{difficulty}水平的学生讲解以下语法点：
{user_input}

要求：
1. 简明扼要地解释语法规则
2. 提供多个例句展示正确用法
3. 指出常见错误和注意事项
4. 给出练习建议
            """,

            "写作批改": f"""
请作为一名英语老师，批改以下{difficulty}水平学生的英语作文：
{user_input}

要求：
1. 指出语法和拼写错误并纠正
2. 评估整体流畅度和表达清晰度
3. 提供改进建议
4. 给出合理的评分和鼓励
            """,

            "口语练习": f"""
请作为一名英语口语教练，为{difficulty}水平的学生提供以下主题的口语练习指导：
{user_input}

要求：
1. 提供2-3个实用的对话示例
2. 指出关键表达和常用短语
3. 给出语音语调的注意事项
4. 建议练习方法
            """,

            "阅读理解辅导": f"""
请作为一名英语老师，帮助{difficulty}水平的学生理解以下英语文章或段落：
{user_input}

要求：
1. 总结文章大意
2. 解释重点单词和复杂句子
3. 分析文章结构和写作手法
4. 提供相关的文化背景知识
            """,

            "听力练习建议": f"""
请作为一名英语听力老师，为{difficulty}水平的学生提供关于以下内容的听力练习建议：
{user_input}

要求：
1. 推荐适合的听力材料来源
2. 提供具体的听力技巧和方法
3. 设计简单的听力练习
4. 给出提高听力水平的长期计划
            """,

            "词汇量测试": f"""
请作为一名英语老师，为{difficulty}水平的学生设计关于以下主题的词汇量测试：
{user_input}

要求：
1. 提供10个相关的重点词汇
2. 为每个词汇设计一个简单的测试题
3. 给出答案和简短解释
4. 建议如何记忆这些词汇
            """,

            "英语知识点总结": f"""
请作为一名英语老师，为{difficulty}水平的学生总结以下英语知识点：
{user_input}

要求：
1. 系统整理相关知识点
2. 提供清晰的分类和结构
3. 使用表格或列表增强可读性
4. 添加记忆技巧和学习建议
            """
        }

        # 如果有对应模板，使用模板；否则使用通用模板
        if task_type in templates:
            return templates[task_type]
        else:
            return f"""
请作为一名英语学习助手，为{difficulty}水平的学生解答以下问题：
{user_input}

请提供详细、准确的回答，并考虑学生的学习需求。
            """

    def _stream_response(self, chunk, done):
        """流式处理AI响应的回调函数"""
        if chunk:
            # 格式化chunk
            formatted_chunk = self.text_formatter.format_for_tkinter(chunk)
            self.after(0, lambda: self._append_to_result(formatted_chunk))

    def _append_to_result(self, text):
        """向结果框添加文本"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)

    def _clear_result(self):
        """清空结果框"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)

    def _on_show_page(self):
        """页面显示时执行的操作，延迟初始化AI服务"""
        log_info("显示AI助手页面")

        # 延迟初始化AI服务，传入主窗口的WordManager实例
        if self.ai_service is None:
            # 使用主窗口的WordManager实例，避免重复初始化
            if hasattr(self.main_window, 'word_manager'):
                self.ai_service = AIService(word_manager=self.main_window.word_manager)
            else:
                self.ai_service = AIService()

        # 重新检查AI连接状态
        self._check_ai_connection()


# 导入缺失的logger函数
from logger import log_warning
