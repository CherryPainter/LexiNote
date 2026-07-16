"""各阶段英语考试真实题型规格（命题蓝图）。

数据依据公开考试大纲整理：
- 专升本：参考安徽/天津/贵州/浙江等省统考《英语》大纲（完形 10~15 空、阅读 3~4 篇四选一）。
- 考研（英语一）：参考教育部考研英语一大纲（完形 20 空、传统阅读 Part A 4 篇×5 题）。
- 高中/初中：参考普通高考与中考英语题型（完形、阅读均为四选一）。
- 大学：参照 CET-4/6 仔细阅读难度。

本模块的目标：让 AI 生成的题目“长得像”真实考卷，而不是泛泛而谈的练习，
同时每次生成都注入随机角度与种子，保证同一主题不会两次生成雷同内容。
"""

import random
from typing import Any

# ---------------------------------------------------------------------------
# 完形填空规格：每个阶段真实的题量、词数、分值与考点分布
# ---------------------------------------------------------------------------
CLOZE_SPECS: dict[str, Any] = {
    "初中": {
        "word_count": (180, 220),
        "blanks": 10,
        "options": 4,
        "scoring": "每空 1 分，共 10 分（四选一）",
        "points": [
            "动词时态与语态",
            "名词词义辨析",
            "形容词/副词辨析",
            "介词基本搭配",
            "固定短语搭配",
            "上下文逻辑衔接",
        ],
    },
    "高中": {
        "word_count": (220, 300),
        "blanks": 20,
        "options": 4,
        "scoring": "每空 1.5 分，共 30 分（四选一）",
        "points": [
            "动词（时态/非谓语/虚拟语气）",
            "名词辨析",
            "形容词/副词辨析",
            "连词与逻辑关系",
            "介词搭配",
            "固定搭配",
            "代词与冠词",
        ],
    },
    "大学": {
        "word_count": (200, 260),
        "blanks": 15,
        "options": 4,
        "scoring": "四选一完形，参照 CET-4/6 难度",
        "points": [
            "词汇辨析",
            "固定搭配",
            "语法结构",
            "逻辑衔接",
            "上下文推断",
        ],
    },
    "专升本": {
        "word_count": (150, 250),
        "blanks": 10,
        "options": 4,
        "scoring": "10 题，每题 2 分，共 20 分（四选一）",
        "points": [
            "词汇辨析",
            "固定搭配",
            "语法",
            "上下文理解",
            "逻辑关系",
        ],
    },
    "考研": {
        "word_count": (240, 320),
        "blanks": 20,
        "options": 4,
        "scoring": "20 题，每题 0.5 分，共 10 分（四选一）",
        "points": [
            "实词辨析（动/名/形/副，含熟词僻义）",
            "固定搭配",
            "逻辑连接（转折/因果/并列/递进）",
            "上下文复现",
            "语法结构",
        ],
    },
}

# ---------------------------------------------------------------------------
# 阅读理解规格：每个阶段真实的篇数、单篇词数、每篇题量与题型分布
# ---------------------------------------------------------------------------
READING_SPECS: dict[str, Any] = {
    "初中": {
        "passages": 2,
        "words_each": (180, 240),
        "per_passage": 4,
        "scoring": "每题 2 分（四选一）",
        "categories": ["细节理解", "主旨大意", "词义猜测", "推理判断"],
    },
    "高中": {
        "passages": 3,
        "words_each": (260, 340),
        "per_passage": 5,
        "scoring": "每题 2 分（四选一）",
        "categories": ["细节理解", "主旨大意", "推理判断", "词义猜测", "观点态度"],
    },
    "大学": {
        "passages": 3,
        "words_each": (300, 400),
        "per_passage": 5,
        "scoring": "每题 2 分（四选一，参照 CET 仔细阅读）",
        "categories": ["细节理解", "主旨大意", "推理判断", "词义猜测", "观点态度"],
    },
    "专升本": {
        "passages": 3,
        "words_each": (250, 320),
        "per_passage": 5,
        "scoring": "每题 2 分（四选一），阅读理解共约 40 分",
        "categories": ["信息提取", "细节理解", "主旨大意", "推理判断", "词义猜测"],
    },
    "考研": {
        "passages": 4,
        "words_each": (380, 480),
        "per_passage": 5,
        "scoring": "每题 2 分（四选一），传统阅读 Part A 共 40 分",
        "categories": ["细节题", "主旨题", "态度题", "推理题", "词义题"],
    },
}

# ---------------------------------------------------------------------------
# 阅读题型定义：明确每类题“考什么、怎么问”，让 AI 不至于自由发挥
# ---------------------------------------------------------------------------
QUESTION_CATEGORY_DEFS = {
    "细节理解": "考查文章具体事实、数据、事件；答案可在原文直接定位（同义替换）。",
    "细节题": "考查文章具体事实、数据、事件；答案可在原文直接定位（同义替换）。",
    "主旨大意": "考查全文或段落中心思想；问法如 main idea / best title / purpose。",
    "主旨题": "考查全文或段落中心思想；问法如 main idea / best title / purpose。",
    "推理判断": "考查言外之意、作者暗示；答案须基于文本合理推断，不能直接抄原文。",
    "推理题": "考查言外之意、作者暗示；答案须基于文本合理推断，不能直接抄原文。",
    "词义猜测": "考查语境猜词；据上下文并列/转折/举例推测生词或短语含义。",
    "词义题": "考查语境猜词；据上下文并列/转折/举例推测生词或短语含义。",
    "观点态度": "考查作者/人物态度倾向（positive/negative/neutral/objective）。",
    "态度题": "考查作者/人物态度倾向（positive/negative/neutral/objective）。",
    "信息提取": "考查从说明文/新闻中快速定位关键信息。",
}

# ---------------------------------------------------------------------------
# 多样性角度池：每次生成随机抽取一个，保证同主题不会两次雷同
# ---------------------------------------------------------------------------
VARIATION_ANGLES = [
    "采用第一人称叙事视角",
    "采用第三人称全知视角",
    "以新闻报道/特稿风格撰写",
    "以科普说明文风格撰写",
    "以议论文/评论风格撰写",
    "以故事化记叙文风格撰写",
    "围绕因果关系展开",
    "围绕对比对照展开",
    "围绕问题解决展开",
    "围绕时间顺序展开",
    "设定在大学校园场景",
    "设定在职场/公司场景",
    "设定在日常生活场景",
    "设定在科学研究/发现场景",
    "设定在社会现象/公共议题场景",
]

# 生成类调用使用的采样温度（高于默认，鼓励多样性；解析/翻译类不传此值）
GEN_TEMPERATURE = 0.85

# JSON 输出示例模板（非 f-string，使用 {n} 占位符，由构造器替换）
_CLOZE_JSON_EXAMPLE = """{
  "title": "简洁标题（概括文章主题）",
  "content": "含 [BLANK_1]…[BLANK_{n}] 的完整文章",
  "options": [
    {"blank": 1, "text": "optA;optB;optC;optD"},
    {"blank": 2, "text": "optA;optB;optC;optD"}
  ],
  "answers": "正确选项序号，逗号分隔，如 1,3,2,4,...（共 {n} 个）",
  "explanation": "逐空解析（英文）：说明正确项依据及每个干扰项的排除理由"
}"""

_READING_JSON_EXAMPLE = """{
  "article": "完整阅读文章（多段，单篇；直接撰写正文，无需 Passage 序号）",
  "questions": [
    "完整题目1（选择题须含 A.… B.… C.… D.…）",
    "完整题目2（选择题须含 A.… B.… C.… D.…）"
  ],
  "answers": ["A", "C"],
  "explanations": ["逐题解析（英文）：指出答案在文中的依据与各干扰项排除理由"]
}"""


def _pick_variation():
    """返回 (随机种子, 随机角度)，用于驱动本次生成的独特性。"""
    return random.randint(1, 99999), random.choice(VARIATION_ANGLES)


def _fmt_points(points: list, n: int) -> str:
    """将考点循环铺满 n 个空，逐空列出重点考查点。"""
    chosen = (points * ((n // len(points)) + 1))[:n]
    return "\n".join(f"  - 第 {i + 1} 空重点考查：{p}" for i, p in enumerate(chosen))


def _fmt_categories(categories: list, total: int):
    """为 total 道题随机分配题型（允许重复），保证每次生成的题型组合不雷同。"""
    chosen = [random.choice(categories) for _ in range(total)]
    lines = [
        f"  - 第 {i + 1} 题题型：{c} —— {QUESTION_CATEGORY_DEFS.get(c, '')}"
        for i, c in enumerate(chosen)
    ]
    return "\n".join(lines), chosen


def build_cloze_prompt(level: str, topic: str, avoid_title: str = None) -> str:
    """构造符合真实题型的完形填空命题提示词（含本次生成独特性要求）。"""
    spec = CLOZE_SPECS.get(level, CLOZE_SPECS["高中"])
    level_name = level if level in CLOZE_SPECS else "高中"
    wc_min, wc_max = spec["word_count"]
    blanks = spec["blanks"]
    seed, angle = _pick_variation()
    points_block = _fmt_points(spec["points"], blanks)
    json_example = _CLOZE_JSON_EXAMPLE.replace("{n}", str(blanks))
    avoid_line = (
        f"\n- 不得与已有题目雷同，尤其避免复用以下标题的场景：「{avoid_title}」"
        if avoid_title else ""
    )

    prompt = f"""你是一位严格按照中国英语考试大纲命题的资深命题专家。请生成一篇符合【{level_name}】英语考试真实题型的完形填空。

【考试规格】
- 文章体裁：记叙文 / 说明文 / 议论文 任选其一，须贴合主题「{topic}」
- 文章长度：约 {wc_min}-{wc_max} 词
- 挖空数量：{blanks} 个，标记为 [BLANK_1]…[BLANK_{blanks}]；首句与末句不挖空
- 每个空格提供 {spec['options']} 个选项（A/B/C/D 形式：optA;optB;optC;optD），仅一个正确
- 分值说明：{spec['scoring']}

【考点分布要求】（在 {blanks} 个空中合理分配，避免连续两空考查同类点）
{points_block}

【干扰项质量要求】
每个干扰项必须与正确项属于同一词性 / 同一语义场，构成有效干扰（如近义词辨析、固定搭配误用、逻辑连接词混淆）；禁止使用明显荒谬或毫不相关的干扰项。

【本次生成独特性要求】（关键）
本轮为第 {seed} 次生成，请务必产出与以往完全不同的全新文章：
- 叙事视角 / 体裁 / 切入角度采用：{angle}
- 不得复用任何教材、真题或先前生成的场景、事例、句子{avoid_line}
- 主题「{topic}」仅作为题材方向，具体情节须原创、自洽

【输出格式】
严格仅输出如下 JSON（不要任何额外说明、不要 Markdown 代码块）：
{json_example}"""
    return prompt


def build_reading_prompt(level: str, topic: str, length: str = "短篇",
                         question_count: int = 5, avoid_title: str = None) -> str:
    """构造符合真实题型的阅读理解命题提示词（含本次生成独特性要求）。"""
    spec = READING_SPECS.get(level, READING_SPECS["高中"])
    level_name = level if level in READING_SPECS else "高中"
    wc_min, wc_max = spec["words_each"]
    if length == "长篇":
        lo, hi = (wc_min + wc_max) // 2, wc_max
    else:
        lo, hi = wc_min, (wc_min + wc_max) // 2
    passages = 1  # 每次仅生成 1 篇短文

    # 题量：用户指定的 question_count 优先；否则用大纲默认（每篇题量）
    total = question_count if question_count else spec["per_passage"]

    cat_block, _ = _fmt_categories(spec["categories"], total)
    seed, angle = _pick_variation()
    avoid_line = (
        f"\n- 不得与已有题目雷同，尤其避免复用以下标题/主题的场景：「{avoid_title}」"
        if avoid_title else ""
    )

    prompt = f"""你是一位严格按照中国英语考试大纲命题的资深命题专家。请生成一篇符合【{level_name}】英语考试真实阅读题型的材料。

【考试规格】
- 共 1 篇短文（题材在 记叙文 / 议论文 / 说明文 / 应用文 间自选），约 {lo}-{hi} 词
- 全部为四选一选择题（A/B/C/D），仅一个正确；共 {total} 道题
- 分值说明：{spec['scoring']}

【题型分布要求】（每题题型从下列真实阅读题型中随机选取，不要求单次全覆盖）
{cat_block}

【命题质量要求】
- 每题答案必须在原文中有明确依据：细节/主旨可直接定位；推理/态度须基于文本合理推断，不得主观臆断
- 正确项通常为原文同义替换；干扰项须属于以下一类：偷换概念 / 以偏概全 / 正反混淆 / 无中生有 / 答非所问
- 严禁使用「Question X」之类占位符，每题必须是完整、具体的提问

【本次生成独特性要求】
本轮为第 {seed} 次生成，请产出与以往完全不同的全新材料：
- 文章主题围绕「{topic}」，但须采用全新素材与角度：{angle}{avoid_line}
- 不得复用真题、教材或先前生成的内容

【输出格式】
严格仅输出如下 JSON（不要任何额外说明、不要 Markdown 代码块）：
{_READING_JSON_EXAMPLE}"""
    return prompt
