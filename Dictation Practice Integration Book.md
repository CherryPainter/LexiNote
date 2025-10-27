# Dictation Practice Integration Book

------

## 📘 文件名建议

```
AI_Dictation_Integration_Book.md
```

------

```markdown
# Dictation Practice Integration Book for LexiNote

## 1. 模块目标
本模块负责用户在完成单词学习后的 **听写练习与熟词复习功能**。  
实现目标：
- ✅ 支持两种听写来源：**词库随机听写** 与 **当日学习单词听写**；
- ✅ 听写模式分为 **单个听写** 与 **队列听写**；
- ✅ 听写结束后自动总结与纠错；
- ✅ 熟词自动进入复习筛选系统；
- ✅ 队列听写有时间限制与数量可调；
- ✅ 支持过滤复习熟词。

---

## 2. 模块结构
```

core/
 ├─ dictation.py          # 听写主逻辑
 ├─ data_manager.py       # 数据读写接口
 ├─ ai_interface.py       # AI拼写评估与反馈
 ├─ settings.json         # 用户自定义参数
 ├─ word_progress.json    # 学习进度数据
 ├─ familiar_words.json   # 熟词数据

```
---

## 3. 听写模式定义

### 3.1 单个听写模式（Single Mode）
- 用户选择一个单词（或系统随机抽取）；
- 系统播放发音；
- 用户输入拼写；
- 系统评估正确性并反馈。

**逻辑：**
```python
selected_word = dictation_manager.select_word(source="today" or "library")
audio.play(selected_word)
user_input = ui.get_text_input()
result = ai_manager.evaluate(selected_word, user_input)
ui.show_feedback(result)
```

**AI评估调用：**

```python
AIManager.evaluate(expected, user_input)
→ 返回 {"accuracy": 0.92, "feedback": "拼写正确率高，缺少字母 e"}
```

------

### 3.2 队列听写模式（Queue Mode）

- 从特定来源（今日单词 / 熟词库 / 全词库）中抽取若干单词；
- 按顺序逐个播放发音；
- 每个单词有拼写时限（默认 60 秒，可在 `settings.json` 中调整）；
- 用户完成全部听写后生成总结报告。

**设置示例：**

```json
{
  "dictation_time_limit": 60,
  "dictation_batch_size": 10
}
```

**逻辑：**

```python
queue = dictation_manager.build_queue(source="today", limit=10)
for word in queue:
    start_timer(60)
    play_audio(word)
    user_input = get_input()
    result = ai_manager.evaluate(word, user_input)
    dictation_manager.record_result(word, result)

summary = dictation_manager.summarize(queue)
ui.show_summary(summary)
```

------

## 4. 数据结构

### 4.1 用户学习进度（`word_progress.json`）

```json
{
  "apple": {"learned": true, "weight": 0.8, "last_practice": "2025-10-27"},
  "banana": {"learned": false, "weight": 1.5, "last_practice": null}
}
```

### 4.2 熟词库（`familiar_words.json`）

```json
{
  "apple": {"mastered": true, "practice_count": 5},
  "book": {"mastered": true, "practice_count": 3}
}
```

### 4.3 听写记录（`dictation_history.json`）

```json
{
  "2025-10-27": {
    "mode": "queue_today",
    "words": [
      {"word": "apple", "result": "correct"},
      {"word": "banana", "result": "misspelled"}
    ]
  }
}
```

------

## 5. 逻辑算法定义

### 5.1 听写抽取算法

根据模式自动筛选：

```python
def select_words(source, limit):
    if source == "today":
        return [w for w in today_words if w.learned and w.weight > 0.6][:limit]
    elif source == "familiar":
        return random.sample(familiar_words, limit)
    elif source == "library":
        return weighted_random_select(word_dict, weight="word_progress.weight", k=limit)
```

**说明：**

- 今日单词：从当天学习过的单词中抽取；
- 熟词听写：从 `familiar_words.json` 中抽取；
- 全词库随机：按权重随机抽取，重点偏向高权重（未掌握）单词。

------

### 5.2 复习过滤算法

复习模式下：

```python
def filter_familiar(words):
    return [w for w in words if w in familiar_words]
```

用户可选：

- “只复习熟词”
- “复习所有错词”
- “混合模式”

------

### 5.3 队列总结算法

生成总结报告：

```python
def summarize(queue):
    total = len(queue)
    correct = sum(1 for q in queue if q["result"] == "correct")
    accuracy = correct / total
    missed = [q["word"] for q in queue if q["result"] != "correct"]
    return {
        "total": total,
        "accuracy": round(accuracy, 2),
        "missed": missed,
        "suggestion": ai_manager.advise({
            "total_words": total,
            "mastered": correct,
            "review_needed": len(missed),
            "average_score": accuracy
        })
    }
```

------

## 6. 用户设置（`settings.json`）

```json
{
  "dictation_time_limit": 60,
  "dictation_batch_size": 10,
  "dictation_source": "today",
  "review_filter": "familiar_only"
}
```

------

## 7. 与其它模块交互

| 模块              | 交互说明                                               |
| ----------------- | ------------------------------------------------------ |
| `learning.py`     | 完成学习后更新 `word_progress.json`，标记 learned=true |
| `dictation.py`    | 读取 `word_progress.json` 生成听写队列                 |
| `ai_interface.py` | 负责听写评估与反馈                                     |
| `data_manager.py` | 保存听写结果、更新熟词记录                             |
| `review.py`       | 根据熟词或错词筛选复习队列                             |

------

## 8. UI交互建议（Tkinter）

### 模式选择页

```
[ 听写模式选择 ]
  ( ) 单个听写
  ( ) 队列听写
  来源：
    [今日学习单词]
    [熟词库]
    [全词库随机]
  [ 开始听写 ]
```

### 队列听写界面

```
┌───────────────────────────┐
│ 队列听写（3/10）               │
│───────────────────────────│
│ 🔊 发音中：_ _ _ _ _          │
│ 拼写输入： [          ]       │
│ ⏱ 剩余时间：42s              │
│───────────────────────────│
│   [ 提交 ]    [ 跳过 ]        │
└───────────────────────────┘
```

### 听写总结页

```
听写完成！
正确率：86%
错词：banana, orange
AI建议：集中复习含 b 音开头的单词。
[ 返回主页 ] [ 复习错词 ]
```

------

## 9. AI调用规范

1. 所有 AI 调用通过 `AIManager`；
2. 禁止在 `dictation.py` 直接使用 `ollama`；
3. 所有听写结果必须存入 `dictation_history.json`；
4. AI 反馈文本中禁止 Markdown；
5. 错误日志保存到 `logs/ai_dictation.log`。

------

## 10. 扩展规划

- 加入语音识别（用户语音拼写）
- 允许 AI 根据用户熟练度动态推荐听写数量
- 通过 AI 生成个性化错词强化练习
- 图形化统计每日听写成绩曲线

------

## ✅ 结语

此文档为 LexiNote 听写练习模块的 AI 设计规范。
 其核心目标是建立一个具备自适应记忆与纠错机制的智能语言训练系统。
 AI（如 trea）在读取本文件后，应能：

- 理解听写的全逻辑；
- 知道如何获取数据；
- 明确调用接口与更新文件；
- 自动生成听写与复习逻辑代码。