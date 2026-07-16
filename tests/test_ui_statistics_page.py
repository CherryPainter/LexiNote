"""ui/statistics_page.py 白盒测试。

使用 headless tkinter：用一个被注入具体返回值的 statistics_manager（通过
word_manager.statistics_manager 提供）驱动各 _load_* 方法，验证：
- _load_summary_stats 综合统计标签聚合
- _load_weekly_trend 空数据占位 / 有数据绘制
- _load_proficiency_distribution 空分布跳过 / 有分布绘制扇形
- _load_word_set_stats 词库表格填充
- _load_recent_progress 最近记录填充与对错映射
- refresh_data 刷新入口
- 无统计管理器时给出警告并安全返回
"""
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from ui.statistics_page import StatisticsPage


def _make_statistics_manager():
    sm = MagicMock()
    sm.get_summary_stats.return_value = {
        "total_words": 100,
        "learned_words": 50,
        "total_practices": 10,
        "total_correct": 8,
        "overall_accuracy": 0.8,
        "today_practices": 3,
        "today_accuracy": 0.9,
        "last_session": "2025-01-01",
    }
    sm.get_weekly_stats.return_value = [
        {"date": "2025-01-01", "practices": 3},
        {"date": "2025-01-02", "practices": 5},
    ]
    sm.get_proficiency_stats.return_value = {
        "未学习": 10,
        "不熟悉": 5,
        "一般": 3,
        "熟练": 2,
    }
    sm.get_word_set_stats.return_value = {
        "CET4": {"word_count": 100, "learned_count": 50, "progress": 0.5},
    }
    sm.get_recent_progress.return_value = [
        {"word": "apple", "is_correct": True, "practice_date": "2025-01-01"},
        {"word": "banana", "is_correct": False, "practice_date": "2025-01-02"},
    ]
    return sm


@pytest.fixture
def statistics_page(tk_root):
    wm = MagicMock()
    wm.statistics_manager = _make_statistics_manager()
    wm.active_word_set_id = 1
    page = StatisticsPage(tk_root, word_manager=wm)
    yield page
    page.destroy()


# ---------------------------------------------------------------------------
# 综合统计
# ---------------------------------------------------------------------------
class TestSummaryStats:
    def test_综合统计标签填充(self, statistics_page):
        # 注意：数值类标签以 int 形式写入，tkinter 会原样存储
        assert statistics_page.total_words_value.cget("text") == 100
        assert statistics_page.learned_words_value.cget("text") == 50
        assert statistics_page.total_correct_value.cget("text") == 8
        # 总体正确率按百分比格式化
        assert statistics_page.overall_accuracy_value.cget("text") == "80.00%"
        assert statistics_page.last_session_value.cget("text") == "2025-01-01"


# ---------------------------------------------------------------------------
# 本周趋势
# ---------------------------------------------------------------------------
class TestWeeklyTrend:
    def test_空数据显示占位(self, statistics_page):
        statistics_page.statistics_manager.get_weekly_stats.return_value = []
        statistics_page._load_weekly_trend()
        # 空数据时画布上应出现“暂无学习数据”文本图元
        assert len(statistics_page.weekly_trend_canvas.find_all()) > 0

    def test_有数据绘制折线(self, statistics_page):
        statistics_page.statistics_manager.get_weekly_stats.return_value = [
            {"date": "2025-01-01", "practices": 3},
            {"date": "2025-01-02", "practices": 5},
        ]
        statistics_page._load_weekly_trend()
        assert len(statistics_page.weekly_trend_canvas.find_all()) > 0


# ---------------------------------------------------------------------------
# 熟练度分布
# ---------------------------------------------------------------------------
class TestProficiencyDistribution:
    def test_空分布不绘制(self, statistics_page):
        statistics_page.statistics_manager.get_proficiency_stats.return_value = {}
        statistics_page._load_proficiency_distribution()
        assert len(statistics_page.proficiency_canvas.find_all()) == 0

    def test_有分布绘制扇形(self, statistics_page):
        statistics_page.statistics_manager.get_proficiency_stats.return_value = {
            "未学习": 10, "不熟悉": 5, "一般": 3, "熟练": 2,
        }
        statistics_page._load_proficiency_distribution()
        assert len(statistics_page.proficiency_canvas.find_all()) > 0


# ---------------------------------------------------------------------------
# 词库统计 / 最近记录
# ---------------------------------------------------------------------------
class TestWordSetAndRecent:
    def test_词库统计填充(self, statistics_page):
        children = statistics_page.word_set_tree.get_children()
        assert len(children) == 1
        values = statistics_page.word_set_tree.item(children[0])["values"]
        assert values[0] == "CET4"
        assert values[1] == 100
        assert values[3] == "50.00%"  # 进度百分比

    def test_最近记录填充与对错映射(self, statistics_page):
        children = statistics_page.recent_tree.get_children()
        assert len(children) == 2
        first = statistics_page.recent_tree.item(children[0])["values"]
        second = statistics_page.recent_tree.item(children[1])["values"]
        assert first[0] == "apple" and first[1] == "正确"
        assert second[0] == "banana" and second[1] == "错误"


# ---------------------------------------------------------------------------
# 刷新入口
# ---------------------------------------------------------------------------
class TestRefresh:
    def test_刷新数据重新加载(self, statistics_page):
        # 改变返回值后刷新，应反映新数据
        statistics_page.statistics_manager.get_summary_stats.return_value = {
            "total_words": 7, "learned_words": 1, "total_practices": 2,
            "total_correct": 1, "overall_accuracy": 0.5, "today_practices": 0,
            "today_accuracy": 0.0, "last_session": "2025-02-02",
        }
        statistics_page.refresh_data()
        assert statistics_page.total_words_value.cget("text") == 7


# ---------------------------------------------------------------------------
# 无统计管理器
# ---------------------------------------------------------------------------
class TestNoManager:
    def test_无统计管理器时警告并返回(self, tk_root):
        wm = MagicMock()
        wm.statistics_manager = None  # 关键：没有统计管理器
        with patch("ui.statistics_page.messagebox.showwarning") as warn:
            page = StatisticsPage(tk_root, word_manager=wm)
        warn.assert_called_once()
        page.destroy()
