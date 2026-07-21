import tkinter as tk
import tkinter.ttk as ttk
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
from ui.font_config import FontConfig
from ui.theme import COLORS, SPACING
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
        self.root.geometry("1080x720")
        self.root.minsize(600, 400)

        # 设置窗口图标
        try:
            # 优先使用程序安装目录（已由 main.py 切换并写入环境变量），
            # 兼容 Nuitka onefile（sys.executable 指向临时解压目录，不可用）
            _app_dir = os.environ.get("LEXINOTE_APP_DIR") or os.getcwd()
            icon_path = os.path.join(_app_dir, 'app.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                log_info(f"已设置窗口图标: {icon_path}")
            else:
                log_info(f"未找到图标文件: {icon_path}")
        except Exception as e:
            log_info(f"设置窗口图标时出错: {str(e)}")

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
        # 字体配置：统一收敛为 FontConfig，所有键均带默认值，杜绝 KeyError
        self.font_config = FontConfig()

    def _create_ui(self):
        """创建用户界面"""
        # 注册全局 ttk 主题（Treeview 等），保证与自定义按钮视觉一致
        self._setup_global_styles()

        # 创建主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建侧边导航
        self._create_sidebar()

        # 创建内容区域
        self._create_content_area()

        # 底部状态栏（非模态反馈 + 提示）
        self.status_bar = tk.Label(
            self.root,
            text="提示：从左侧选择学习模式开始练习",
            bg=COLORS["surface_alt"],
            fg=COLORS["text_secondary"],
            anchor=tk.W,
            font=self.font_config["small"],
            padx=SPACING["lg"],
            pady=SPACING["sm"],
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 显示欢迎页面
        self._show_welcome_page()

    def _setup_global_styles(self):
        """为 ttk 组件（Treeview 等）注册全局主题，统一视觉语言。"""
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=COLORS["surface"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["surface"],
            bordercolor=COLORS["border"],
            relief=tk.FLAT,
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["surface_alt"],
            foreground=COLORS["text_primary"],
            relief=tk.FLAT,
            borderwidth=1,
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["info_tint"])],
            foreground=[("selected", COLORS["text_primary"])],
        )

    def show_status(self, message: str, kind: str = "info", revert: int = 4000):
        """在底部状态栏显示提示，revert 毫秒后恢复默认提示。"""
        tint = {
            "info": COLORS["surface_alt"],
            "success": COLORS["primary_tint"],
            "warning": COLORS["warning_tint"],
            "error": COLORS["error_tint"],
        }.get(kind, COLORS["surface_alt"])
        self.status_bar.config(text=message, bg=tint)
        if revert > 0:
            self.root.after(revert, lambda: self.status_bar.config(
                text="提示：从左侧选择学习模式开始练习", bg=COLORS["surface_alt"]))

    def _set_active_nav(self, page_key: str):
        """切换侧边栏选中态：重置全部，高亮当前页。"""
        for key, btn in self._nav_buttons.items():
            active = (key == page_key)
            btn._is_active = active
            if active:
                btn.config(bg=COLORS["primary"], fg=COLORS["text_on_primary"],
                           highlightbackground=COLORS["primary"])
            else:
                btn.config(bg=COLORS["sidebar_btn"], fg=COLORS["text_primary"],
                           highlightbackground=COLORS["sidebar_btn"])

    def _create_sidebar(self):
        """创建侧边导航栏（使用设计 Token，带选中态与焦点环）"""
        self.sidebar = tk.Frame(self.main_frame, width=200, bg=COLORS["sidebar"],
                                bd=0, relief=tk.FLAT)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # 标题
        title_label = tk.Label(self.sidebar, text="LexiNote", font=self.font_config['title'],
                               bg=COLORS["sidebar"], fg=COLORS["text_primary"])
        title_label.pack(pady=SPACING["xl"])

        # 导航按钮：(显示文字, 对应 page_key, 点击回调)
        # 注意：emoji 图标暂保留（与你“代码禁 emoji”规则存冲突，待产品决策）
        nav_items = [
            ("📚 单词学习", "learning", self._show_learning_page),
            ("📝 听写练习", "dictation", self._show_dictation_page),
            ("🌐 翻译练习", "translation", self._show_translation_page),
            ("📊 单词复习", "review", self._show_review_page),
            ("🔤 完形填空", "cloze_test", self._show_cloze_test_page),
            ("📖 阅读理解", "reading_comprehension", self._show_reading_comprehension_page),
            ("📁 词库管理", "word_set", self._show_word_set_page),
            ("🤖 AI助手", "ai_assistant", self._show_ai_assistant_page),
            ("📈 学习统计", "statistics", self._show_statistics),
            ("⚙️ 设置", "settings", self._show_settings_page)
        ]

        self._nav_buttons: dict[str, tk.Button] = {}
        for text, key, command in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=self.font_config['button'],
                width=20,
                height=2,
                command=command,
                bg=COLORS["sidebar_btn"],
                fg=COLORS["text_primary"],
                relief=tk.FLAT,
                bd=0,
                activebackground=COLORS["sidebar_btn_hover"],
                cursor="hand2",
                takefocus=True,
                highlightthickness=2,
                highlightcolor=COLORS["info"],
                highlightbackground=COLORS["sidebar_btn"],
            )
            btn._is_active = False
            btn.pack(pady=SPACING["xs"], padx=SPACING["md"])

            # 悬停：仅非选中态切换底色
            btn.bind('<Enter>', lambda e, b=btn: b.config(
                bg=COLORS["sidebar_btn_hover"]) if not b._is_active else None)
            btn.bind('<Leave>', lambda e, b=btn: b.config(
                bg=COLORS["sidebar_btn"]) if not b._is_active else None)

            self._nav_buttons[key] = btn

    def _create_content_area(self):
        """创建内容区域"""
        self.content_area = tk.Frame(self.main_frame, bg=COLORS["surface"])
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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        self._set_active_nav(page_key)
        log_info("切换到设置页面")

    def _show_welcome_page(self):
        """显示欢迎页面"""
        # 欢迎页不属于任何导航项，清除选中态
        self._set_active_nav("")

        # 节流检查：如果当前页面已经是欢迎页面，则不执行任何操作
        if hasattr(self, 'current_page'):
            # 检查当前页面是否是欢迎页面的Frame
            if hasattr(self.current_page, 'master') and self.current_page.master == self.content_area:
                # 检查当前页面的第一个子组件是否是欢迎标题
                children = list(self.current_page.winfo_children())
                if children and hasattr(children[0], 'cget') and children[0].cget('text') == "欢迎使用 LexiNote":
                    return

        self._clear_content_area()

        welcome_frame = tk.Frame(self.content_area, bg=COLORS["surface"])
        welcome_frame.pack(expand=True, fill=tk.BOTH)

        # 设置当前页面为欢迎页面的Frame
        self.current_page = welcome_frame

        title_label = tk.Label(
            welcome_frame,
            text="欢迎使用 LexiNote",
            font=self.font_config['title'],
            bg=COLORS["surface"],
            fg=COLORS["text_primary"]
        )
        title_label.pack(pady=50)

        subtitle_label = tk.Label(
            welcome_frame,
            text="您的个人英语学习助手",
            font=self.font_config['header'],
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"]
        )
        subtitle_label.pack(pady=20)

        # 显示进度信息
        progress = self.word_manager.get_progress()
        progress_frame = tk.Frame(welcome_frame, bg=COLORS["surface"])
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
                bg=COLORS["surface"],
                fg=COLORS["text_primary"]
            )
            stat_label.pack(pady=10)

        hint_label = tk.Label(
            welcome_frame,
            text="请从左侧选择学习模式开始练习",
            font=self.font_config['normal'],
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"]
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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        self._set_active_nav(page_key)
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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        self._set_active_nav(page_key)
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
                font_config=self.font_config,
                audio_player=self.audio_player
            )

        # 先获取页面实例
        page = self._pages[page_key]

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        self._set_active_nav(page_key)
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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        self._set_active_nav(page_key)
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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        # 先记录页面切换日志，再执行初始化操作
        self._set_active_nav(page_key)
        log_info("切换到完形填空页面")

        # 调用页面的on_show方法
        if hasattr(self.current_page, 'on_show'):
            self.current_page.on_show()

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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        # 先记录页面切换日志，再执行初始化操作
        self._set_active_nav(page_key)
        log_info("切换到阅读理解页面")

        # 调用页面的on_show方法
        if hasattr(self.current_page, 'on_show'):
            self.current_page.on_show()

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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        # 调用页面的on_enter方法
        if hasattr(self.current_page, 'on_enter'):
            self.current_page.on_enter()

        self._set_active_nav(page_key)
        log_info("切换到学习统计页面")

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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        # 先记录页面切换日志，再执行初始化操作
        self._set_active_nav(page_key)
        log_info("切换到AI助手页面")

        # 调用页面的on_show方法
        if hasattr(self.current_page, 'on_show'):
            self.current_page.on_show()

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

        # 节流检查：如果当前页面已经是要显示的页面，则不执行任何操作
        if hasattr(self, 'current_page') and self.current_page == page:
            return

        # 清空内容区域
        self._clear_content_area()

        # 再设置当前页面并pack
        self.current_page = page
        self.current_page.pack(fill=tk.BOTH, expand=True)

        self._set_active_nav(page_key)
        log_info("切换到词库管理页面")

def main():
    """主函数"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
