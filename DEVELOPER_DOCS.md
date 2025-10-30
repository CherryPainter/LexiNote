# 开发者文档

本文档为 LexiNote 应用的开发者指南，提供深入理解项目架构、功能实现和开发流程的完整参考。

## 目录

- [项目概述](#项目概述)
- [架构设计](#架构设计)
- [核心模块](#核心模块)
- [功能模块](#功能模块)
- [数据管理](#数据管理)
- [AI功能](#ai功能)
- [UI设计](#ui设计)
- [开发环境设置](#开发环境设置)
- [开发规范](#开发规范)
- [测试策略](#测试策略)
- [部署指南](#部署指南)
- [附录](#附录)

## 项目概述

LexiNote 是一个个人英语学习工具，旨在提供高效、智能的英语学习体验。主要功能包括单词管理、翻译练习、听写练习、阅读理解和完形填空等多种学习模式，同时集成了AI辅助功能提升学习效果。

### 主要功能

- 单词管理与学习进度跟踪
- 多模式练习：翻译、听写、阅读理解、完形填空
- AI辅助学习：翻译判断、例句生成、智能评估
- 个性化学习体验：基于记忆曲线的智能推荐
- 数据统计与分析：学习进度可视化

### 技术栈

- Python 3.12+
- Tkinter (UI框架)
- SQLite (数据存储)
- Ollama API (AI功能)

## 架构设计

### 目录结构

```
├── core/            # 核心功能模块
│   ├── ai_interface.py  # AI接口管理
│   └── learning.py      # 学习逻辑模块
├── data/            # 用户数据存储目录
│   ├── word_list.json   # 单词库文件
│   ├── word_progress.json # 学习进度数据
│   ├── user_settings.json # 用户设置数据
│   └── lexinote.db      # SQLite数据库文件
├── modules/         # 功能模块
│   ├── word_importer.py    # 单词导入功能
│   ├── ai_service.py       # AI服务扩展
│   ├── cloze_test.py       # 完形填空模块
│   ├── reading_comprehension.py # 阅读理解模块
│   ├── database.py         # 数据库操作
│   ├── portal_manager.py   # 题库管理
│   └── utils.py            # 工具函数
├── ui/              # 用户界面模块
│   ├── dictation_page.py  # 听写练习页面
│   ├── learning_page.py   # 学习模式页面
│   ├── main_window.py     # 主窗口
│   ├── review_page.py     # 复习页面
│   ├── translation_page.py # 翻译练习页面
│   ├── cloze_test_page.py # 完形填空页面
│   ├── reading_comprehension_page.py # 阅读理解页面
│   └── ai_assistant_page.py # AI助手页面
├── word_manager.py  # 单词管理核心类
├── audio_player.py  # 音频播放功能
├── logger.py        # 日志记录功能
├── requirements.txt # 项目依赖
├── main.py          # 应用程序入口
├── README.md        # 项目说明
└── DEVELOPER_DOCS.md # 开发者文档
```

### 模块交互关系

```
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│   UI模块     │ ────>│ WordManager  │ ────>│  AIManager    │
│ (ui/*.py)   │ <─── │ (核心桥梁)     │ <───│(core/ai_interface.py)
└─────────────┘      └───────┬──────┘      └───────────────┘
                             │
                             ▼
                     ┌────────────────┐
                     │ LearningManager │
                     │(core/learning.py)│
                     └────────────────┘
                             │
                             ▼
                     ┌─────────────────┐
                     │   数据文件/数据库 │
                     │  (data/)        │
                     └─────────────────┘
```

### 数据流向

1. **UI 层到逻辑层**：
   - 用户操作触发 UI 事件
   - UI 调用 WordManager 提供的方法
   - WordManager 根据需要调用 AIManager 或 LearningManager

2. **逻辑层到数据层**：
   - WordManager 读写单词库和学习进度
   - LearningManager 读写用户学习记录
   - 所有数据操作遵循先读再写的原则，避免覆盖数据

3. **数据层到 UI 层**：
   - WordManager 将处理结果返回给 UI
   - UI 根据返回结果更新界面展示

## 核心模块

### WordManager

**职责**：负责单词的增删改查、管理单词权重和学习进度、提供翻译检查功能

**主要方法**：

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_random_word()` | 获取随机单词进行练习 | exclude_words=None | 单词字符串 |
| `get_weighted_random_word()` | 根据单词权重随机选择单词 | exclude_words=None | 单词字符串 |
| `check_translation()` | 检查翻译正确性并更新学习统计 | word, user_translation, update_stats=True | 布尔值 |
| `translate_text()` | 翻译文本 | text, mode | 翻译结果字符串 |
| `update_word_weight()` | 更新单词权重 | word, is_correct, time_spent | None |
| `update_word_familiarity()` | 更新单词熟悉度 | word, delta | None |
| `add_wrong_word()` | 记录错误单词并增加其权重 | word | None |
| `get_today_learned_words()` | 获取今日学习的单词列表 | 无 | 单词列表 |
| `get_word_example()` | 获取单词例句 | word | 例句字典 |
| `is_ai_available()` | 检查 AI 功能是否可用 | 无 | 布尔值 |
| `get_words_by_criteria()` | 根据条件获取单词 | criteria | 单词列表 |
| `batch_import_words()` | 批量导入单词 | file_path | 导入统计字典 |

**设计特点**：
- 作为 UI 和 AI 功能之间的桥梁
- 从 v1.3.2 版本开始完全使用 AI 进行翻译判断
- 实现了延迟加载 AIManager 的机制，提高启动效率
- 包含完善的错误处理和日志记录

### AIManager (core/ai_interface.py)

**职责**：封装 Ollama API 调用，提供 AI 相关功能

**主要方法**：

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `translate()` | 翻译文本 | text, mode | 翻译结果字符串 |
| `generate_text()` | 生成文本内容 | prompt | 生成文本字符串 |
| `check_translation()` | 判断翻译是否正确 | expected, user_input, is_english_to_chinese | 布尔值 |
| `example()` | 为单词生成例句 | word | 例句字符串 |
| `evaluate_spelling()` | 评估拼写准确性 | word, user_input | 评估结果字典 |

**设计特点**：
- 使用 requests 直接调用 Ollama API，不依赖 ollama 模块
- 实现错误处理和降级服务机制
- 封装提示词工程，优化 AI 输出质量
- 支持流式输出，提升用户体验

### LearningManager (core/learning.py)

**职责**：实现学习模式的核心逻辑，管理单词学习过程

**主要方法**：

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_next_word()` | 获取下一个要学习的单词 | 无 | 单词字符串 |
| `update_mastery_level()` | 更新单词掌握度 | word, rating | None |
| `get_word_definition()` | 获取单词释义 | word | 释义字符串 |
| `get_word_progress()` | 获取单词学习进度 | 无 | 进度统计字典 |

**设计特点**：
- 基于记忆曲线的学习算法
- 个性化的学习进度跟踪
- 智能的单词推荐系统
- 实现依赖注入，避免紧耦合

### AudioPlayer

**职责**：提供单词发音功能

**主要方法**：

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `play_pronunciation()` | 播放单词发音 | word | 布尔值(是否成功) |
| `stop()` | 停止播放 | 无 | None |

**设计特点**：
- 支持多平台音频播放
- 包含错误处理和失败恢复机制

## 功能模块

### 单词批量导入功能 (v1.6.2)

**功能概述**：实现从JSON文件批量导入单词到数据库的功能，支持格式与data/word_dict.json一致，提供高效可靠的批量数据处理能力。

**实现原理**：
- 采用模块化设计，将导入功能封装在独立的`word_importer.py`中，实现单一职责原则
- 使用数据库事务确保数据完整性，避免部分导入失败导致数据不一致
- 通过"INSERT OR IGNORE"语句自动处理重复单词，无需额外的重复检查逻辑
- 实现多层次的错误处理机制，包括文件读取、JSON解析、数据验证和数据库操作

**数据流程**：
1. 验证JSON文件存在且可读
2. 解析JSON文件内容
3. 验证数据格式正确性
4. 逐行验证单词和翻译的有效性
5. 批量插入到数据库（使用事务）
6. 生成导入统计报告
7. 更新内存中的单词缓存

**使用方式**：
- 通过WordManager接口：`word_manager.batch_import_words('path/to/words.json')`
- 直接运行模块：`python -m modules.word_importer path/to/words.json`

### 智能学习算法

**权重算法核心**：
- 初始权重：每个单词初始权重为 1.0
- 错误惩罚：每次错误，权重增加 0.5
- 正确奖励：每次正确，权重乘以 0.8
- 掌握度计算：基于练习历史动态计算单词掌握程度
- 每日衰减：模拟遗忘曲线，自动调整单词权重

### 听写功能前置检查实现

从 v1.4.0 版本开始，系统实现了听写功能前置检查机制：

1. **检查逻辑**：
   - 在 main_window.py 的\_show_dictation_page()方法中，调用 word_manager.get_today_learned_words()获取今日学习的单词
   - 如果返回空列表，表示用户当天未学习单词，显示提示对话框
   - 只有当今日有学习记录时，才允许进入听写页面

2. **用户体验优化**：
   - 提供清晰的错误提示，指导用户先进行单词学习
   - 记录用户操作行为到日志，便于后续分析

### 理解类练习模块

从 v1.1.0 开始引入两个理解类练习模块：

#### 完形填空模块 (ClozeTestModule)

**职责**：提供完形填空练习功能，支持在线生成和离线加载

**主要功能**：
- 在线生成题目：通过AI生成完形填空题目
- 离线加载题目：从数据库加载已保存的题目
- 答案评估：通过AI评估用户答案的正确性
- 进度跟踪：记录用户在完形填空模块的学习进度

#### 阅读理解模块 (ReadingComprehensionModule)

**职责**：提供阅读理解练习功能，支持选择题和主观题

**主要功能**：
- 生成阅读理解材料和问题
- 支持选择题和主观题两种题型
- 智能答案评估：选择题自动判分，主观题通过AI评估
- 学习进度统计：记录用户在阅读理解模块的表现

### AI助手模块 (v1.6.0)

**职责**：提供AI英语学习助手功能，支持多种学习任务类型

**主要功能**：
- 单词解释与例句生成
- 语法讲解
- 写作批改
- 口语练习指导
- 阅读理解辅导
- 听力练习建议
- 词汇量测试
- 英语知识点总结

**设计特点**：
- 使用流式响应提升用户体验
- 异步处理避免UI卡顿
- 支持多种难度级别设置
- 任务类型模板化，优化AI输出质量

## 数据管理

### 数据一致性保障

- 所有用户数据统一保存在 data/ 目录下
- 写入 JSON 前先读取并合并旧数据，避免覆盖
- 数据库操作使用事务确保数据完整性
- 实现多级缓存机制，提升应用响应速度

### 数据库结构

- **lexinote.db**：主要数据库文件
  - **words**：存储单词和翻译信息
  - **word_progress**：记录单词学习进度
  - **cloze_tests**：存储完形填空题目
  - **reading_comprehensions**：存储阅读理解材料和问题
  - **dictation_history**：记录听写历史
  - **progress**：总体学习进度统计

### 数据存储约定

- 单词熟悉度数据存储在 word_familiarity.json 文件中
- 用户设置存储在 user_settings.json 文件中
- 所有数据操作必须通过相应的管理器类进行，避免直接访问文件

## AI功能

### AI 翻译判断

从 v1.3.2 版本开始，翻译判断功能完全交由 AI 处理：

**特点**：
1. **AI 优先判断**：系统默认使用 AI 来判断翻译的正确性
2. **双向支持**：同时支持英译中和中译英的 AI 判断
3. **备用机制**：当 AI 服务不可用时，系统会自动回退到原有的匹配逻辑
4. **AI 参考翻译**：无论翻译是否正确，都提供 AI 的参考翻译

### AI 功能检测机制

从 v1.4.0 版本开始，系统实现了全面的 AI 功能检测机制：

**双层检测机制**：

- 模块导入检测：在\_initialize_ai_manager()方法中尝试导入 AIManager
- 服务连接检测：在 is_ai_available()方法中测试 Ollama 服务连接
- 请求响应检测：在\_test_ai_connection()方法中发送实际请求验证功能可用性

**降级处理策略**：

- 当 AI 功能不可用时，get_word_example()方法提供硬编码的基础例句作为备用
- 所有 AI 调用都包含 try-except 捕获，确保系统在 AI 不可用时仍能正常运行

### AI 输出质量与 JSON 解析重试机制

为确保 AI 调用在实际运行中更稳定、可调试，项目实现了以下机制：

1. **输出质量规范**：
   - 定义了标准的 JSON 格式，确保 AI 返回的数据结构一致性
   - 针对不同功能类型（如完形填空、阅读理解）制定专门的格式规范

2. **解析工具**：
   - `extract_json_from_text()` 方法用于从 AI 返回的文本中提取有效的 JSON
   - 支持从非标准格式中提取 JSON 内容，提高鲁棒性

3. **重试机制**：
   - 当解析失败时，系统会发送补充提示并重试一次
   - 若重试失败，记录原始响应到日志并提供容错处理

4. **日志记录**：
   - 详细记录 AI 调用过程中的所有重要事件和错误
   - 支持将原始 AI 响应保存到 cache/ai_text/ 目录，便于后续分析

## UI设计

### 界面架构设计

**页面继承与参数一致性**：
- 所有页面类统一继承自 tk.Frame，确保一致的继承结构
- 统一参数传递模式，所有页面都接受 settings_manager 参数
- 通用滚动框架组件，统一管理滚动功能，解决内容溢出问题
- 页面组件正确绑定父框架，避免组件层次混乱

### 设置监听器与运行时生效

为支持用户在运行时修改设置并立即生效，项目引入了 SettingsManager 的监听器机制：

- 在页面/组件初始化时注册必要的监听器
- 在页面销毁或切换时注销监听器，避免内存泄漏
- 监听器回调应尽量轻量，避免在主线程执行耗时操作
- 如需修改 tkinter 组件，使用 `widget.after(0, func)` 将操作调度到主线程

## 开发环境设置

### 必要依赖

- Python 3.12+
- 依赖库：见 requirements.txt
- Ollama 服务（用于 AI 功能）

### 开发流程

1. 克隆仓库：`git clone https://github.com/CherryPainter/LexiNote.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 确保 Ollama 服务正在运行（默认端口 11434）
4. 运行程序：`python main.py`

## 开发规范

### 代码规范

- 遵循 PEP8 编码规范
- 类名使用 PascalCase
- 函数名和变量名使用小写+下划线
- 为所有公共函数添加文档字符串

### 数据存储

- 所有用户数据统一保存在 data/目录下
- 写入前先读取并合并旧数据，避免覆盖
- 路径写为相对路径

### 错误处理

- 所有用户输入和外部调用需 try/except 捕获
- 重要操作都写入 logger.py 记录
- 不能在 AI 逻辑中直接 exit() 程序

### 日志与调试

- 所有重要操作（练习开始、错误单词、翻译失败）都写入 logger.py 记录
- AI 功能异常时提供优雅降级，确保应用基本功能可用
- 完善的边界条件处理，避免索引越界、空队列访问等问题

### 版本控制

- 使用 git 进行版本控制
- 每次重大修改更新版本号：v1.0.0 → v1.1.0
- 所有核心逻辑变更记录在 DEVELOPER_DOCS.md
- 详细的版本更新日志请参考 CHANGELOG.md 文件

## 测试策略

### 单元测试

推荐为以下功能编写单元测试：

1. AI 输出解析功能：`extract_json_from_text()`
2. 数据导入导出功能
3. 单词权重计算算法
4. 翻译判断逻辑
5. 错误处理和降级服务机制

### 测试建议

- 为 `extract_json_from_text` 编写测试用例，包括：
  - 标准 JSON
  - JSON 前后包含说明文字
  - JSON 被额外的解释包围
  - 完全无效文本

- 对 `AIService.evaluate_reading_answer` 写集成测试：
  - 模拟模型返回标准 JSON
  - 模拟返回难解析的 JSON
  - 模拟返回无法解析的文本

## 部署指南

### 本地部署

1. 确保已安装 Python 3.12 或更高版本
2. 安装所有依赖：`pip install -r requirements.txt`
3. 下载并安装 Ollama（https://ollama.com/）
4. 拉取必要的模型：`ollama pull gemma:7b`
5. 启动 Ollama 服务
6. 运行应用：`python main.py`

### 配置说明

- Ollama 默认服务地址：http://localhost:11434
- 数据存储目录：./data/
- 日志文件：./logs/

## 附录

### 模块独立性原则

每个文件必须只做一件事：
- 核心逻辑与 UI 严格分离
- 数据访问通过专门的管理器类进行
- 工具函数集中在 utils.py 中

### 命名规范

- 文件名：小写 + 下划线
- 变量名：小写 + 下划线
- 函数名：小写 + 下划线
- 类名：PascalCase

### 版本历史参考

详细的版本更新日志请参考 <mcfile name="CHANGELOG.md" path="d:/Learn/data/py25/25-10-25/CHANGELOG.md"></mcfile> 文件，该文档中记录了从v1.1.4到最新版本的完整变更历史。
