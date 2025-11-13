import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.dictation_page import DictationPage
from ui.translation_page import TranslationPage
from ui.review_page import ReviewPage
from ui.learning_page import LearningPage
from ui.settings_page import SettingsPage
from ui.cloze_test_page import ClozeTestPage
from ui.reading_comprehension_page import ReadingComprehensionPage
from ui.ai_assistant_page import AIAssistantPage
from ui.word_set_page import WordSetPage
from ui.statistics_page import StatisticsPage
from word_manager import WordManager
from core.learning import LearningManager
from core.settings_manager import SettingsManager
from statistics import StatisticsManager
from audio_player import AudioPlayer
from logger import log_info


class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("LexiNote - 个人英语学习工具")
        self.root.geometry("1080x720")
        self.root.minsize(600, 400)
        
        # 设置中文字体
        self._set_fonts()
        
        # 初始化核心管理器
        self.settings_manager = SettingsManager()
        self.audio_player = AudioPlayer()
        
        # 直接创建单词管理器，它会自动初始化统计管理器
        self.word_manager = WordManager()
        
        # 页面实例缓存，使用懒加载模式
        self._pages = {}
        
        # 创建UI
        self._create_ui()
        
        log_info("主窗口启动")
    
    def _set_fonts(self):
        """设置中文字体"""
        # 在不同操作系统上尝试使用合适的中文字体
        self.font_families = ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'Arial Unicode MS']
        self.font_config = {
            'header': ('SimHei', 16, 'bold'),
            'normal': ('SimHei', 12),
            'button': ('SimHei', 12),
            'title': ('SimHei', 24, 'bold')
        }
    
    def _create_ui(self):
        """创建用户界面"""
        # 创建主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建侧边导航
        self._create_sidebar()
        
        # 创建内容区域
        self._create_content_area()
        
        # 显示欢迎页面
        self._show_welcome_page()
    
    def _create_sidebar(self):
        """创建侧边导航栏"""
        self.sidebar = tk.Frame(self.main_frame, width=200, bg='#f0f0f0', bd=2, relief=tk.SUNKEN)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 标题
        title_label = tk.Label(self.sidebar, text="LexiNote", font=self.font_config['title'], bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # 导航按钮
        nav_buttons = [
            ("📚 单词学习", self._show_learning_page),
            ("📝 听写练习", self._show_dictation_page),
            ("🌐 翻译练习", self._show_translation_page),
            ("📊 单词复习", self._show_review_page),
            ("🔤 完形填空", self._show_cloze_test_page),
            ("📖 阅读理解", self._show_reading_comprehension_page),
            ("📁 词库管理", self._show_word_set_page),
            ("🤖 AI助手", self._show_ai_assistant_page),
            ("📈 学习统计", self._show_statistics),
            ("⚙️ 设置", self._show_settings_page)
        ]
        
        for text, command in nav_buttons:
            button = tk.Button(
                self.sidebar, 
                text=text, 
                font=self.font_config['button'],
                width=20, 
                height=2,
                command=command,
                bg='#e0e0e0',
                relief=tk.RAISED,
                bd=1
            )
            button.pack(pady=5, padx=10)
            
            # 添加悬停效果
            button.bind('<Enter>', lambda e, b=button: b.config(bg='#d0d0d0'))
            button.bind('<Leave>', lambda e, b=button: b.config(bg='#e0e0e0'))
    
    def _create_content_area(self):
        """创建内容区域"""
        self.content_area = tk.Frame(self.main_frame, bg='white')
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def _clear_content_area(self):
        """清空内容区域，使用forget而不是destroy以保留页面实例"""
        for widget in self.content_area.winfo_children():
            # 使用pack_forget()而不是destroy()，保留组件以便复用
            try:
                widget.pack_forget()
            except:
                # 如果组件不是使用pack()布局的，尝试使用place_forget
                try:
                    widget.place_forget()
                except:
                    # 如果都不行，则销毁组件
                    widget.destroy()
    
    def _show_settings_page(self):
        """显示设置页面"""
        page_key = "settings"
        
        # 懒加载页面
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = SettingsPage(
                self.content_area,
                settings_manager=self.settings_manager,
                word_manager=self.word_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到设置页面")
    
    def _show_welcome_page(self):
        """显示欢迎页面"""
        self._clear_content_area()
        
        welcome_frame = tk.Frame(self.content_area, bg='white')
        welcome_frame.pack(expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(
            welcome_frame, 
            text="欢迎使用 LexiNote", 
            font=self.font_config['title'],
            bg='white'
        )
        title_label.pack(pady=50)
        
        subtitle_label = tk.Label(
            welcome_frame, 
            text="您的个人英语学习助手", 
            font=self.font_config['header'],
            bg='white'
        )
        subtitle_label.pack(pady=20)
        
        # 显示进度信息
        progress = self.word_manager.get_progress()
        progress_frame = tk.Frame(welcome_frame, bg='white')
        progress_frame.pack(pady=30)
        
        stats = [
            f"总学习单词数: {progress.get('total_learned', 0)}",
            f"正确率: {progress.get('correct_rate', 0) * 100:.1f}%",
            f"最后学习: {progress.get('last_session', '未开始')}"
        ]
        
        for stat in stats:
            stat_label = tk.Label(
                progress_frame, 
                text=stat, 
                font=self.font_config['normal'],
                bg='white'
            )
            stat_label.pack(pady=10)
        
        hint_label = tk.Label(
            welcome_frame, 
            text="请从左侧选择学习模式开始练习", 
            font=self.font_config['normal'],
            fg='#666666',
            bg='white'
        )
        hint_label.pack(pady=20)
    
    def _show_dictation_page(self):
        """显示听写练习页面"""
        page_key = "dictation"
        today_words = self.word_manager.get_today_learned_words()
        
        # 懒加载页面
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = DictationPage(
                self.content_area,
                word_manager=self.word_manager,
                settings_manager=self.settings_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info(f"切换到听写练习页面，今日已学习 {len(today_words)} 个单词")
    
    def _show_translation_page(self):
        """显示翻译练习页面"""
        page_key = "translation"
        
        # 懒加载页面
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = TranslationPage(
                self.content_area,
                word_manager=self.word_manager,
                settings_manager=self.settings_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到翻译练习页面")
    
    def _show_review_page(self):
        """显示单词复习页面"""
        page_key = "review"
        
        # 懒加载页面
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = ReviewPage(
                self.content_area,
                word_manager=self.word_manager,
                settings_manager=self.settings_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到单词复习页面")
    
    def _show_learning_page(self):
        """显示学习模式页面"""
        page_key = "learning"
        
        # 懒加载页面
        if page_key not in self._pages:
            # 创建学习管理器
            self.learning_manager = LearningManager(
                word_manager=self.word_manager,
                audio_player=self.audio_player
            )
            
            # 先创建页面但不pack
            self._pages[page_key] = LearningPage(
                self.content_area,
                word_manager=self.word_manager,
                learning_manager=self.learning_manager,
                settings_manager=self.settings_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到学习模式页面")
    
    def _show_cloze_test_page(self):
        """显示完形填空页面"""
        page_key = "cloze_test"
        
        # 懒加载页面，避免在初始化时连接AI
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = ClozeTestPage(
                self.content_area,
                self
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        # 调用页面的on_show方法
        if hasattr(self.current_page, 'on_show'):
            self.current_page.on_show()
            
        log_info("切换到完形填空页面")
    
    def _show_reading_comprehension_page(self):
        """显示阅读理解页面"""
        page_key = "reading_comprehension"
        
        # 懒加载页面，避免在初始化时连接AI
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = ReadingComprehensionPage(
                self.content_area,
                self
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        # 调用页面的on_show方法
        if hasattr(self.current_page, 'on_show'):
            self.current_page.on_show()
            
        log_info("切换到阅读理解页面")
        
    def _show_statistics(self):
        """显示学习统计页面"""
        page_key = "statistics"
        
        # 懒加载页面
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = StatisticsPage(
                self.content_area,
                word_manager=self.word_manager,
                settings_manager=self.settings_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        # 调用页面的on_enter方法
        if hasattr(self.current_page, 'on_enter'):
            self.current_page.on_enter()
            
        log_info("切换到学习统计页面")
    
    # _show_settings方法已被_settings_page替代，保留_apply_decay方法用于设置页面
    
    def _show_ai_assistant_page(self):
        """显示AI助手页面"""
        page_key = "ai_assistant"
        
        # 懒加载页面，避免在初始化时连接AI
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = AIAssistantPage(
                self.content_area,
                self
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        # 调用页面的on_show方法
        if hasattr(self.current_page, 'on_show'):
            self.current_page.on_show()
            
        log_info("切换到AI助手页面")
        
    def _show_word_set_page(self):
        """显示词库管理页面"""
        page_key = "word_set"
        
        # 懒加载页面
        if page_key not in self._pages:
            # 先创建页面但不pack
            self._pages[page_key] = WordSetPage(
                self.content_area,
                word_manager=self.word_manager,
                font_config=self.font_config
            )
        
        # 先获取页面实例
        page = self._pages[page_key]
        
        # 清空内容区域
        self._clear_content_area()
        
        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到词库管理页面")
    
    def _apply_decay(self):
        """应用每日权重衰减"""
        result = self.word_manager.apply_daily_decay()
        
        # 显示结果提示
        result_window = tk.Toplevel(self.root)
        result_window.title("操作结果")
        result_window.geometry("300x150")
        result_window.resizable(False, False)
        
        # 计算居中位置
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        result_window.geometry(f"300x150+{x}+{y}")
        
        message = "权重衰减应用成功！"
        if not result:
            message = "权重衰减应用失败！"
        
        message_label = tk.Label(
            result_window,
            text=message,
            font=self.font_config['normal']
        )
        message_label.pack(pady=40)
        
        ok_button = tk.Button(
            result_window,
            text="确定",
            font=self.font_config['button'],
            width=10,
            command=result_window.destroy
        )
        ok_button.pack()


def main():
    """主函数"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()