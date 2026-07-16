"""settings_manager / word_manager / statistics 白盒测试。

通过设置管理器单例的缓存与数据库 mock，验证：
- AI 模式（off/local/cloud）的读写与兼容逻辑
- 云端配置存取
- WordManager.ai_available 属性正确委托给 AIManager
- StatisticsManager 各统计查询的数值正确性、熟练度区间边界、除零保护
"""
import threading
from unittest.mock import MagicMock

import pytest

from core.settings_manager import SettingsManager
from statistics import StatisticsManager
import word_manager as wm_mod


# ---------------------------------------------------------------------------
# SettingsManager（绕过 __init__）
# ---------------------------------------------------------------------------
def make_sm():
    sm = SettingsManager.__new__(SettingsManager)
    sm._settings_cache = {}
    sm._cache_lock = threading.RLock()
    sm.db_manager = MagicMock()
    sm.db_manager.get_setting.return_value = None  # 缺失键默认返回 None，与真实 DB 行为一致
    sm._listeners = {}
    sm._listeners_lock = threading.RLock()
    return sm


class TestSettingsAiMode:
    def test_缓存有效模式直接返回(self):
        sm = make_sm()
        sm._settings_cache["ai_mode"] = "local"
        assert sm.get_ai_mode() == "local"

    def test_无效模式且云开启视为cloud(self):
        sm = make_sm()
        sm._settings_cache["ai_mode"] = "乱写"
        sm._settings_cache["cloud_ai_enabled"] = True
        assert sm.get_ai_mode() == "cloud"

    def test_无效模式且云关闭视为off(self):
        sm = make_sm()
        sm._settings_cache["ai_mode"] = "乱写"
        sm._settings_cache["cloud_ai_enabled"] = False
        assert sm.get_ai_mode() == "off"

    def test_无配置默认off(self):
        sm = make_sm()
        assert sm.get_ai_mode() == "off"

    def test_set_ai_mode有效(self):
        sm = make_sm()
        assert sm.set_ai_mode("cloud") is True
        assert sm._settings_cache["ai_mode"] == "cloud"
        sm.db_manager.set_setting.assert_called_once()

    def test_set_ai_mode无效返回False(self):
        sm = make_sm()
        assert sm.set_ai_mode("weird") is False
        assert "ai_mode" not in sm._settings_cache

    def test_云端配置存取(self):
        sm = make_sm()
        ok = sm.save_cloud_ai_config(True, "https://api", "key123", "qwen")
        assert ok is True
        assert sm.get_cloud_ai_enabled() is True
        assert sm.get_cloud_ai_api_url() == "https://api"
        assert sm.get_cloud_ai_api_key() == "key123"
        assert sm.get_cloud_ai_model_name() == "qwen"


class TestSettingsCacheAndListener:
    def test_get_setting命中缓存(self):
        sm = make_sm()
        sm._settings_cache["ai_model"] = "gemma3n"
        assert sm.get_setting("ai_model") == "gemma3n"

    def test_set_setting更新缓存并入库(self):
        sm = make_sm()
        sm.set_setting("voice_speed", 1.5)
        assert sm._settings_cache["voice_speed"] == 1.5
        sm.db_manager.set_setting.assert_called_with("voice_speed", 1.5)

    def test_监听器在变更时触发(self):
        sm = make_sm()
        cb = MagicMock()
        sm.register_listener("ai_mode", cb)
        sm.set_ai_mode("local")
        cb.assert_called_once_with("ai_mode", "local")

    def test_set_voice_speed范围限制(self):
        sm = make_sm()
        sm.set_voice_speed(99.0)
        assert sm._settings_cache["voice_speed"] == 3.0
        sm.set_voice_speed(0.1)
        assert sm._settings_cache["voice_speed"] == 0.5


# ---------------------------------------------------------------------------
# WordManager.ai_available 属性委托
# ---------------------------------------------------------------------------
class TestWordManagerAiAvailable:
    def test_委托给AIManager为True(self):
        wm = wm_mod.WordManager.__new__(wm_mod.WordManager)
        wm.ai_manager = MagicMock()
        wm.ai_manager.is_ai_available.return_value = True
        assert wm.ai_available is True

    def test_委托给AIManager为False(self):
        wm = wm_mod.WordManager.__new__(wm_mod.WordManager)
        wm.ai_manager = MagicMock()
        wm.ai_manager.is_ai_available.return_value = False
        assert wm.ai_available is False

    def test_ai_manager为None返回False(self):
        wm = wm_mod.WordManager.__new__(wm_mod.WordManager)
        wm.ai_manager = None
        assert wm.ai_available is False


# ---------------------------------------------------------------------------
# StatisticsManager
# ---------------------------------------------------------------------------
UNIVERSAL_ROW = [{'count': 0, 'total': 0, 'correct': 0, 'last_date': None}]


def make_stat(db=None):
    db = db or MagicMock()
    db.execute_read.return_value = UNIVERSAL_ROW
    return StatisticsManager(db)


class TestStatistics:
    def test_总单词数(self):
        db = MagicMock()
        db.execute_read.return_value = [{'count': 42}]
        assert StatisticsManager(db).get_total_word_count() == 42

    def test_查询异常返回0(self):
        db = MagicMock()
        db.execute_read.side_effect = Exception("db err")
        assert StatisticsManager(db).get_total_word_count() == 0

    def test_总体正确率除零保护(self):
        db = MagicMock()
        db.execute_read.return_value = [{'total': 0, 'correct': 0}]
        assert StatisticsManager(db).get_overall_accuracy() == 0.0

    def test_总体正确率计算(self):
        db = MagicMock()
        db.execute_read.return_value = [{'total': 10, 'correct': 7}]
        assert abs(StatisticsManager(db).get_overall_accuracy() - 0.7) < 1e-9

    def test_每日统计除零保护(self):
        db = MagicMock()
        db.execute_read.return_value = [{'count': 0}]
        s = StatisticsManager(db).get_daily_stats("2026-07-16")
        assert s["accuracy"] == 0.0
        assert s["practices"] == 0

    def test_每日统计正确率(self):
        db = MagicMock()
        db.execute_read.side_effect = [
            [{'count': 4}],   # practices
            [{'count': 2}],   # correct
            [{'count': 3}],   # words
        ]
        s = StatisticsManager(db).get_daily_stats("2026-07-16")
        assert s["practices"] == 4
        assert s["correct"] == 2
        assert s["accuracy"] == 0.5

    def test_熟练度区间边界分类(self):
        sm = make_sm_settings()
        db = MagicMock()
        calls = []
        def fake(sql, params=None):
            calls.append((sql, params))
            return [{'count': 1}]
        db.execute_read.side_effect = fake
        stats = StatisticsManager(db).get_proficiency_stats()
        # 四个区间均出现
        assert set(stats.keys()) == {"未学习", "不熟悉", "一般", "熟练"}
        # 校验 SQL 边界值
        # 未学习：proficiency = 0
        assert "PROFICIENCY = ?" in calls[0][0].upper()
        assert calls[0][1] == (0,)
        # 不熟悉：0 < p <= 0.3
        assert "PROFICIENCY > ? AND PROFICIENCY <= ?" in calls[1][0].upper()
        assert calls[1][1] == (0, 0.3)
        # 一般：0.3 < p <= 0.7
        assert calls[2][1] == (0.3, 0.7)
        # 熟练：0.7 < p <= 1.0
        assert calls[3][1] == (0.7, 1.0)

    def test_综合统计含关键字段(self):
        s = make_stat()
        summary = s.get_summary_stats()
        for k in ["total_words", "learned_words", "overall_accuracy",
                  "proficiency_distribution", "last_session"]:
            assert k in summary

    def test_周报返回7天且升序(self):
        s = make_stat()
        weeks = s.get_weekly_stats()
        assert len(weeks) == 7
        dates = [w["date"] for w in weeks]
        assert dates == sorted(dates)

    def test_最近进度解析(self):
        db = MagicMock()
        db.execute_read.return_value = [
            {"word": "apple", "is_correct": 1, "practice_date": "2026-07-16"},
            {"word": "banana", "is_correct": 0, "practice_date": "2026-07-15"},
        ]
        rows = StatisticsManager(db).get_recent_progress(limit=2)
        assert len(rows) == 2
        assert rows[0]["is_correct"] is True
        assert rows[1]["is_correct"] is False

    def test_词库统计(self):
        db = MagicMock()
        def fake(sql, params=None):
            if "FROM WORD_SETS" in sql.upper():
                return [{"id": 1, "name": "CET4"}]
            return [{"count": 5}]
        db.execute_read.side_effect = fake
        s = StatisticsManager(db).get_word_set_stats()
        assert "CET4" in s
        assert s["CET4"]["word_count"] == 5
        assert s["CET4"]["learned_count"] == 5
        assert s["CET4"]["progress"] == 1.0

    def test_熟练度按词库过滤(self):
        db = MagicMock()
        calls = []
        def fake(sql, params=None):
            calls.append((sql, params))
            return [{"count": 1}]
        db.execute_read.side_effect = fake
        StatisticsManager(db).get_proficiency_stats(set_id=3)
        # 每个区间查询都带 set_id 参数（含“未学习”桶）
        for sql, params in calls:
            if "proficiency" in sql.lower():
                assert 3 in params


def make_sm_settings():
    # 占位：与上方 test 无关，仅为可读性；Stats 测试不依赖 SettingsManager
    return None
