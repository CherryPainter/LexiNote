import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.dictation_page import DictationPage
from ui.translation_page import TranslationPage
from ui.review_page import ReviewPage
from ui.learning_page import LearningPage
from ui.settings_page import SettingsPage
from word_manager import WordManager
from core.learning import LearningManager
from core.settings_manager import SettingsManager
from audio_player import AudioPlayer
from logger import log_info


class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("LexiNote - 个人英语学习工具")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 设置中文字体
        self._set_fonts()
        
        # 初始化核心管理器
        self.word_manager = WordManager()
        self.settings_manager = SettingsManager()
        self.audio_player = AudioPlayer()
        
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
        """清空内容区域"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def _show_settings_page(self):
        """显示设置页面"""
        self._clear_content_area()
        
        # 创建设置页面
        self.current_page = SettingsPage(
            self.content_area,
            settings_manager=self.settings_manager,
            word_manager=self.word_manager,
            font_config=self.font_config
        )
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
        # 允许用户进入听写页面，即使今日没有学习单词
        # 具体的功能访问限制将在dictation_page中处理
        today_words = self.word_manager.get_today_learned_words()
        self._clear_content_area()
        self.current_page = DictationPage(
            self.content_area,
            word_manager=self.word_manager,
            settings_manager=self.settings_manager,
            font_config=self.font_config
        )
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info(f"切换到听写练习页面，今日已学习 {len(today_words)} 个单词")
    
    def _show_translation_page(self):
        """显示翻译练习页面"""
        self._clear_content_area()
        # 确保传递settings_manager到翻译页面
        self.current_page = TranslationPage(
            self.content_area,
            word_manager=self.word_manager,
            settings_manager=self.settings_manager,
            font_config=self.font_config
        )
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到翻译练习页面")
    
    def _show_review_page(self):
        """显示单词复习页面"""
        self._clear_content_area()
        # 确保传递settings_manager到复习页面
        self.current_page = ReviewPage(
            self.content_area,
            word_manager=self.word_manager,
            settings_manager=self.settings_manager,
            font_config=self.font_config
        )
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到单词复习页面")
    
    def _show_learning_page(self):
        """显示学习模式页面"""
        self._clear_content_area()
        
        # 创建学习管理器
        learning_manager = LearningManager(
            data_manager=self.word_manager,
            scheduler=self.word_manager,
            audio_player=self.audio_player,
            logger=self.word_manager
        )
        
        # 创建学习页面并确保传递settings_manager
        self.current_page = LearningPage(
            self.content_area,
            learning_manager=learning_manager,
            word_manager=self.word_manager,
            settings_manager=self.settings_manager,
            font_config=self.font_config,
            bg='white'
        )
        self.current_page.pack(fill=tk.BOTH, expand=True)
        
        log_info("切换到学习模式页面")
    
    def _show_statistics(self):
        """显示学习统计页面"""
        self._clear_content_area()
        
        stats_frame = tk.Frame(self.content_area, bg='white')
        stats_frame.pack(expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(
            stats_frame, 
            text="学习统计", 
            font=self.font_config['header'],
            bg='white'
        )
        title_label.pack(pady=30)
        
        # 获取进度数据
        progress = self.word_manager.get_progress()
        
        # 创建统计信息表格
        stats_data = [
            ("总学习单词数", str(progress.get('total_learned', 0))),
            ("总练习次数", str(progress.get('total_attempts', 0))),
            ("正确次数", str(progress.get('total_correct', 0))),
            ("正确率", f"{progress.get('correct_rate', 0) * 100:.1f}%"),
            ("最后学习时间", progress.get('last_session', '未开始')),
            ("错误单词数", str(len(self.word_manager.get_wrong_words())))
        ]
        
        for i, (label_text, value_text) in enumerate(stats_data):
            row_frame = tk.Frame(stats_frame, bg='white')
            row_frame.pack(pady=10, padx=50, fill=tk.X)
            
            label = tk.Label(
                row_frame, 
                text=label_text, 
                font=self.font_config['normal'],
                width=20,
                bg='white',
                anchor='w'
            )
            label.pack(side=tk.LEFT)
            
            value = tk.Label(
                row_frame, 
                text=value_text, 
                font=self.font_config['normal'],
                bg='white',
                fg='#0066cc',
                anchor='w'
            )
            value.pack(side=tk.LEFT, padx=20)
    
    # _show_settings方法已被_settings_page替代，保留_apply_decay方法用于设置页面
    
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