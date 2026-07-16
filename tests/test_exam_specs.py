"""modules/exam_specs.py 白盒测试：命题蓝图、字段注入、单篇限制、题型随机、避免雷同。"""
import random

import pytest

from modules import exam_specs as esp


LEVELS = list(esp.CLOZE_SPECS.keys())
R_LEVELS = list(esp.READING_SPECS.keys())


# ---------------------------------------------------------------------------
# 完形填空
# ---------------------------------------------------------------------------
class TestBuildClozePrompt:
    def test_全部阶段都能构造且注入规格(self):
        for level in LEVELS:
            spec = esp.CLOZE_SPECS[level]
            p = esp.build_cloze_prompt(level, "科技")
            assert level in p
            assert f"挖空数量：{spec['blanks']}" in p
            wc_min, wc_max = spec["word_count"]
            assert f"{wc_min}-{wc_max} 词" in p
            assert spec["scoring"] in p
            # 每个考点都出现
            for pt in spec["points"]:
                assert pt in p

    def test_fstring占位符已替换(self):
        p = esp.build_cloze_prompt("高中", "环保")
        assert "{blanks}" not in p
        assert "{n}" not in p
        assert "BLANK_1" in p
        assert "BLANK_20" in p  # 高中 20 空

    def test_未知阶段回退到高中(self):
        p = esp.build_cloze_prompt("不存在的阶段", "x")
        assert "高中" in p
        assert "挖空数量：20" in p  # 高中 blanks

    def test_avoid_title被注入(self):
        p = esp.build_cloze_prompt("考研", "教育", avoid_title="旧标题示例")
        assert "旧标题示例" in p
        assert "不得与已有题目雷同" in p

    def test_avoid_title缺省时不注入(self):
        p = esp.build_cloze_prompt("考研", "教育")
        assert "不得与已有题目雷同" not in p

    def test_每次生成都含随机种子与角度(self):
        p1 = esp.build_cloze_prompt("高中", "音乐")
        p2 = esp.build_cloze_prompt("高中", "音乐")
        # 种子/角度随机，两次不应完全相同（极低概率相同，但同主题应当不同）
        assert p1 != p2
        for p in (p1, p2):
            assert "本轮为第" in p
            assert "叙事视角 / 体裁 / 切入角度采用" in p


# ---------------------------------------------------------------------------
# 阅读理解
# ---------------------------------------------------------------------------
class TestBuildReadingPrompt:
    def test_单篇限制(self):
        for level in R_LEVELS:
            p = esp.build_reading_prompt(level, "历史")
            assert "共 1 篇短文" in p
            # 不再要求用 Passage 1 / Passage 2 作为分隔（示例说明里允许出现“Passage 序号”字样）
            assert "Passage 1" not in p
            assert "Passage 2" not in p

    def test_题量优先使用question_count(self):
        p = esp.build_reading_prompt("考研", "经济", "短篇", question_count=8)
        assert "共 8 道题" in p

    def test_题量缺省使用大纲每篇题量(self):
        for level in R_LEVELS:
            per = esp.READING_SPECS[level]["per_passage"]
            p = esp.build_reading_prompt(level, "社会", question_count=0)
            assert f"共 {per} 道题" in p

    def test_短篇取词数下限(self):
        level = "考研"
        wc_min, wc_max = esp.READING_SPECS[level]["words_each"]
        p = esp.build_reading_prompt(level, "人工智能", "短篇")
        assert f"约 {wc_min}-{(wc_min + wc_max) // 2} 词" in p

    def test_长篇取词数上半区(self):
        level = "考研"
        wc_min, wc_max = esp.READING_SPECS[level]["words_each"]
        lo = (wc_min + wc_max) // 2
        p = esp.build_reading_prompt(level, "人工智能", "长篇")
        assert f"约 {lo}-{wc_max} 词" in p

    def test_题型从池中随机且合法(self):
        for level in R_LEVELS:
            spec = esp.READING_SPECS[level]
            per = spec["per_passage"]
            p = esp.build_reading_prompt(level, "文化", question_count=per)
            # 题型说明必须包含 per 行「第 N 题题型：xxx」
            lines = [ln for ln in p.splitlines() if "题题型：" in ln]
            assert len(lines) == per
            # 每行题型必须属于该阶段题型池
            for ln in lines:
                cat = ln.split("题题型：")[1].split(" ")[0]
                assert cat in spec["categories"]

    def test_题型随机产生多样性(self):
        # 多次生成，题型组合应当出现至少两种不同的排列
        seen = set()
        for _ in range(40):
            p = esp.build_reading_prompt("考研", "哲学", question_count=5)
            seq = tuple(
                ln.split("题题型：")[1].split(" ")[0]
                for ln in p.splitlines() if "题题型：" in ln
            )
            seen.add(seq)
        assert len(seen) >= 2  # 随机抽题生效

    def test_avoid_title注入(self):
        p = esp.build_reading_prompt("高中", "自然", avoid_title="旧文章标题")
        assert "旧文章标题" in p

    def test_未知阶段回退(self):
        p = esp.build_reading_prompt("未知", "x")
        assert "高中" in p


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------
class TestHelpers:
    def test_pick_variation返回种子与角度(self):
        seed, angle = esp._pick_variation()
        assert isinstance(seed, int) and 1 <= seed <= 99999
        assert angle in esp.VARIATION_ANGLES

    def test_fmt_points循环铺满(self):
        pts = ["A", "B"]
        out = esp._fmt_points(pts, 5)
        assert "第 1 空重点考查：A" in out
        assert "第 5 空重点考查" in out
        assert out.count("重点考查") == 5

    def test_gen_temperature常量(self):
        assert esp.GEN_TEMPERATURE == 0.85
