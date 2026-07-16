"""core/database_manager.py 数据层集成测试（白盒）。

用「绕过 __init__ + 重定向临时目录」的方式构建一个指向临时 SQLite 文件的
DatabaseManager 单例，覆盖单词 CRUD、熟练度、学习进度、词库、设置、AI 缓存等
数据持久化逻辑，不污染项目的真实 data/lexinote.db。
"""
import os
import shutil
import tempfile
import threading
from datetime import datetime

import pytest

import core.database_manager as dm_mod
from core.database_manager import DatabaseManager


@pytest.fixture
def db():
    """构建指向临时目录的 DatabaseManager 单例。"""
    DatabaseManager._instance = None
    inst = DatabaseManager.__new__(DatabaseManager)
    tmp = tempfile.mkdtemp()
    inst.data_dir = tmp
    inst.db_path = os.path.join(tmp, "lexinote.db")
    inst._write_queue = []
    inst._write_lock = threading.Lock()
    inst._last_write_time = datetime.now()
    # 手动初始化表结构（temp 目录下无 word_dict.json，导入会优雅跳过）
    inst._init_database()
    inst.create_dictation_tables()
    inst.create_exercise_sessions_table()
    inst._initialized = True
    # 不启动后台写线程；强制所有写入立即落库，保证测试的确定性
    _orig_write = inst.execute_write

    def _immediate_write(query, params=None, immediate=False):
        return _orig_write(query, params, immediate=True)

    inst.execute_write = _immediate_write
    yield inst
    DatabaseManager._instance = None
    shutil.rmtree(tmp, ignore_errors=True)


class TestWordCRUD:
    def test_新增与查询单词(self, db):
        assert db.add_word("apple", "苹果") is True
        assert db.get_word_translation("apple") == "苹果"

    def test_批量新增与列举(self, db):
        for w, t in [("cat", "猫"), ("dog", "狗"), ("pig", "猪")]:
            db.add_word(w, t)
        words = db.get_all_words()
        assert set(words) == {"cat", "dog", "pig"}

    def test_查询不存在返回None(self, db):
        assert db.get_word_translation("nonexistent") is None

    def test_更新翻译(self, db):
        db.add_word("book", "书")
        assert db.update_word_translation("book", "书籍") is True
        assert db.get_word_translation("book") == "书籍"

    def test_按id查询与按id更新(self, db):
        db.add_word("pen", "笔")
        wid = db.get_word_by_id(1)["id"]
        assert db.update_word(wid, translation="钢笔") == (True, "更新成功")
        assert db.get_word_translation("pen") == "钢笔"

    def test_删除单词(self, db):
        db.add_word("temp", "临时")
        assert db.remove_word("temp") is True
        assert db.get_word_translation("temp") is None


class TestProficiencyAndProgress:
    def _column(self, db, word, col):
        rows = db.execute_read(
            f"SELECT {col} FROM words WHERE word = ?", (word,))
        return rows[0][col] if rows else None

    def test_熟练度写入与读取(self, db):
        db.add_word("sky", "天空")
        db.update_proficiency("sky", 0.75)
        assert abs(self._column(db, "sky", "proficiency") - 0.75) < 1e-6

    def test_熟练度边界_0与1(self, db):
        db.add_word("a", "甲")
        db.add_word("b", "乙")
        db.update_proficiency("a", 0.0)
        db.update_proficiency("b", 1.0)
        assert self._column(db, "a", "proficiency") == 0.0
        assert self._column(db, "b", "proficiency") == 1.0

    def test_学习记录可追溯(self, db):
        db.add_word("run", "跑")
        db.add_progress_record("run", is_correct=1, proficiency_change=0.1)
        db.add_progress_record("run", is_correct=0, proficiency_change=-0.1)
        prog = db.get_word_progress("run")
        # progress 表记录了两次练习，计算熟练度 = 1/2
        assert prog is not None
        assert abs(prog["proficiency"] - 0.5) < 1e-6
        assert prog["total_count"] == 2

    def test_未练习单词进度返回None(self, db):
        db.add_word("idle", "闲")
        # 无进度记录时 get_word_progress 返回 None
        assert db.get_word_progress("idle") is None


class TestWordSets:
    def test_创建与按名查询(self, db):
        sid, _ = db.create_word_set("考研词汇", "考研必备")
        assert isinstance(sid, int) and sid > 0
        got = db.get_word_set_by_name("考研词汇")
        assert got is not None
        assert got["id"] == sid

    def test_向词库添加单词(self, db):
        sid, _ = db.create_word_set("CET4", "四级")
        db.add_word("happy", "快乐")
        assert db.add_word_to_set(sid, "happy", "快乐") == (True, "添加成功")
        in_set = db.get_words_by_set_id(sid)
        assert any(w["word"] == "happy" for w in in_set)

    def test_默认词库存在(self, db):
        # _init_database 会创建默认词库
        default = db.get_word_set_by_name("默认词库")
        assert default is not None


class TestSettings:
    def test_设置读取往返(self, db):
        db.set_setting("theme", "dark")
        assert db.get_setting("theme") == "dark"

    def test_缺失设置返回默认(self, db):
        assert db.get_setting("not_exist_key", "fallback") == "fallback"

    def test_设置覆盖(self, db):
        db.set_setting("voice_speed", "1.0")
        db.set_setting("voice_speed", "1.5")
        assert db.get_setting("voice_speed") == "1.5"


class TestAICache:
    def test_缓存与命中(self, db):
        db.cache_ai_response("什么是单词?", "单词是语言最小单位")
        assert db.get_cached_ai_response("什么是单词?") == "单词是语言最小单位"

    def test_未命中返回None(self, db):
        assert db.get_cached_ai_response("不存在的提示") is None
