## 🧩 LexiNote 新功能扩展设计书（Expansion Spec v1.0）

### 🏷 模块名称

1. **完形填空（Cloze Test Module）**
2. **阅读理解（Reading Comprehension Module）**

------

## 🎯 功能总目标

为 LexiNote 增加 “英语理解类练习” 模块。
 实现 AI 与用户双协同学习机制：

- ✅ 在线状态：AI 实时生成题目 + 判题 + 给解析
- ✅ 离线状态：从本地数据库中加载题目、答案与解析
- ✅ 支持用户选择题库来源（在线 / 离线 / 混合模式）

------

## 🧠 核心功能逻辑

### 1️⃣ 完形填空模块（Cloze Test Module）

**主要功能：**

- 生成完形填空（文章 + 空格题 + 选项 + 答案 + 解析）
- 存储到数据库（支持离线使用）
- 用户作答后，自动判定正确与否

**工作流：**

```text
选择模式 → （在线 / 离线）
 ├─ 在线：调用AI生成题目
 │   ├─ 保存到数据库 (题目, 答案, 解析)
 │   └─ 展示题目 → 用户作答 → AI判题+解析展示
 │
 └─ 离线：从数据库中加载
     ├─ 题目展示 → 用户作答
     └─ 离线比对答案 → 展示公共解析
```

------

### 2️⃣ 阅读理解模块（Reading Comprehension Module）

**主要功能：**

- 生成阅读理解题（长篇/短篇可选）
- 包括多选题、主观题两种形式
- 支持AI判分和离线对比

**在线逻辑：**

```python
if ai_service_available:
    question, answer, explanation = AI.generate_reading(level, length)
    db.save(question, answer, explanation)
    show(question)
    user_answer = get_user_input()
    result = AI.evaluate(user_answer, answer)
    show_result(result, explanation)
```

**离线逻辑：**

```python
question, answer, explanation = db.random("reading")
show(question)
user_answer = get_user_input()
result = (user_answer == answer)
show_result(result, explanation)
```

------

## 💾 数据库存储结构

| 表名          | 字段名         | 类型    | 描述                      |
| ------------- | -------------- | ------- | ------------------------- |
| `cloze_tests` | `id`           | INTEGER | 主键                      |
|               | `title`        | TEXT    | 题目标题                  |
|               | `content`      | TEXT    | 完形填空原文              |
|               | `options`      | JSON    | 选项                      |
|               | `answer`       | TEXT    | 正确答案                  |
|               | `explanation`  | TEXT    | 题目解析                  |
|               | `source`       | TEXT    | 来源（AI生成 / 离线导入） |
|               | `date_created` | DATE    | 创建时间                  |

| 表名                     | 字段名         | 类型    | 描述                      |
| ------------------------ | -------------- | ------- | ------------------------- |
| `reading_comprehensions` | `id`           | INTEGER | 主键                      |
|                          | `article`      | TEXT    | 阅读原文                  |
|                          | `questions`    | JSON    | 题目列表                  |
|                          | `answers`      | JSON    | 答案列表                  |
|                          | `explanations` | JSON    | 解析列表                  |
|                          | `source`       | TEXT    | 来源（AI生成 / 离线导入） |
|                          | `date_created` | DATE    | 创建时间                  |

------

## 🔄 在线/离线模式切换算法

```python
def get_mode():
    return "online" if ai_connection_alive() else "offline"

def ai_connection_alive():
    try:
        ping_ollama()
        return True
    except:
        return False
```

| 模式 | 数据来源   | 判题方式     | 解析方式         |
| ---- | ---------- | ------------ | ---------------- |
| 在线 | AI生成     | AI分析判断   | AI生成个性化解析 |
| 离线 | 本地数据库 | 直接比对答案 | 展示公共解析     |

------

## 🔍 用户交互逻辑

1. 用户选择模块（完形 / 阅读）
2. 选择模式（在线 / 离线）
3. 若离线数据库为空 → 提示“暂无题目，请先联网生成内容”
4. 若在线 → 自动保存生成题目到数据库
5. 完成题后 → 展示对错与解析
6. 用户可选择「加入错题本」

------

## 🪄 可拓展点（AI辅助逻辑）

- AI可根据用户最近错误频率调整题目难度。
- 用户可通过门户（Portal）管理离线题库：查看、删除、重做、收藏。
- 离线题目支持导出为 JSON / CSV。

------

## 🔐 文件结构建议

```
LexiNote/
├─ modules/
│   ├─ cloze_test.py
│   ├─ reading_comprehension.py
│   ├─ database.py
│   ├─ ai_service.py
│   └─ portal_manager.py
├─ data/
│   ├─ cloze_tests.db
│   ├─ reading_comprehensions.db
│   └─ config.json
├─ main.py
└─ settings.py
```

------

## 🧩 推荐使用的技术栈

| 功能         | 推荐库                            |
| ------------ | --------------------------------- |
| 数据库       | `sqlite3`（轻量本地数据库）       |
| JSON数据处理 | `json`                            |
| 界面（可选） | `tkinter` / `PyQt5`               |
| AI连接       | `ollama` 接口（或本地LLM服务）    |
| 缓存策略     | `functools.lru_cache` 或 文件缓存 |

