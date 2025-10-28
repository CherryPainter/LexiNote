## 🧩 Patch Spec: 今日学习进度检测与听写提醒逻辑

### 📁 适用模块

- **模块名称**：听写练习模块
- **关联模块**：单词学习模块

------

### 🔍 背景说明

当前听写逻辑允许用户选择“根据今日学习进度听写”，
 但系统尚未验证用户是否已完成当天学习任务。
 此补丁旨在**增加状态检测与提醒逻辑**，
 以确保用户不会在学习任务未完成的情况下进行听写。

------

### 🎯 功能目标

当用户选择【根据今日学习进度听写】时，
 系统首先检查单词学习模块中的「今日学习完成状态」。

- 若未完成 → 弹出提示框，提醒用户尚未完成学习
- 若已完成 → 正常进入听写流程

------

### 🧠 逻辑流程（伪代码）

```python
def start_dictation(mode):
    if mode == "today_learning":
        if not check_today_progress_completed():
            show_message(
                "您今天还没有完成单词学习哦~ 请先完成今日学习进度再进行听写练习！"
            )
            return
        else:
            start_dictation_session("today_words")
    elif mode == "random":
        start_dictation_session("random_words")
```

------

### 🧩 状态检测逻辑

```python
def check_today_progress_completed():
    """
    检查单词学习模块是否标记为完成状态
    来源：学习模块的每日任务表
    返回：True / False
    """
    record = db.query("SELECT completed FROM daily_learning WHERE date = today()")
    if record and record["completed"] == True:
        return True
    return False
```

------

### 💾 数据依赖

| 表名             | 字段            | 类型    | 描述             |
| ---------------- | --------------- | ------- | ---------------- |
| `daily_learning` | `date`          | DATE    | 学习日期         |
|                  | `completed`     | BOOLEAN | 是否完成当天学习 |
|                  | `words_learned` | INTEGER | 已学习单词数     |
|                  | `total_words`   | INTEGER | 今日目标单词总数 |

> 当 `words_learned >= total_words` 时，系统在学习模块自动更新 `completed = True`。

------

### 🪄 用户交互逻辑

| 状态   | 提示内容                                     | 操作选项              |
| ------ | -------------------------------------------- | --------------------- |
| 未完成 | “您今天还没完成学习进度，是否前往学习页面？” | 【去学习】 / 【取消】 |
| 已完成 | “今日进度已完成，开始听写吧！”               | 【开始听写】          |

------

### ⚙️ 系统集成点

- **调用位置**：听写页面初始化或模式选择确认时

------

### 🔮 AI可选扩展（可由Trea实现）

- 若用户反复未完成学习进度，AI可以提醒其制定更小的学习目标。
- 若学习进度完成但听写结果差，AI自动生成「重点复习列表」。

------

