# 开发者文档

## 1. 项目说明

LexiNote 是一个个人英语学习工具，帮助用户管理单词表、学习单词和跟踪学习进度。

## 2. 版本历史

请查看 [CHANGELOG.md](./CHANGELOG.md) 获取完整的版本更新记录。

## 3. 项目结构

```
├── .flake8
├── .gitignore
├── API_DOCUMENTATION.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── DEVELOPER_DOCS.md
├── README.md
├── RELEASE_NOTES.md
├── SETTINGS.md
├── TESTS.md
├── app.ico
├── audio_cache.py
├── audio_player.py
├── core\
│   ├── ai_interface.py
│   ├── cache_manager.py
│   ├── database_manager.py
│   ├── dictation.py
│   ├── learning.py
│   ├── settings_manager.py
│   └── text_formatter.py
├── logger.py
├── main.py
├── modules\
│   ├── ai_service.py
│   ├── cloze_test.py
│   ├── database.py
│   ├── portal_manager.py
│   ├── reading_comprehension.py
│   ├── utils.py
│   └── word_importer.py
├── requirements.txt
├── statistics.py
├── ui\
│   ├── ai_assistant_page.py
│   ├── cloze_test_page.py
│   ├── components\
│   │   ├── loading_dialog.py
│   │   ├── scrollable_frame.py
│   │   └── translation_editor.py
│   ├── dictation_page.py
│   ├── learning_page.py
│   ├── main_window.py
│   ├── reading_comprehension_page.py
│   ├── review_page.py
│   ├── settings_page.py
│   ├── statistics_page.py
│   ├── translation_page.py
│   └── word_set_page.py
└── word_manager.py
```

## 4. 核心模块说明

### 4.1 单词管理模块 (word_manager.py)

单词管理是系统的核心功能，负责单词的增删改查、分类、学习状态管理等。

#### 主要功能

- 单词的添加、删除、更新和查询
- 单词分类管理
- 学习状态跟踪（掌握、需要复习、未学习）
- 随机单词选择
- 单词统计信息

#### 核心 API

```python
# 初始化
word_manager = WordManager()

# 单词操作
word_manager.add_word(word, definition, example, category)
word_manager.update_word(word_id, definition, example, category)
word_manager.delete_word(word_id)
word_manager.get_word(word_id)

# 批量操作
word_manager.get_random_words(batch_size=10)
word_manager.get_words_by_category(category)
word_manager.get_all_words()

# 学习状态管理
word_manager.mark_as_mastered(word_id)
word_manager.mark_as_need_review(word_id)
word_manager.reset_learning_status(word_id)
```

### 4.2 统计模块 (statistics.py)

统计模块负责记录和分析用户的学习数据，提供学习进度和成果的可视化数据。

#### 主要功能

- 记录每日学习单词数
- 统计单词掌握率
- 跟踪学习时长
- 生成学习趋势图表数据
- 提供详细的学习统计报告

#### 核心 API

```python
# 初始化
statistics_manager = StatisticsManager()

# 记录学习数据
statistics_manager.record_word_learned(word_id)
statistics_manager.record_word_mastered(word_id)
statistics_manager.record_study_session(duration)

# 获取统计数据
daily_stats = statistics_manager.get_daily_statistics()
weekly_stats = statistics_manager.get_weekly_statistics()
monthly_stats = statistics_manager.get_monthly_statistics()
total_stats = statistics_manager.get_total_statistics()

# 导出统计数据
statistics_manager.export_statistics()
```

### 4.3 核心功能模块 (core/)

#### 4.3.1 AI 接口模块 (core/ai_interface.py)

- 管理与 AI 服务的交互
- 提供统一的 AI 接口（翻译、语音合成等）
- 处理 AI 请求和响应

#### 4.3.2 数据库管理模块 (core/database_manager.py)

- 管理数据库连接
- 提供数据持久化功能
- 执行数据库查询和操作

#### 4.3.3 学习逻辑模块 (core/learning.py)

- 实现学习算法（如遗忘曲线）
- 管理学习进度和计划
- 生成学习批次

#### 4.3.4 缓存管理模块 (core/cache_manager.py)

- 管理各种缓存数据
- 实现缓存的增删查改
- 处理缓存过期

#### 4.3.5 设置管理模块 (core/settings_manager.py)

- 管理应用程序设置
- 提供设置的加载和保存
- 处理设置变更

#### 4.3.6 听写核心逻辑 (core/dictation.py)

- 实现听写功能的核心逻辑
- 管理听写会话
- 评估听写结果

### 4.4 功能模块 (modules/)

#### 4.4.1 AI 服务模块 (modules/ai_service.py)

- 提供 AI 翻译、语法分析等服务
- 实现与外部 AI 服务的集成

#### 4.4.2 完形填空模块 (modules/cloze_test.py)

- 生成完形填空练习
- 评估练习结果

#### 4.4.3 数据库操作模块 (modules/database.py)

- 实现具体的数据库操作
- 提供数据访问层

#### 4.4.4 题库门户管理模块 (modules/portal_manager.py)

- 管理题库资源
- 提供题库访问接口

#### 4.4.5 阅读理解模块 (modules/reading_comprehension.py)

- 生成阅读理解练习
- 评估练习结果

#### 4.4.6 工具函数模块 (modules/utils.py)

- 提供各种工具函数
- 实现通用功能

#### 4.4.7 单词导入模块 (modules/word_importer.py)

- 从各种格式导入单词
- 实现批量导入功能

### 4.5 音频相关模块

#### 4.5.1 音频播放模块 (audio_player.py)

- 提供音频播放功能
- 支持各种音频格式

#### 4.5.2 音频缓存模块 (audio_cache.py)

- 管理音频缓存
- 实现缓存的增删查改

### 4.6 日志模块 (logger.py)

- 记录应用程序日志
- 支持不同级别的日志
- 提供日志查询和分析功能

## 5. 开发规范

### 5.1 命名规范

- 文件名：小写 + 下划线（如 `word_manager.py`）
- 变量名和函数名：小写 + 下划线（如 `get_random_word()`）
- 类名：PascalCase（如 `WordManager`）

### 5.2 代码质量

- 所有代码必须符合 PEP8 规范
- 使用 flake8 检查代码质量
- 为所有类和方法添加详细注释

### 5.3 数据管理

- 所有用户数据统一保存在 `data/` 目录下
- 使用相对路径访问数据文件
- 写入 JSON 前必须先读取并合并旧数据，避免覆盖

### 5.4 错误处理

- 所有用户输入和外部调用需 try/except 捕获
- 不在 AI 逻辑中直接 exit() 程序
- 所有重要操作写入日志

## 6. 测试说明

### 6.1 单元测试

- 为核心功能编写单元测试
- 测试覆盖主要业务逻辑

### 6.2 集成测试

- 测试模块之间的交互
- 确保 UI 与业务逻辑正确集成

## 7. 部署说明

### 7.1 依赖安装

```bash
pip install -r requirements.txt
```

### 7.2 运行程序

```bash
python -m main
```

## 8. 数据库设计

LexiNote 使用 SQLite 作为数据存储引擎，所有数据统一保存在 `data/lexinote.db` 文件中。以下是详细的数据库设计说明：

### 8.1 表结构概览

| 表名                   | 描述       |
| ---------------------- | ---------- |
| word_sets              | 词库信息表 |
| words                  | 单词表     |
| progress               | 学习进度表 |
| settings               | 设置表     |
| ai_cache               | AI 缓存表  |
| cloze_tests            | 完形填空表 |
| reading_comprehensions | 阅读理解表 |
| delete_logs            | 删除日志表 |
| dictation_sessions     | 听写会话表 |
| exercise_sessions      | 练习会话表 |

### 8.2 详细表结构

#### 8.2.1 词库信息表 (word_sets)

```sql
CREATE TABLE IF NOT EXISTS word_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    source TEXT,
    create_time TEXT,
    word_count INTEGER DEFAULT 0
)
```

**字段说明：**

- `id`: 词库 ID，主键自增
- `name`: 词库名称，唯一
- `description`: 词库描述
- `source`: 词库来源
- `create_time`: 创建时间
- `word_count`: 词库中单词数量

#### 8.2.2 单词表 (words)

```sql
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id INTEGER,
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    phonetic TEXT,
    example TEXT,
    meaning_en TEXT,
    tag TEXT,
    example_translation TEXT,
    familiarity INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_practice TIMESTAMP,
    last_review TIMESTAMP,
    proficiency FLOAT DEFAULT 0.0,
    FOREIGN KEY (set_id) REFERENCES word_sets(id)
)
```

**字段说明：**

- `id`: 单词 ID，主键自增
- `set_id`: 所属词库 ID，外键关联 `word_sets.id`
- `word`: 英文单词
- `translation`: 中文翻译
- `phonetic`: 音标
- `example`: 例句
- `meaning_en`: 英文释义
- `tag`: 标签
- `example_translation`: 例句翻译
- `familiarity`: 熟悉度（学习次数）
- `added_at`: 添加时间
- `last_practice`: 最后练习时间
- `last_review`: 最后复习时间
- `proficiency`: 熟练度（0.0-1.0）

**索引：**

- `idx_word`: 单词索引
- `idx_proficiency`: 熟练度索引
- `idx_set_id`: 词库 ID 索引

#### 8.2.3 学习进度表 (progress)

```sql
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    practice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_correct INTEGER,
    proficiency_change FLOAT,
    FOREIGN KEY (word) REFERENCES words(word)
)
```

**字段说明：**

- `id`: 记录 ID，主键自增
- `word`: 单词，外键关联 `words.word`
- `practice_date`: 练习日期
- `is_correct`: 是否正确（0 或 1）
- `proficiency_change`: 熟练度变化值

**索引：**

- `idx_practice_date`: 练习日期索引

#### 8.2.4 设置表 (settings)

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
```

**字段说明：**

- `key`: 设置项键名，主键
- `value`: 设置项值

#### 8.2.5 AI 缓存表 (ai_cache)

```sql
CREATE TABLE IF NOT EXISTS ai_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_hash INTEGER NOT NULL,
    prompt TEXT,
    response TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    UNIQUE(prompt_hash)
)
```

**字段说明：**

- `id`: 缓存 ID，主键自增
- `prompt_hash`: 提示词哈希值，唯一
- `prompt`: 提示词内容
- `response`: AI 响应内容
- `cached_at`: 缓存时间
- `usage_count`: 使用次数

**索引：**

- `idx_prompt_hash`: 提示词哈希值索引

#### 8.2.6 完形填空表 (cloze_tests)

```sql
CREATE TABLE IF NOT EXISTS cloze_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    options TEXT NOT NULL,  -- JSON格式存储选项
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    source TEXT NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**字段说明：**

- `id`: 题目 ID，主键自增
- `title`: 题目标题
- `content`: 完形填空原文
- `options`: 选项列表（JSON 格式）
- `answer`: 正确答案
- `explanation`: 题目解析
- `source`: 来源
- `date_created`: 创建时间

#### 8.2.7 阅读理解表 (reading_comprehensions)

```sql
CREATE TABLE IF NOT EXISTS reading_comprehensions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT NOT NULL,
    questions TEXT NOT NULL,  -- JSON格式存储题目列表
    answers TEXT NOT NULL,    -- JSON格式存储答案列表
    explanations TEXT NOT NULL,  -- JSON格式存储解析列表
    source TEXT NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**字段说明：**

- `id`: 题目 ID，主键自增
- `article`: 阅读原文
- `questions`: 题目列表（JSON 格式）
- `answers`: 答案列表（JSON 格式）
- `explanations`: 解析列表（JSON 格式）
- `source`: 来源
- `date_created`: 创建时间

#### 8.2.8 删除日志表 (delete_logs)

```sql
CREATE TABLE IF NOT EXISTS delete_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    module_type TEXT NOT NULL,  -- 'cloze' 或 'reading'
    question_data TEXT NOT NULL,  -- JSON格式存储被删除的数据
    delete_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**字段说明：**

- `id`: 日志 ID，主键自增
- `question_id`: 被删除的题目 ID
- `module_type`: 模块类型（'cloze' 或 'reading'）
- `question_data`: 被删除的题目数据（JSON 格式）
- `delete_time`: 删除时间

#### 8.2.9 听写会话表 (dictation_sessions)

```sql
-- 由 create_dictation_tables 方法创建
-- 存储听写会话信息
```

#### 8.2.10 练习会话表 (exercise_sessions)

```sql
-- 由 create_exercise_sessions_table 方法创建
-- 存储练习会话信息
```

### 8.3 表关系图

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  word_sets  │        │    words    │        │   progress  │
├─────────────┤        ├─────────────┤        ├─────────────┤
│ id (PK)     │<───────┤ id (PK)     │───────>│ id (PK)     │
│ name        │        │ set_id (FK) │        │ word (FK)   │
│ description │        │ word        │        │ practice_date│
│ source      │        │ translation │        │ is_correct  │
│ create_time │        │ phonetic    │        │ proficiency_change│
│ word_count  │        │ example     │        └─────────────┘
└─────────────┘        │ meaning_en  │
                       │ tag         │
                       │ example_translation │
                       │ familiarity │
                       │ added_at    │
                       │ last_practice│
                       │ last_review │
                       │ proficiency │
                       ├─────────────┤
                       │             │
                       ▼             ▼
┌─────────────┐    ┌─────────────┐  ┌─────────────┐
│ cloze_tests │    │ delete_logs │  │ reading_comprehensions │
├─────────────┤    ├─────────────┤  ├─────────────┤
│ id (PK)     │<───┤ id (PK)     │  │ id (PK)     │
│ title       │    │ question_id │  │ article     │
│ content     │    │ module_type │  │ questions   │
│ options     │    │ question_data│  │ answers     │
│ answer      │    │ delete_time │  │ explanations│
│ explanation │    └─────────────┘  │ source      │
│ source      │                     │ date_created│
│ date_created│                     └─────────────┘
└─────────────┘

┌─────────────┐        ┌─────────────┐
│  settings   │        │   ai_cache  │
├─────────────┤        ├─────────────┤
│ key (PK)    │        │ id (PK)     │
│ value       │        │ prompt_hash │
└─────────────┘        │ prompt      │
                       │ response    │
                       │ create_time │
                       └─────────────┘
```

#### 详细关联关系说明：

1. **word_sets 与 words 表关系**：

   - 关联字段：`word_sets.id` → `words.set_id`
   - 关系类型：一对多 (One-to-Many)
   - 描述：一个词库可以包含多个单词，每个单词必须属于一个词库

2. **words 与 progress 表关系**：

   - 关联字段：`words.id` → `progress.word`
   - 关系类型：一对多 (One-to-Many)
   - 描述：一个单词可以有多个学习进度记录，每个进度记录关联到一个具体单词

3. **words 与 cloze_tests 表关系**：

   - 关联字段：`words.id` → `cloze_tests.id`
   - 关系类型：一对多 (One-to-Many)
   - 描述：一个单词可以出现在多个完形填空题中，每个完形填空题关联到一个具体单词

4. **words 与 delete_logs 表关系**：

   - 关联字段：`words.id` → `delete_logs.question_id`
   - 关系类型：一对多 (One-to-Many)
   - 描述：一个单词可以有多个删除记录，每个删除记录关联到一个具体单词或问题

5. **reading_comprehensions 与 delete_logs 表关系**：

   - 关联字段：`reading_comprehensions.id` → `delete_logs.question_id`
   - 关系类型：一对多 (One-to-Many)
   - 描述：一篇阅读理解可以有多个删除记录，每个删除记录关联到一个具体的阅读理解或问题

6. **settings 表**：

   - 无外键关联，独立存储系统设置
   - 描述：存储系统的各项配置参数

7. **ai_cache 表**：
   - 无外键关联，独立存储 AI 缓存数据
   - 描述：存储 AI 请求和响应的缓存，提高性能

### 8.4 数据访问

所有数据库操作都通过以下模块进行：

1. **core/database_manager.py**: 主要的数据库管理器，负责单词管理相关的数据库操作
2. **modules/database.py**: 理解类练习（完形填空、阅读理解）的数据库操作

### 8.5 版本迁移

系统会自动检测数据库版本并进行必要的迁移，包括：

- 为旧版本单词表添加 `set_id` 列并关联到默认词库
- 添加新的字段（如 `phonetic`, `example`, `meaning_en`, `tag`, `example_translation`）
- 创建必要的索引以提高查询性能

## 9. 版本更新记录

### v2.7.0 (2025-11-17)
- 清理了DEVELOPER_DOCS.md文件中的重复内容和冗余章节
- 修复了CHANGELOG.md文件的格式问题，统一了变更记录的格式和分类标准
- 创建了utils目录并将其添加到.gitignore文件中，用于存放辅助函数

## 10. 未来计划

- 增加更多学习模式（如拼写练习、听力练习）
- 改进遗忘曲线算法
- 支持单词分类和标签
- 增强学习统计功能，添加更多图表类型和数据维度
