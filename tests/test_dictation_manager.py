"""core/dictation.py 集成测试（白盒，P0b）。

复用 test_word_manager 同款隔离模式：临时 SQLite 单例 + MagicMock AIManager 的
WordManager 作为 DictationManager 的依赖，覆盖会话管理、队列导航、结果评分、
熟词统计与今日进度等核心逻辑，不依赖网络/音频。
"""
import os
import shutil
import tempfile
import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import core.database_manager as dm_mod
from core.database_manager import DatabaseManager
from core.dictation import DictationManager
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
    DatabaseManager._instance = inst
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


@pytest.fixture
def dm(wm):
    d = DictationManager(wm)
    yield d


class TestSession:
    def test_开始会话返回id(self, dm):
        sid = dm.start_session("single", "library", 5)
        assert isinstance(sid, int) and sid > 0
        assert dm.current_session is not None
        assert dm.current_session["mode"] == "single"

    def test_结束会话返回统计(self, dm):
        dm.start_session("single", "library", 5)
        dm.session_results.append(
            {"word": "apple", "user_input": "apple",
             "is_correct": True, "similarity": 1.0, "timestamp": "x"})
        stats = dm.end_session()
        assert isinstance(stats, dict)
        assert "accuracy" in stats
        assert dm.current_session is None

    def test_无会话结束返回None(self, dm):
        assert dm.end_session() is None


class TestQueueNavigation:
    def test_队列顺序与推进(self, dm):
        dm.current_queue = ["apple", "banana", "cat"]
        dm.current_queue_index = 0
        assert dm.next_in_queue() == "apple"
        assert dm.next_in_queue() == "banana"
        assert dm.has_next_in_queue() is True
        assert dm.next_in_queue() == "cat"
        assert dm.has_next_in_queue() is False
        assert dm.next_in_queue() is None

    def test_跳过当前单词(self, dm):
        dm.current_queue = ["apple"]
        dm.current_queue_index = 0
        assert dm.skip_current_word("apple", 1) is True
        assert any(c["word"] == "apple" and not c["is_correct"]
                   for c in dm.completed_words)


class TestProcessResult:
    def test_正确结果记录(self, dm, wm):
        wm.add_word("apple", "苹果")
        dm.start_session("single", "library", 5)
        dm.process_result("apple", "apple", True, 2)
        assert any(c["word"] == "apple" and c["is_correct"]
                   for c in dm.session_results)
        assert any(c["word"] == "apple" and c["is_correct"]
                   for c in dm.completed_words)

    def test_错误结果记录(self, dm, wm):
        wm.add_word("apple", "苹果")
        dm.start_session("single", "library", 5)
        dm.process_result("apple", "wrong", False, 2)
        assert any(c["word"] == "apple" and not c["is_correct"]
                   for c in dm.session_results)


class TestStats:
    def test_熟词数量返回int(self, dm):
        assert isinstance(dm.get_familiar_words_count(), int)

    def test_标记已学习不报错(self, dm):
        dm.mark_word_as_learned("apple")  # 仅验证不抛异常

    def test_今日进度返回dict(self, dm):
        prog = dm.get_today_progress()
        assert isinstance(prog, dict)
