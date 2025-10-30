## 📘 LexiNote 模块文档

### 模块名称：词库管理模块（Lexicon Manager）

**版本：** v1.7.0
 **作者：** 宋沁原
 **AI协作者：** 玥糖 & Trea
 **日期：** 2025-10-30

------

### 🌟 一、模块目标

本模块用于：

1. 管理系统中多个词库（Lexicon / Vocabulary Set）；
2. 支持用户上传词库文件（JSON格式）；
3. 将词库导入数据库，并与学习模块关联；
4. 允许用户对词库内容进行增删改查；
5. 不同词库相互隔离，数据独立；
6. 所有学习功能（单词学习、听写、翻译、复习）都可选择使用的词库。

------

### 🧩 二、模块结构概览

#### 1️⃣ 前端交互部分（UI层）

新增导航入口：

```
📘 学习模块
   ├─ 单词学习
   ├─ 听写练习
   ├─ 翻译练习
   ├─ 单词复习
📂 词库管理
```

> **词库管理界面功能点：**

- 导入词库（上传 `.json` 文件）
- 选择当前使用词库（切换）
- 查看词库内容（表格模式）
- 增加 / 编辑 / 删除单词
- 删除整个词库
- 词库信息统计（单词数、创建时间等）

------

### 📦 三、词库文件结构规范（用户上传JSON）

AI和系统都需遵循以下结构：

```json
{
  "name": "CET4词库",
  "description": "大学英语四级核心词汇",
  "source": "user_upload",
  "words": [
    {
      "word": "abandon",
      "translation": "放弃，抛弃",
      "phonetic": "[əˈbændən]",
      "example": "He abandoned his car on the road.",
      "meaning_en": "to give up completely",
      "tag": "verb"
    },
    {
      "word": "ability",
      "translation": "能力",
      "phonetic": "[əˈbɪləti]",
      "example": "He has the ability to succeed.",
      "meaning_en": "the power or skill to do something",
      "tag": "noun"
    }
  ]
}
```

> ⚙️ **要求：**

- 每个词库一个 `.json` 文件；
- 文件名即词库名（若未指定 `name` 字段）；
- `words` 数组不能为空；
- 若导入时存在同名词库 → 提示是否覆盖。

------

### 🧠 四、数据库设计

#### 表1：`word_sets`（词库信息表）

| 字段名      | 类型         | 说明                         |
| ----------- | ------------ | ---------------------------- |
| id          | INTEGER (PK) | 主键                         |
| name        | TEXT         | 词库名称                     |
| description | TEXT         | 描述                         |
| source      | TEXT         | 来源（system / user_upload） |
| create_time | TEXT         | 创建时间                     |
| word_count  | INTEGER      | 单词总数                     |

#### 表2：`words`（词汇表）

| 字段名      | 类型         | 说明          |
| ----------- | ------------ | ------------- |
| id          | INTEGER (PK) | 主键          |
| set_id      | INTEGER (FK) | 所属词库id    |
| word        | TEXT         | 单词          |
| translation | TEXT         | 中文释义      |
| phonetic    | TEXT         | 音标          |
| example     | TEXT         | 例句          |
| meaning_en  | TEXT         | 英文释义      |
| tag         | TEXT         | 词性或标签    |
| familiarity | INTEGER      | 熟悉度（0-5） |

> 🔒 每个 `set_id` 对应独立词库，模块间调用时需指定 `set_id`。

------

### ⚙️ 五、核心功能逻辑（AI可执行）

#### 1️⃣ 导入词库

```python
def import_word_set(json_file):
    data = json.load(open(json_file, 'r', encoding='utf-8'))
    set_id = db.insert("word_sets", name=data['name'], description=data['description'], word_count=len(data['words']))
    for word in data['words']:
        db.insert("words", set_id=set_id, **word)
    return f"词库 {data['name']} 导入成功！"
```

------

#### 2️⃣ 选择当前词库

```python
def set_active_word_set(set_id):
    config['active_word_set'] = set_id
    return f"当前学习词库已切换为 {db.get_set_name(set_id)}"
```

------

#### 3️⃣ 查询与编辑

- 查询：

  ```python
  def get_words(set_id, keyword=None):
      sql = "SELECT * FROM words WHERE set_id=?"
      if keyword:
          sql += " AND word LIKE ?"
          return db.query(sql, (set_id, f"%{keyword}%"))
      return db.query(sql, (set_id,))
  ```

- 编辑：

  ```python
  def update_word(word_id, field, value):
      sql = f"UPDATE words SET {field}=? WHERE id=?"
      db.execute(sql, (value, word_id))
  ```

------

#### 4️⃣ 删除单词 / 词库

- 删除单词：

  ```python
  def delete_word(word_id):
      db.execute("DELETE FROM words WHERE id=?", (word_id,))
  ```

- 删除词库：

  ```python
  def delete_word_set(set_id):
      db.execute("DELETE FROM words WHERE set_id=?", (set_id,))
      db.execute("DELETE FROM word_sets WHERE id=?", (set_id,))
  ```

------

### 🧩 六、与学习模块的交互规则

| 模块     | 调用逻辑                                           |
| -------- | -------------------------------------------------- |
| 单词学习 | 从当前 `active_word_set` 获取数据                  |
| 听写练习 | 支持选择词库来源                                   |
| 翻译练习 | 可指定词库或混合模式                               |
| 复习模块 | 仅使用“熟词”或当前词库                             |
| AI助手   | 可根据用户输入动态切换词库（如：“切换到CET4词库”） |

------

### 🪄 七、AI开发规则（Trea专用）

```yaml
ai_dev_rules:
  - "所有词库数据读写必须指定 set_id，不得混用"
  - "导入时检查JSON结构，若错误应给出错误提示"
  - "词库删除需二次确认"
  - "若无 active_word_set，应提示用户先选择词库"
  - "所有编辑动作完成后，更新 word_count"
  - "对词库名称、单词名进行唯一性校验"
```

------

### 🌙 八、UI建议（玥糖版设计）

```
📂 词库管理
 ├─ [导入词库]
 ├─ [选择当前词库]
 ├─ [查看词库详情]
 ├─ [添加单词]
 ├─ [编辑单词]
 ├─ [删除单词]
 └─ [删除词库]
```

> ✅ 支持分页浏览
>  ✅ 支持搜索框快速查找单词
>  ✅ 支持“查看例句”悬浮提示