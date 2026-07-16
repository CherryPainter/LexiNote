"""
学习统计页面

展示用户学习数据的详细统计信息和分析
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import math

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import log_error
from ui.components.scrollable_frame import create_scrollable_frame
from ui.font_config import FontConfig


class StatisticsPage(tk.Frame):
    """
    学习统计页面，展示用户学习数据的详细统计信息和分析
    """

    def __init__(self, parent, word_manager=None, settings_manager=None, font_config=None, **kwargs):
        """
        初始化统计页面

        Args:
            parent: 父窗口组件
            word_manager: 单词管理器实例
            settings_manager: 设置管理器实例
            font_config: 字体配置字典
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.word_manager = word_manager
        self.settings_manager = settings_manager
        self.font_config = font_config or {'title': ("Arial", 48, "bold"), 'header': ("Arial", 24), 'normal': ("Arial", 12), 'button': ("Arial", 12)}

        # 获取统计管理器
        self.statistics_manager = word_manager.statistics_manager if word_manager else None

        # 创建UI组件
        self._create_widgets()

        # 加载统计数据
        self._load_statistics()

    def _create_widgets(self):
        """
        创建页面组件
        """
        # 设置页面背景
        self.configure(bg="#f0f0f0")

        # 创建标题
        title_label = tk.Label(
            self,
            text="学习统计",
            font=self.font_config.get('header', ("Arial", 24)),
            bg="#f0f0f0",
            fg="#333333"
        )
        title_label.pack(pady=20)

        # 创建滚动框架
        content_scroll_frame, content_frame, _, _ = create_scrollable_frame(self, padx=40, pady=20)
        content_scroll_frame.pack(fill=tk.BOTH, expand=True)

        # 创建综合统计卡片
        self._create_summary_stats_card(content_frame)

        # 创建本周学习趋势卡片
        self._create_weekly_trend_card(content_frame)

        # 创建熟练度分布卡片
        self._create_proficiency_distribution_card(content_frame)

        # 创建词库统计卡片
        self._create_word_set_stats_card(content_frame)

        # 创建最近学习记录卡片
        self._create_recent_progress_card(content_frame)

    def _create_summary_stats_card(self, parent):
        """
        创建综合统计卡片
        """
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2, padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)

        # 标题
        title = tk.Label(
            card,
            text="综合统计",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333333"
        )
        title.pack(anchor=tk.W, pady=(0, 15))

        # 创建统计网格
        grid_frame = tk.Frame(card, bg="white")
        grid_frame.pack(fill=tk.X)

        # 统计项标签和值
        stats = [
            ("总单词数", "total_words_value"),
            ("已学习单词", "learned_words_value"),
            ("总练习次数", "total_practices_value"),
            ("总正确次数", "total_correct_value"),
            ("总体正确率", "overall_accuracy_value"),
            ("今日练习次数", "today_practices_value"),
            ("今日正确率", "today_accuracy_value"),
            ("最后学习时间", "last_session_value")
        ]

        for i, (label_text, value_var) in enumerate(stats):
            row, col = divmod(i, 4)

            # 标签
            label = tk.Label(
                grid_frame,
                text=label_text,
                font=("Arial", 12),
                bg="white",
                fg="#666666"
            )
            label.grid(row=row*2, column=col, padx=20, pady=(0, 5), sticky=tk.W)

            # 值
            value = tk.Label(
                grid_frame,
                text="--",
                font=("Arial", 14, "bold"),
                bg="white",
                fg="#333333"
            )
            value.grid(row=row*2+1, column=col, padx=20, pady=(0, 15), sticky=tk.W)

            # 保存引用
            setattr(self, value_var, value)

    def _create_weekly_trend_card(self, parent):
        """
        创建本周学习趋势卡片
        """
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2, padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)

        # 标题
        title = tk.Label(
            card,
            text="本周学习趋势",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333333"
        )
        title.pack(anchor=tk.W, pady=(0, 15))

        # 趋势图表区域
        self.weekly_trend_canvas = tk.Canvas(card, width=600, height=200, bg="#f9f9f9")
        self.weekly_trend_canvas.pack(fill=tk.X)

    def _create_proficiency_distribution_card(self, parent):
        """
        创建熟练度分布卡片
        """
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2, padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)

        # 标题
        title = tk.Label(
            card,
            text="熟练度分布",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333333"
        )
        title.pack(anchor=tk.W, pady=(0, 15))

        # 创建分布图表
        self.proficiency_canvas = tk.Canvas(card, width=600, height=150, bg="#f9f9f9")
        self.proficiency_canvas.pack(fill=tk.X)

        # 熟练度图例
        legend_frame = tk.Frame(card, bg="white")
        legend_frame.pack(fill=tk.X, pady=10)

        proficiencies = [
            ("未学习", "#e0e0e0"),
            ("不熟悉", "#FF9800"),
            ("一般", "#2196F3"),
            ("熟练", "#4CAF50")
        ]

        for i, (label, color) in enumerate(proficiencies):
            legend_item = tk.Frame(legend_frame, bg="white")
            legend_item.pack(side=tk.LEFT, padx=20)

            color_box = tk.Frame(legend_item, width=20, height=20, bg=color)
            color_box.pack(side=tk.LEFT, padx=5)

            label = tk.Label(legend_item, text=label, font=("Arial", 12), bg="white")
            label.pack(side=tk.LEFT)

    def _create_word_set_stats_card(self, parent):
        """
        创建词库统计卡片
        """
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2, padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)

        # 标题
        title = tk.Label(
            card,
            text="词库统计",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333333"
        )
        title.pack(anchor=tk.W, pady=(0, 15))

        # 词库列表
        self.word_set_tree = ttk.Treeview(card, columns=("word_count", "learned_count", "progress"), show="headings")
        self.word_set_tree.heading("word_count", text="单词总数")
        self.word_set_tree.heading("learned_count", text="已学习")
        self.word_set_tree.heading("progress", text="学习进度")

        # 设置列宽
        self.word_set_tree.column("word_count", width=100, anchor=tk.CENTER)
        self.word_set_tree.column("learned_count", width=100, anchor=tk.CENTER)
        self.word_set_tree.column("progress", width=150, anchor=tk.CENTER)

        self.word_set_tree.pack(fill=tk.X)

    def _create_recent_progress_card(self, parent):
        """
        创建最近学习记录卡片
        """
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2, padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)

        # 标题
        title = tk.Label(
            card,
            text="最近学习记录",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#333333"
        )
        title.pack(anchor=tk.W, pady=(0, 15))

        # 最近记录列表
        self.recent_tree = ttk.Treeview(card, columns=("word", "result", "date"), show="headings")
        self.recent_tree.heading("word", text="单词")
        self.recent_tree.heading("result", text="结果")
        self.recent_tree.heading("date", text="练习时间")

        # 设置列宽
        self.recent_tree.column("word", width=150, anchor=tk.W)
        self.recent_tree.column("result", width=100, anchor=tk.CENTER)
        self.recent_tree.column("date", width=200, anchor=tk.CENTER)

        self.recent_tree.pack(fill=tk.X)

    def _load_statistics(self):
        """
        加载统计数据并更新UI
        """
        if not self.statistics_manager:
            messagebox.showwarning("警告", "统计管理器未初始化，无法加载统计数据")
            return

        try:
            # 强制更新UI，确保能获取到正确的画布尺寸
            self.update_idletasks()

            # 加载综合统计
            self._load_summary_stats()

            # 加载本周趋势
            self._load_weekly_trend()

            # 加载熟练度分布
            self._load_proficiency_distribution()

            # 加载词库统计
            self._load_word_set_stats()

            # 加载最近学习记录
            self._load_recent_progress()

        except Exception as e:
            log_error(f"加载统计数据失败: {str(e)}")
            messagebox.showerror("错误", f"加载统计数据失败: {str(e)}")

    def _load_summary_stats(self):
        """
        加载综合统计数据
        """
        # 获取当前激活的词库ID
        active_set_id = None
        if hasattr(self.word_manager, 'active_word_set_id'):
            active_set_id = self.word_manager.active_word_set_id

        summary_stats = self.statistics_manager.get_summary_stats(active_set_id)

        # 更新UI
        self.total_words_value.config(text=summary_stats['total_words'])
        self.learned_words_value.config(text=summary_stats['learned_words'])
        self.total_practices_value.config(text=summary_stats['total_practices'])
        self.total_correct_value.config(text=summary_stats['total_correct'])
        self.overall_accuracy_value.config(text=f"{summary_stats['overall_accuracy']:.2%}")
        self.today_practices_value.config(text=summary_stats['today_practices'])
        self.today_accuracy_value.config(text=f"{summary_stats['today_accuracy']:.2%}")
        self.last_session_value.config(text=summary_stats['last_session'])

    def _load_weekly_trend(self):
        """
        加载本周学习趋势数据
        """
        weekly_stats = self.statistics_manager.get_weekly_stats()

        # 清空画布
        self.weekly_trend_canvas.delete("all")

        if not weekly_stats:
            # 如果没有数据，显示提示
            canvas_width = self.weekly_trend_canvas.winfo_width() or 600
            canvas_height = self.weekly_trend_canvas.winfo_height() or 200
            self.weekly_trend_canvas.create_text(
                canvas_width / 2, canvas_height / 2,
                text="暂无学习数据",
                font=("Arial", 14),
                fill="#666666"
            )
            return

        # 获取画布尺寸
        canvas_width = self.weekly_trend_canvas.winfo_width() or 600
        canvas_height = self.weekly_trend_canvas.winfo_height() or 200

        # 计算绘图区域
        padding = 40
        plot_width = canvas_width - 2 * padding
        plot_height = canvas_height - 2 * padding

        # 计算最大值，确保至少为1
        max_practices = max(stat['practices'] for stat in weekly_stats) if weekly_stats else 1
        if max_practices == 0:
            max_practices = 1

        # 绘制坐标轴
        self.weekly_trend_canvas.create_line(padding, padding, padding, canvas_height - padding, width=2)
        self.weekly_trend_canvas.create_line(padding, canvas_height - padding, canvas_width - padding, canvas_height - padding, width=2)

        # 绘制数据点和线条
        point_width = plot_width / (len(weekly_stats) - 1) if len(weekly_stats) > 1 else 0

        for i, stat in enumerate(weekly_stats):
            # 确保x坐标在合理范围内
            x = padding + i * point_width
            # 确保y坐标在绘图区域内
            practices_ratio = stat['practices'] / max_practices
            y = canvas_height - padding - (practices_ratio * plot_height)

            # 绘制数据点
            self.weekly_trend_canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#2196F3", outline="#1976D2")

            # 绘制线条
            if i > 0:
                prev_x = padding + (i - 1) * point_width
                prev_y = canvas_height - padding - (weekly_stats[i-1]['practices'] / max_practices) * plot_height
                self.weekly_trend_canvas.create_line(prev_x, prev_y, x, y, width=2, fill="#2196F3")

            # 绘制日期标签
            date = stat['date'].split('-')[-2:]
            date_str = f"{date[0]}/{date[1]}"
            self.weekly_trend_canvas.create_text(x, canvas_height - padding + 20, text=date_str, font=("Arial", 10))

            # 绘制数值标签
            self.weekly_trend_canvas.create_text(x, y - 15, text=str(stat['practices']), font=("Arial", 10), fill="#333333")

    def _load_proficiency_distribution(self):
        """
        加载熟练度分布数据
        """
        # 获取当前激活的词库ID
        active_set_id = None
        if hasattr(self.word_manager, 'active_word_set_id'):
            active_set_id = self.word_manager.active_word_set_id

        # 根据当前激活词库获取熟练度分布统计
        proficiency_stats = self.statistics_manager.get_proficiency_stats(active_set_id)

        # 清空画布
        self.proficiency_canvas.delete("all")

        if not proficiency_stats:
            return

        # 获取画布尺寸
        canvas_width = self.proficiency_canvas.winfo_width() or 600
        canvas_height = self.proficiency_canvas.winfo_height() or 150

        # 计算绘图区域
        padding = 20
        plot_width = canvas_width - 2 * padding
        plot_height = canvas_height - 2 * padding

        # 计算总单词数
        total = sum(proficiency_stats.values())

        if total == 0:
            return

        # 定义颜色
        colors = {
            "未学习": "#e0e0e0",
            "不熟悉": "#FF9800",
            "一般": "#2196F3",
            "熟练": "#4CAF50"
        }

        # 绘制饼图
        current_angle = 0
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        radius = min(plot_width, plot_height) / 2

        # 按面积从小到大绘制，确保小部分不会被大部分覆盖：熟练 -> 一般 -> 不熟悉 -> 未学习
        draw_order = ["熟练", "一般", "不熟悉", "未学习"]

        for label in draw_order:
            count = proficiency_stats.get(label, 0)
            if count == 0:
                continue

            angle = (count / total) * 360

            # 绘制扇形
            self.proficiency_canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=current_angle,
                extent=angle,
                fill=colors[label],
                outline="white",
                width=2
            )

            # 只对较大的扇形绘制标签，避免标签重叠
            if angle > 5:  # 大于5度的扇形才显示标签
                mid_angle = current_angle + angle / 2
                # 使用三角函数计算标签位置
                radians = math.radians(mid_angle)
                label_x = center_x + (radius * 0.7) * math.cos(radians)
                label_y = center_y - (radius * 0.7) * math.sin(radians)

                self.proficiency_canvas.create_text(
                    label_x,
                    label_y,
                    text=f"{count}",
                    font=("Arial", 12, "bold"),
                    fill="white"
                )

            current_angle += angle

    def _load_word_set_stats(self):
        """
        加载词库统计数据
        """
        word_set_stats = self.statistics_manager.get_word_set_stats()

        # 清空树状图
        for item in self.word_set_tree.get_children():
            self.word_set_tree.delete(item)

        # 添加数据
        for set_name, stats in word_set_stats.items():
            progress = f"{stats['progress']:.2%}"
            self.word_set_tree.insert("", tk.END, values=(set_name, stats['word_count'], stats['learned_count'], progress))

    def _load_recent_progress(self):
        """
        加载最近学习记录
        """
        recent_progress = self.statistics_manager.get_recent_progress(limit=15)

        # 清空树状图
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        # 添加数据
        for record in recent_progress:
            result = "正确" if record['is_correct'] else "错误"
            self.recent_tree.insert("", tk.END, values=(record['word'], result, record['practice_date']))

    def refresh_data(self):
        """
        刷新统计数据
        """
        self._load_statistics()

    def on_enter(self):
        """
        进入页面时的操作
        """
        # 刷新数据
        self.refresh_data()

    def on_leave(self):
        """
        离开页面时的操作
        """
        pass
