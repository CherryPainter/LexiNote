import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.components.scrollable_frame import create_scrollable_frame

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
        if self.cloze_module is None:
            from modules.cloze_test import ClozeTestModule
            self.cloze_module = ClozeTestModule(word_manager=self.controller.word_manager)
            
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
        self.level_var = tk.StringVar(value="中级")
        level_options = ["初级", "中级", "高级"]
        level_combo = ttk.Combobox(level_frame, textvariable=self.level_var, values=level_options, 
                                  font=self.font_config['normal'], width=8)
        level_combo.grid(row=0, column=1, padx=5)
        level_combo.current(1)
        
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
        
        # 内容区域
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
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
        
        # 文章内容
        self.article_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                                     height=15, bg="#f5f5f5", state=tk.DISABLED)
        self.article_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 为文章内容添加鼠标滚轮支持
        from ui.components.scrollable_frame import add_mousewheel_support
        add_mousewheel_support(self.article_text, self.article_text)
        
        # 选项区域 - 使用通用滚动框架
        options_scroll_frame, self.options_frame, _, _ = create_scrollable_frame(content_frame)
        options_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 答案输入和提交
        answer_frame = tk.Frame(content_frame)
        answer_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(answer_frame, text="请输入答案（用逗号分隔，如：1,2,3,4）:", 
                font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.answer_entry = tk.Entry(answer_frame, font=self.font_config['normal'], width=50)
        self.answer_entry.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.submit_button = tk.Button(answer_frame, text="提交答案", command=self._submit_answer,
                                     font=self.font_config['button'], bg="#2196F3", fg="white", 
                                     width=12, height=1, state=tk.DISABLED)
        self.submit_button.grid(row=1, column=1, padx=10, pady=5)
        
        # 结果显示区域
        result_frame = tk.LabelFrame(content_frame, text="结果", font=self.font_config['normal'])
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=self.font_config['normal'],
                                                    height=8, bg="#f0f0f0", state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
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
                    self.article_text.config(state=tk.NORMAL)
                    self.article_text.delete(1.0, tk.END)
                    self.article_text.insert(tk.END, content)
                    self.article_text.config(state=tk.DISABLED)
                    
                    # 显示选项
                    self._display_options(test_data.get('options', []))
                    
                    # 启用提交按钮
                    self.submit_button.config(state=tk.NORMAL)
                    
                    log_info(f"成功开始新的完形填空练习，ID: {test_data.get('id')}")
                    messagebox.showinfo("提示", "题目已准备好，请开始答题！")
                else:
                    log_error("未能获取测试数据")
                    messagebox.showerror("错误", "无法生成题目，请检查AI服务是否可用或尝试使用离线模式")
                    # 显示默认提示
                    self.article_text.config(state=tk.NORMAL)
                    self.article_text.delete(1.0, tk.END)
                    self.article_text.insert(tk.END, "请点击'开始新练习'按钮生成题目")
                    self.article_text.config(state=tk.DISABLED)
            except Exception as e:
                log_error(f"生成题目时出错: {str(e)}")
                messagebox.showerror("错误", f"生成题目失败: {str(e)}")
                # 显示默认提示
                self.article_text.config(state=tk.NORMAL)
                self.article_text.delete(1.0, tk.END)
                self.article_text.insert(tk.END, "请点击'开始新练习'按钮生成题目")
                self.article_text.config(state=tk.DISABLED)
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
        for opt in sorted(options, key=lambda x: x['blank']):
            blank_num = opt['blank']
            opts = opt['options']
            
            # 创建空格选项框架
            blank_frame = tk.LabelFrame(self.options_frame, text=f"第{blank_num}空", 
                                       font=self.font_config['normal'])
            blank_frame.pack(fill=tk.X, pady=5)
            
            # 显示选项 - 水平排列，每个选项之间有间距
            options_frame = tk.Frame(blank_frame)
            options_frame.pack(anchor=tk.W, padx=10, pady=5, fill=tk.X)
            
            for i, opt in enumerate(opts, 1):
                option_text = f"{chr(64+i)}. {opt}"
                tk.Label(options_frame, text=option_text, font=self.font_config['normal'], 
                        justify=tk.LEFT).pack(side=tk.LEFT, padx=15)
        
        # 滚动区域会自动更新，无需手动调用
    
    def _submit_answer(self):
        """提交答案"""
        try:
            user_answer = self.answer_entry.get().strip()
            
            if not user_answer:
                messagebox.showwarning("提示", "请输入答案！")
                return
            
            # 提交答案
            is_correct, evaluation, explanation = self.cloze_module.submit_answer(user_answer)
            
            # 显示结果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            # 显示评估结果
            self.result_text.insert(tk.END, "评估结果:\n")
            self.result_text.insert(tk.END, f"{evaluation}\n\n")
            
            # 显示解析
            self.result_text.insert(tk.END, "解析:\n")
            self.result_text.insert(tk.END, explanation)
            
            self.result_text.config(state=tk.DISABLED)
            
            # 禁用提交按钮
            self.submit_button.config(state=tk.DISABLED)
            
            # 提示用户
            if is_correct:
                messagebox.showinfo("恭喜", "全部答对了！")
            else:
                messagebox.showinfo("提示", "答题完成，请查看解析")
                
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
        self.article_text.config(state=tk.NORMAL)
        self.article_text.delete(1.0, tk.END)
        self.article_text.config(state=tk.DISABLED)
        
        # 清空选项区域
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # 清空答案输入
        self.answer_entry.delete(0, tk.END)
        
        # 清空结果显示
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        # 禁用提交按钮
        self.submit_button.config(state=tk.DISABLED)
    
    # 滚动相关方法已通过create_scrollable_frame实现
    
    def _on_delete_question(self):
        """处理删除题目的逻辑"""
        if not hasattr(self, 'current_test_id') or self.current_test_id is None:
            messagebox.showwarning("提示", "没有可删除的题目")
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
                    messagebox.showinfo("成功", "题目已成功删除")
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