import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_info, log_wrong_word
from audio_player import AudioPlayer
from ui.components.scrollable_frame import create_scrollable_frame


class TranslationPage(tk.Frame):
    """翻译练习页面"""
    
    def __init__(self, parent, settings_manager=None, word_manager=None, font_config=None, **kwargs):
        """初始化翻译练习页面"""
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.settings_manager = settings_manager
        self.word_manager = word_manager
        self.font_config = font_config or {'title': ('Arial', 24), 'normal': ('Arial', 16), 'small': ('Arial', 12)}
        self.current_word = ""
        self.current_translation = ""
        
        # 注册设置监听器
        if self.settings_manager:
            self.settings_manager.register_listener(
                'auto_mode_translation_practice', 
                self._on_auto_mode_translation_practice_change
            )
        self.is_english_to_chinese = True
        self.current_example = ""
        self.is_example_visible = False
        
        # 初始化音频播放器
        self.audio_player = AudioPlayer()
        self.audio_available = self.audio_player.is_available()
        
        # 创建UI
        self._create_ui()
        # 注册设置监听器以便运行时生效
        try:
            self.settings_manager.register_listener('auto_mode_translation_practice', self._on_auto_mode_translation_change)
        except Exception:
            pass

        # 开始练习
        self.word_manager.start_exercise("翻译")
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架 - 使用通用滚动框架
        content_scroll_frame, self.main_frame, _, _ = create_scrollable_frame(self, padx=50, pady=30)
        content_scroll_frame.pack(expand=True, fill=tk.BOTH)
        
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
        
        # 例句框架
        self.example_frame = tk.Frame(self.main_frame, bg="#f9f9f9", bd=1, relief=tk.SUNKEN)
        self.example_frame.pack(fill=tk.X, pady=15, padx=50, side=tk.BOTTOM)
        
        # 例句显示标签
        self.example_label = tk.Label(
            self.example_frame,
            text="",
            font=self.font_config['normal'],
            bg="#f9f9f9",
            fg="#333333",
            wraplength=600,
            justify=tk.LEFT,
            padx=15,
            pady=10
        )
        self.example_label.pack(fill=tk.X)
        
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
        
        self.pronounce_button = tk.Button(
            buttons_frame,
            text="🔊 发音",
            font=self.font_config['button'],
            width=12,
            height=2,
            command=self._play_pronunciation,
            bg="#4CAF50",
            fg="white"
        )
        self.pronounce_button.pack(side=tk.LEFT, padx=10)
        
        self.example_button = tk.Button(
            buttons_frame,
            text="📝 显示例句",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._toggle_example,
            bg="#2196F3",
            fg="white"
        )
        self.example_button.pack(side=tk.LEFT, padx=10)
        
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
        
        # 下一个按钮（手动模式时使用）
        self.next_button = tk.Button(
            buttons_frame,
            text="🔄 下一个",
            font=self.font_config['button'],
            width=15,
            height=2,
            command=self._next_translation,
            bg='#9C27B0',
            fg='white'
        )
        
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
    
    def _play_pronunciation(self):
        """播放单词发音"""
        if not self.current_word:
            return
        
        word_to_pronounce = self.current_word
        
        # 如果是中译英模式，需要考虑是否需要发音中文
        # 这里只对英文单词进行发音
        if not self.is_english_to_chinese:
            # 在中译英模式下，current_word可能是中文
            # 如果需要中文发音功能，可以在这里添加
            pass
        
        # 在后台线程播放，避免阻塞UI
        def _play():
            try:
                result = self.audio_player.play_pronunciation(word_to_pronounce)
            except Exception as e:
                from logger import log_error
                log_error(f"播放线程异常: {str(e)}")
                result = False

            def _on_done():
                # 恢复按钮并显示可能的错误
                try:
                    self.pronounce_button.config(state=tk.NORMAL, text="🔊 发音")
                except Exception:
                    pass

                if not result and self.audio_available:
                    messagebox.showerror("播放失败", "无法播放单词发音，请检查网络连接。")
                else:
                    try:
                        self.status_var.set(f"已播放: {word_to_pronounce}")
                    except Exception:
                        pass

            try:
                self.main_frame.after(0, _on_done)
            except Exception:
                _on_done()

        # 禁用按钮并提供视觉反馈
        try:
            self.pronounce_button.config(state=tk.DISABLED, text="🔊 播放中...")
            self.status_var.set("正在播放...")
        except Exception:
            pass

        threading.Thread(target=_play, daemon=True).start()
    
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
        self.current_translation = self.word_manager.get_translation(self.current_word) or ""
        
        # 获取完整单词信息以显示音标
        self.current_word_info = {}
        if self.is_english_to_chinese:
            # 英翻中时，获取单词的完整信息
            try:
                words = self.word_manager.get_words_from_active_set(keyword=self.current_word)
                if words and len(words) > 0:
                    self.current_word_info = words[0]
            except Exception:
                pass
            
            # 显示要翻译的内容，包含音标
            display_text = self.current_word
            if self.current_word_info.get('phonetic'):
                display_text = f"{self.current_word}\n{self.current_word_info['phonetic']}"
            self.word_var.set(display_text)
        else:
            self.word_var.set(self.current_translation)
        
        # 清空输入和结果
        self.translation_text.delete(1.0, tk.END)
        self.result_var.set("")
        
        # 重置例句状态
        self.is_example_visible = False
        self.current_example = ""
        self.example_label.config(text="")
        self.example_button.config(text="📝 显示例句")
        
        # 如果例句功能启用，异步获取例句
        if self.settings_manager and self.settings_manager.get_setting("example_enabled", True):
            threading.Thread(target=self._fetch_example_async, daemon=True).start()
        
        # 设置焦点到输入框
        self.translation_text.focus_set()
    
    def _check_translation(self):
        """使用AI检查翻译答案并显示明确的提示信息"""
        user_input = self.translation_text.get(1.0, tk.END).strip()
        
        if not user_input:
            messagebox.showwarning("提示", "请输入翻译后再检查。")
            return
        
        # 获取翻译判定模式设置
        translation_mode = self.settings_manager.get_setting('translation_mode', 'ai_first') if self.settings_manager else 'ai_first'
        
        # 根据翻译判定模式设置显示文本
        if translation_mode == 'local_only':
            ai_judgment_source = "📝 仅本地判断"
        elif translation_mode == 'local_first':
            ai_judgment_source = "📝 本地优先"
        else:  # ai_first
            ai_judgment_source = "🤖 AI智能判断" if self.word_manager.ai_available else "📝 系统判断"
        
        # 检查翻译（现在完全由AI或备用逻辑判断）
        if self.is_english_to_chinese:
            is_correct = self.word_manager.check_translation(self.current_word, user_input, True, translation_mode=translation_mode)
        else:
            is_correct = self.word_manager.check_translation(self.current_translation, user_input, False, translation_mode=translation_mode)
        
        # 更新单词权重
        # 因为这里没有时间统计，使用0作为默认值
        self.word_manager.update_word_weight(self.current_word, is_correct, 0)
        
        # 获取AI翻译参考（无论英译中还是中译英都提供）
        ai_reference = ""
        
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
                    result_text += f"参考翻译: {self.word_manager.get_translation(self.current_word) or ''}"
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
            # 记录错误：日志 + word_manager 跟踪
            try:
                if hasattr(self.word_manager, 'add_wrong_word'):
                    self.word_manager.add_wrong_word(self.current_word)
            except Exception:
                pass
            log_wrong_word(self.current_word, user_input)
        
        # 更新状态栏
        progress = self.word_manager.get_progress()
        self.status_var.set(f"正确率: {progress.get('correct_rate', 0) * 100:.1f}% | 判断方式: {ai_judgment_source}")
        
        # 检查是否需要自动下一个单词
        # 受模块级别的手动/自动设置控制
        module_mode = 'manual'
        try:
            module_mode = self.settings_manager.get_setting('auto_mode_translation_practice', 'manual') if self.settings_manager else 'manual'
        except Exception:
            module_mode = 'manual'

        auto_next = False
        if module_mode == 'auto':
            # 维持现有的按答对/答错自动跳转逻辑
            if is_correct:
                auto_next = self.settings_manager.get_setting("auto_next_correct", False) if self.settings_manager else False
            else:
                auto_next = self.settings_manager.get_setting("auto_next_wrong", False) if self.settings_manager else False
        else:
            # 模块设为手动时，禁止自动跳转
            auto_next = False

        if auto_next:
            # 延迟一小段时间再自动下一个单词，让用户有时间看到反馈
            self.after(1000, self._next_translation)
            # 隐藏手动下一个按钮（如果存在）
            try:
                self.next_button.pack_forget()
            except Exception:
                pass
        else:
            # 手动模式或不自动时，显示下一个按钮供用户手动继续
            try:
                self.next_button.pack(side=tk.LEFT, padx=10)
            except Exception:
                pass
    
    def _on_auto_mode_translation_practice_change(self, key, value):
        """设置变更回调：自动/手动切换变动时更新 UI 行为"""
        try:
            if value == 'auto':
                # 自动模式下，仅当答对/答错设置为自动时才隐藏下一个按钮
                if self.settings_manager:
                    if self.result_var.get().startswith("✓"):
                        auto_next = self.settings_manager.get_setting("auto_next_correct", False)
                    elif self.result_var.get().startswith("✗"):
                        auto_next = self.settings_manager.get_setting("auto_next_wrong", False)
                    else:
                        auto_next = False
                    
                    if auto_next:
                        try:
                            self.next_button.pack_forget()
                        except Exception:
                            pass
            else:
                # 手动模式时，始终显示下一个按钮（如果有结果）
                if self.result_var.get().strip() and not self.result_var.get() == "请输入翻译":
                    try:
                        self.next_button.pack(side=tk.LEFT, padx=10)
                    except Exception:
                        pass
        except Exception as e:
            pass
            
    def _skip_translation(self):
        """跳过当前翻译"""
        # 标记为错误
        # 因为这里没有时间统计，使用0作为默认值
        self.word_manager.update_word_weight(self.current_word, False, 0)
        
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
        
        # 检查是否需要自动下一个单词
        auto_next = self.settings_manager.get_setting("auto_next_wrong", False) if self.settings_manager else False
        
        if auto_next:
            # 延迟一小段时间再自动下一个单词
            self.after(1000, self._next_translation)
        else:
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
    
    def _fetch_example_async(self):
        """异步获取单词例句"""
        if self.current_word and hasattr(self.word_manager, 'get_word_example'):
            # 确保传递的是单词字符串而不是字典
            word_str = self.current_word['word'] if isinstance(self.current_word, dict) else self.current_word
            # 使用WordManager的异步API获取例句
            self.word_manager.get_word_example(
                word_str, 
                async_mode=True, 
                callback=self._on_example_fetched
            )
            
    def _on_example_fetched(self, example):
        """
        例句获取完成后的回调处理
        
        Args:
            example: 获取到的例句文本
        """
        try:
            self.current_example = example
            # 如果用户已经点击显示例句，自动更新UI
            if self.is_example_visible:
                self.master.after(0, lambda: self.example_label.config(text=example))
        except Exception as e:
            pass  # 忽略UI更新错误
    
    def _toggle_example(self):
        """切换例句显示状态"""
        if not self.current_word:
            return
            
        if not self.is_example_visible:
            # 显示例句
            if self.current_example:
                self.example_label.config(text=self.current_example)
                self.is_example_visible = True
                self.example_button.config(text="📝 隐藏例句")
            elif self.settings_manager and self.settings_manager.get_setting("example_enabled", True) and hasattr(self.word_manager, 'get_word_example'):
                # 如果还没有例句，异步获取
                self.example_label.config(text="正在获取例句...")
                self.is_example_visible = True
                
                # 使用异步方式获取例句
                def on_example_ready(example):
                    try:
                        self.current_example = example
                        self.master.after(0, lambda: self.example_label.config(
                            text=example if example else "无法获取例句"
                        ))
                        self.master.after(0, lambda: self.example_button.config(
                            text="📝 隐藏例句"
                        ))
                    except Exception as e:
                        pass  # 忽略UI更新错误
                
                # 确保传递的是单词字符串而不是字典
                word_str = self.current_word['word'] if isinstance(self.current_word, dict) else self.current_word
                self.word_manager.get_word_example(
                    word_str, 
                    async_mode=True, 
                    callback=on_example_ready
                )
        else:
            # 隐藏例句
            self.example_label.config(text="")
            self.is_example_visible = False
            self.example_button.config(text="📝 显示例句")

    def _on_auto_mode_translation_change(self, key, value):
        """设置变更回调：当翻译练习模块的自动/手动模式变更时，更新UI按钮可见性"""
        try:
            if value == 'auto':
                # 自动模式时隐藏手动下一个按钮
                try:
                    self.next_button.pack_forget()
                except Exception:
                    pass
            else:
                # 手动模式时显示下一个按钮
                try:
                    self.next_button.pack(side=tk.LEFT, padx=10)
                except Exception:
                    pass
        except Exception:
            pass
    
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
    
    def on_show(self):
        """页面显示时的回调"""
        # 刷新设置
        self._update_hint_text()
        self._update_auto_mode_setting()
        
        # 重新开始练习
        self.word_manager.start_exercise("翻译")
        self.next_word()
    
    # 滚动相关方法已通过create_scrollable_frame实现