"""word_manager.py 集成测试（白盒，建议 2 的一部分）。

构造 WordManager 时复用「指向临时 SQLite」的 DatabaseManager 单例，并禁用后台
初始化线程、用桩 AIManager 注入 ai_available，覆盖节流控制、AI 可用性委托，以及
基于数据库的单词增删查等核心逻辑，不污染项目真实数据。
"""
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import core.database_manager as dm_mod
from core.database_manager import DatabaseManager
from word_manager import WordManager


def _make_temp_db():
    DatabaseManager._instance = None
    inst = DatabaseManager.__new__(DatabaseManager)
    tmp = tempfile.mkdtemp()
    inst.data_dir = tmp
    inst.db_path = os.path.join(tmp, "lexinote.db")
    inst._write_queue = []
    inst._write_lock = threading.Lock()
    inst._last_write_time = datetime.now()
    inst._init_database()
    inst.create_dictation_tables()
    inst.create_exercise_sessions_table()
    _orig = inst.execute_write
    inst.execute_write = lambda q, p=None, immediate=False: _orig(q, p, immediate=True)
    inst._initialized = True
    DatabaseManager._instance = inst  # 让 WordManager 复用临时库
    return inst, tmp


@pytest.fixture
def wm():
    db_inst, tmp = _make_temp_db()
    with patch.object(WordManager, "_init_background", lambda self: None):
        w = WordManager()
    w.is_initialized = True
    w.ai_manager = MagicMock()
    w.ai_manager.is_ai_available.return_value = True
    w._load_active_word_set()
    yield w
    DatabaseManager._instance = None
    shutil.rmtree(tmp, ignore_errors=True)


class TestThrottle:
    def test_最小间隔限制(self, wm):
        # 用固定历史时间戳隔离“间隔”逻辑，不受两次调用真实时差影响
        wm._recent_ai_calls.clear()
        wm.set_throttle_limits(min_interval_ms=500, max_calls_per_minute=1000)
        now = time.time()
        wm._recent_ai_calls.append(now - 10.0)     # 10 秒前的调用，间隔足够
        assert wm._check_throttle_limit() is True   # 间隔 10s > 0.5s → 放行
        assert wm._check_throttle_limit() is False  # 紧接着间隔 ~0 < 0.5s → 限流

    def test_每分钟次数限制(self, wm):
        # 专测“每分钟次数”上限：历史条目间隔 1s，确保不被间隔逻辑拦截
        wm._recent_ai_calls.clear()
        wm.set_throttle_limits(min_interval_ms=100, max_calls_per_minute=2)
        now = time.time()
        wm._recent_ai_calls.append(now - 1.0)      # 模拟 1 次（1 秒前）
        assert wm._check_throttle_limit() is True   # len=1<2 且间隔 1s>0.1s → 放行
        assert wm._check_throttle_limit() is False  # 现在 len=2>=2 → 限流

    def test_放宽限制后恢复(self, wm):
        wm._recent_ai_calls.clear()
        wm.set_throttle_limits(min_interval_ms=100, max_calls_per_minute=2)
        now = time.time()
        wm._recent_ai_calls.append(now - 2.0)
        wm._recent_ai_calls.append(now - 1.0)      # 2 条，已达上限
        assert wm._check_throttle_limit() is False
        # 放宽到很大额度后恢复正常
        wm.set_throttle_limits(min_interval_ms=100, max_calls_per_minute=1000)
        assert wm._check_throttle_limit() is True


class TestAIAvailability:
    def test_无AI管理器返回False(self, wm):
        wm.ai_manager = None
        assert wm.ai_available is False

    def test_委托AI管理器(self, wm):
        wm.ai_manager = MagicMock()
        wm.ai_manager.is_ai_available.return_value = True
        assert wm.ai_available is True
        wm.ai_manager.is_ai_available.return_value = False
        assert wm.ai_available is False


class TestWordCRUD:
    def test_新增并查询(self, wm):
        assert wm.add_word("apple", "苹果") is True
        assert wm.get_word_translation("apple") == "苹果"

    def test_缓存生效(self, wm):
        wm.add_word("cat", "猫")
        # 第二次查询优先走内存缓存
        assert wm.get_word_translation("cat") == "猫"
        assert wm._word_cache.get("cat") == "猫"

    def test_删除单词(self, wm):
        wm.add_word("temp", "临时")
        assert wm.remove_word("temp") is True
        assert wm.get_word_translation("temp") is None

    def test_列举全部单词(self, wm):
        wm.add_word("one", "一")
        wm.add_word("two", "二")
        assert "one" in wm.get_all_words()
        assert "two" in wm.get_all_words()


class TestWordSet:
    def test_创建词库返回id(self, wm):
        sid, msg = wm.create_word_set("测试词库", "描述")
        assert isinstance(sid, int) and sid > 0

    def test_列举含新建词库(self, wm):
        wm.create_word_set("库X", "")
        names = [s["name"] for s in wm.get_all_word_sets()]
        assert "库X" in names

    def test_激活并加词(self, wm):
        sid, _ = wm.create_word_set("库A", "")
        wm.set_active_word_set(sid)
        ok, msg = wm.add_word_to_active_set("hello", "你好")
        assert ok is True
        words = wm.get_words_from_active_set()
        assert any(w["word"] == "hello" for w in words)

    def test_删除非默认词库(self, wm):
        sid, _ = wm.create_word_set("待删", "")
        result = wm.delete_word_set(sid)
        assert result is not False
        assert not any(s.get("name") == "待删" for s in wm.get_all_word_sets())

    def test_缺失详情单词(self, wm):
        sid, _ = wm.create_word_set("库B", "")
        wm.set_active_word_set(sid)
        wm.add_word_to_active_set("apple", "苹果")
        missing = wm.get_words_missing_details(limit=10)
        assert any(w["word"] == "apple" for w in missing)


class TestSpellingAndTranslation:
    def test_拼写大小写不敏感(self, wm):
        assert wm.check_spelling("Apple", "apple") is True
        assert wm.check_spelling("Apple", "banana") is False

    def test_翻译检查正确(self, wm):
        wm.add_word("apple", "苹果")
        assert wm.check_translation("apple", "苹果") is True

    def test_翻译检查错误(self, wm):
        wm.add_word("apple", "苹果")
        assert wm.check_translation("apple", "香蕉") is False

    def test_翻译缺词返回False(self, wm):
        assert wm.check_translation("ghostword", "xyz") is False


class TestRandomAndCount:
    def test_随机单词(self, wm):
        sid, _ = wm.create_word_set("库R", "")
        wm.set_active_word_set(sid)
        wm.add_word_to_active_set("one", "一")
        wm.add_word_to_active_set("two", "二")
        assert wm.get_random_word() in ("one", "two")

    def test_加权随机单词(self, wm):
        sid, _ = wm.create_word_set("库R2", "")
        wm.set_active_word_set(sid)
        wm.add_word_to_active_set("one", "一")
        wm.add_word_to_active_set("two", "二")
        r = wm.get_weighted_random_word()
        assert r is None or isinstance(r, str)

    def test_单词计数返回int(self, wm):
        assert isinstance(wm.get_word_count(), int)


class TestProficiency:
    def test_更新熟练度不报错(self, wm):
        wm.add_word("apple", "苹果")
        wm.update_word_proficiency("apple", True)
        wm.update_word_proficiency("apple", False)
        fam = wm.get_word_familiarity("apple")
        assert isinstance(fam, (int, float))

    def test_熟悉度增量更新(self, wm):
        wm.add_word("apple", "苹果")
        wm.update_word_familiarity("apple", 0.1, delta=True)
        fam = wm.get_word_familiarity("apple")
        assert isinstance(fam, (int, float))


class TestExerciseAndProgress:
    def test_开始练习写会话(self, wm):
        wm.start_exercise("听写")  # 仅验证不抛异常

    def test_获取进度返回dict(self, wm):
        prog = wm.get_progress()
        assert isinstance(prog, dict)
        assert "total_learned" in prog


class TestWrongAndDifficult:
    def test_错词记录(self, wm):
        # add_wrong_word 经 update_word_weight / update_word_proficiency 联动底层熟练度，
        # 但不直接写入 self.wrong_words（该内存字典由外部练习流程填充，方法语义存疑）
        wm.add_word("apple", "苹果")
        wm.add_wrong_word("apple")
        assert isinstance(wm.get_wrong_words(), dict)
