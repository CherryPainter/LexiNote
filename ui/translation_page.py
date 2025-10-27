import tkinter as tk
from tkinter import messagebox, ttk
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_wrong_word


class TranslationPage:
    """翻译练习页面"""
    
    def __init__(self, parent, word_manager, font_config):
        """初始化翻译练习页面"""
        self.parent = parent
        self.word_manager = word_manager
        self.font_config = font_config
        
        # 当前练习状态
        self.current_word = None
        self.current_translation = None
        self.is_english_to_chinese = True
        
        # 创建UI
        self._create_ui()
        
        # 开始练习
        self.word_manager.start_exercise("翻译")
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        self.main_frame = tk.Frame(self.parent, bg='white')
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)
        
        # 标题
        title_label = tk.Label(
            self.main_frame, 
            text="翻译练习", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=20)
        
        # 翻译方向选择
        direction_frame = tk.Frame(self.main_frame, bg='white')
        direction_frame.pack(pady=10)
        
        self.direction_var = tk.BooleanVar(value=True)  # True: 英译中, False: 中译英
        
        en_to_zh_radio = tk.Radiobutton(
            direction_frame,
            text="🌐 英译中",
            variable=self.direction_var,
            value=True,
            font=self.font_config['normal'],
            bg='white',
            command=self._on_direction_change
        )
        en_to_zh_radio.pack(side=tk.LEFT, padx=20)
        
        zh_to_en_radio = tk.Radiobutton(
            direction_frame,
            text="🌐 中译英",
            variable=self.direction_var,
            value=False,
            font=self.font_config['normal'],
            bg='white',
            command=self._on_direction_change
        )
        zh_to_en_radio.pack(side=tk.LEFT, padx=20)
        
        # 提示信息
        self.hint_var = tk.StringVar()
        self.hint_var.set("请输入单词的中文翻译")
        self.hint_label = tk.Label(
            self.main_frame, 
            textvariable=self.hint_var,
            font=self.font_config['normal'],
            bg='white',
            fg='#666666'
        )
        self.hint_label.pack(pady=10)
        
        # 单词显示区域
        word_frame = tk.Frame(self.main_frame, bg='#f5f5f5', bd=2, relief=tk.SUNKEN)
        word_frame.pack(pady=30, fill=tk.X, padx=50)
        
        self.word_var = tk.StringVar()
        self.word_label = tk.Label(
            word_frame,
            textvariable=self.word_var,
            font=self.font_config['header'],
            bg='#f5f5f5',
            wraplength=600
        )
        self.word_label.pack(pady=20)
        
        # 输入区域
        input_frame = tk.Frame(self.main_frame, bg='white')
        input_frame.pack(pady=20)
        
        input_label = tk.Label(
            input_frame,
            text="请输入翻译:",
            font=self.font_config['normal'],
            bg='white'
        )
        input_label.pack(anchor='w', pady=5)
        
        # 使用Text控件以支持多行输入
        self.translation_text = tk.Text(
            input_frame,
            font=self.font_config['normal'],
            width=40,
            height=3,
            bd=2,
            relief=tk.SUNKEN,
            wrap=tk.WORD
        )
        self.translation_text.pack(pady=10, ipady=5)
        self.translation_text.bind('<Return>', lambda event: self._check_translation())
        # 添加Ctrl+Return作为提交快捷键
        self.translation_text.bind('<Control-Return>', lambda event: self._check_translation())
        
        # 按钮区域
        buttons_frame = tk.Frame(self.main_frame, bg='white')
        buttons_frame.pack(pady=30)
        
        self.check_button = tk.Button(
            buttons_frame,
            text="✓ 检查",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._check_translation,
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
            command=self._skip_translation,
            bg='#FF9800',
            fg='white'
        )
        self.skip_button.pack(side=tk.LEFT, padx=10)
        
        self.add_word_button = tk.Button(
            buttons_frame,
            text="➕ 添加单词",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._show_add_word_dialog,
            bg='#4CAF50',
            fg='white'
        )
        self.add_word_button.pack(side=tk.LEFT, padx=10)
        
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
        
        # 加载第一个单词
        self._next_translation()
    
    def _on_direction_change(self):
        """翻译方向改变时的处理"""
        self.is_english_to_chinese = self.direction_var.get()
        if self.is_english_to_chinese:
            self.hint_var.set("请输入单词的中文翻译")
        else:
            self.hint_var.set("请输入中文的英文翻译")
        # 加载新单词
        self._next_translation()
    
    def _next_translation(self):
        """获取下一个翻译练习"""
        # 从单词管理器获取单词
        self.current_word = self.word_manager.get_word_by_weight()
        if not self.current_word:
            messagebox.showinfo("提示", "没有可用的单词，请先添加单词。")
            return
        
        # 获取对应的翻译
        self.current_translation = self.word_manager.word_dict.get(self.current_word, "")
        
        # 显示要翻译的内容
        if self.is_english_to_chinese:
            self.word_var.set(self.current_word)
        else:
            self.word_var.set(self.current_translation)
        
        # 清空输入和结果
        self.translation_text.delete(1.0, tk.END)
        self.result_var.set("")
        
        # 设置焦点到输入框
        self.translation_text.focus_set()
    
    def _check_translation(self):
        """使用AI检查翻译答案并显示明确的提示信息"""
        user_input = self.translation_text.get(1.0, tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("提示", "请输入翻译后再检查。")
            return
        
        # 检查翻译（现在完全由AI或备用逻辑判断）
        if self.is_english_to_chinese:
            is_correct = self.word_manager.check_translation(self.current_word, user_input, True)
        else:
            is_correct = self.word_manager.check_translation(self.current_translation, user_input, False)
        
        # 更新单词权重
        self.word_manager.update_word_weight(self.current_word, is_correct)
        
        # 获取AI翻译参考（无论英译中还是中译英都提供）
        ai_reference = ""
        ai_judgment_source = "🤖 AI智能判断" if self.word_manager.ai_available else "📝 系统判断"
        
        # 针对当前翻译方向获取参考
        try:
            if self.word_manager.ai_available:
                if self.is_english_to_chinese:
                    ai_translation = self.word_manager.translate_text(self.current_word, "en2zh")
                    if ai_translation and ai_translation.strip():
                        ai_reference = f"\n\n{ai_translation}"
                else:
                    ai_translation = self.word_manager.translate_text(self.current_translation, "zh2en")
                    if ai_translation and ai_translation.strip():
                        ai_reference = f"\n\n{ai_translation}"
        except Exception as e:
            # 出错时不影响主要功能
            pass
        
        # 显示结果，提供明确的对错提示
        if is_correct:
            # 正确答案的反馈
            result_text = f"✅ 翻译正确！[{ai_judgment_source}]\n\n"
            if self.is_english_to_chinese:
                result_text += f"英文: {self.current_word}\n你的答案: {user_input}\n\n"
                if ai_reference:
                    result_text += f"AI推荐翻译:{ai_reference}"
            else:
                result_text += f"中文: {self.current_translation}\n你的答案: {user_input}\n\n"
                if ai_reference:
                    result_text += f"AI推荐翻译:{ai_reference}"
            
            self.result_var.set(result_text)
            # 使用更醒目的样式表示正确
            self.result_label.config(fg='#2E7D32', font=('SimHei', 13, 'bold'))
            # 短暂闪烁背景色增强视觉反馈
            self._flash_background('#E8F5E9')
            log_info(f"翻译正确: {self.current_word} -> {user_input}")
        else:
            # 错误答案的反馈
            result_text = f"❌ 翻译不正确 [{ai_judgment_source}]\n\n"
            if self.is_english_to_chinese:
                result_text += f"英文: {self.current_word}\n你的答案: {user_input}\n\n"
                if ai_reference:
                    result_text += f"AI推荐翻译:{ai_reference}"
                else:
                    result_text += f"参考翻译: {self.word_manager.word_dict.get(self.current_word, '')}"
            else:
                result_text += f"中文: {self.current_translation}\n你的答案: {user_input}\n\n"
                if ai_reference:
                    result_text += f"AI推荐翻译:{ai_reference}"
                else:
                    result_text += f"参考翻译: {self.current_word}"
            
            self.result_var.set(result_text)
            # 使用更醒目的样式表示错误
            self.result_label.config(fg='#C62828', font=('SimHei', 13, 'bold'))
            # 短暂闪烁背景色增强视觉反馈
            self._flash_background('#FFEBEE')
            log_wrong_word(self.current_word, user_input)
        
        # 更新状态栏
        progress = self.word_manager.get_progress()
        self.status_var.set(f"正确率: {progress.get('correct_rate', 0) * 100:.1f}% | 判断方式: {ai_judgment_source}")
        
        # 延长显示时间，让用户有更充分的时间查看结果和AI建议
        self.main_frame.after(4000, self._next_translation)
    
    def _skip_translation(self):
        """跳过当前翻译"""
        # 标记为错误
        self.word_manager.update_word_weight(self.current_word, False)
        
        # 获取AI翻译参考（为跳过的单词也提供AI参考）
        ai_reference = ""
        try:
            if self.word_manager.ai_available:
                if self.is_english_to_chinese:
                    ai_translation = self.word_manager.translate_text(self.current_word, "en2zh")
                    if ai_translation and ai_translation.strip():
                        ai_reference = f"\n\nAI推荐翻译: {ai_translation}"
                else:
                    ai_translation = self.word_manager.translate_text(self.current_translation, "zh2en")
                    if ai_translation and ai_translation.strip():
                        ai_reference = f"\n\nAI推荐翻译: {ai_translation}"
        except Exception:
            pass
        
        if self.is_english_to_chinese:
            self.result_var.set(f"⏭️ 已跳过: {self.current_word} -> {self.current_translation}{ai_reference}")
        else:
            self.result_var.set(f"⏭️ 已跳过: {self.current_translation} -> {self.current_word}{ai_reference}")
        self.result_label.config(fg='#FF9800')
        log_info(f"跳过翻译: {self.current_word}")
        
        # 显示下一个
        self.main_frame.after(2000, self._next_translation)
    
    def _flash_background(self, color):
        """短暂闪烁背景色以增强视觉反馈"""
        original_bg = self.main_frame.cget('bg')
        
        def flash():
            # 第一次闪烁
            self.main_frame.config(bg=color)
            self.main_frame.after(300, lambda: self.main_frame.config(bg=original_bg))
            # 第二次闪烁
            self.main_frame.after(600, lambda: self.main_frame.config(bg=color))
            # 恢复原始背景
            self.main_frame.after(900, lambda: self.main_frame.config(bg=original_bg))
        
        flash()
    
    def _show_add_word_dialog(self):
        """显示添加单词对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("添加新单词")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.parent.winfo_width() // 2) - (width // 2) + self.parent.winfo_x()
        y = (self.parent.winfo_height() // 2) - (height // 2) + self.parent.winfo_y()
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 创建输入字段
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 英文输入
        tk.Label(frame, text="英文单词:", font=self.font_config['normal']).grid(row=0, column=0, sticky='w', pady=10)
        english_entry = tk.Entry(frame, font=self.font_config['normal'], width=30)
        english_entry.grid(row=0, column=1, pady=10)
        
        # 中文翻译输入
        tk.Label(frame, text="中文翻译:", font=self.font_config['normal']).grid(row=1, column=0, sticky='w', pady=10)
        chinese_entry = tk.Text(frame, font=self.font_config['normal'], width=30, height=3, wrap=tk.WORD)
        chinese_entry.grid(row=1, column=1, pady=10)
        
        # 添加按钮
        def add_word():
            english = english_entry.get().strip()
            chinese = chinese_entry.get(1.0, tk.END).strip()
            
            if not english or not chinese:
                messagebox.showwarning("提示", "请填写完整的单词和翻译。")
                return
            
            if self.word_manager.add_word(english, chinese):
                messagebox.showinfo("成功", f"已添加单词: {english} -> {chinese}")
                dialog.destroy()
            else:
                messagebox.showerror("失败", "添加单词失败。")
        
        buttons_frame = tk.Frame(dialog)
        buttons_frame.pack(pady=20)
        
        tk.Button(
            buttons_frame,
            text="添加",
            font=self.font_config['button'],
            width=15,
            command=add_word,
            bg='#4CAF50',
            fg='white'
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            buttons_frame,
            text="取消",
            font=self.font_config['button'],
            width=15,
            command=dialog.destroy,
            bg='#f44336',
            fg='white'
        ).pack(side=tk.LEFT, padx=10)