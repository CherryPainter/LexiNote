# 开发者文档

本文档记录了 LexiNote 应用的核心逻辑变更和开发信息。

## 版本历史

### v1.5.1 (2025-10-29)

- 实现完形填空和阅读理解题目删除功能
  - 在标题右侧添加删除按钮，仅在离线模式下可用
  - 实现删除确认对话框，防止误操作
  - 在database.py中添加delete_logs表和相关记录功能
  - 实现完整的错误处理和日志记录
- 修复删除按钮不响应问题
  - 在ClozeTestModule和ReadingComprehensionModule中添加_current_mode属性
  - 增强get_mode方法，准确反映当前实际使用的模式（而非仅检测AI可用性）
  - 修改模式检测逻辑，避免循环引用问题

### v1.5.0 (2025-10-29)

- 集成 AI 功能（使用 gemma:7b 模型）
- 添加翻译、例句生成、拼写评估功能
- 实现 AI 功能降级服务
- 添加用户学习建议生成功能
- 集成本地 AI 功能，通过 requests 直接调用 Ollama API
- 创建 core/ai_interface.py 实现 AIManager 类
- 添加学习模式功能，实现主动单词记忆
- 创建 core/learning.py 核心逻辑模块
- 创建 ui/learning_page.py 用户界面模块
- 新增 word_progress.json 数据文件存储学习进度
- 实现基于掌握度的权重调整算法
- 更新主界面导航菜单，优化用户体验
- 创建 test_ai_fallback.py 测试脚本验证降级机制
- 实现完形填空与阅读理解功能

### v1.4.6 (2025-10-29)

- 移除了听写练习页面导航限制，允许用户即使今日没有学习单词也能进入页面使用其他功能（熟词、随机词库、难词等）
- 队列听写中添加了来源单词检查，当所选来源没有单词时显示弹窗提示用户选择其他来源，不自动继续
- 修复了 dictation.py 中 build_queue 方法的 UnboundLocalError 错误
- 修复了 WordManager 类缺少 wrong_words 属性的问题
- 修复了 AIManager 中 advise 方法异步调用未等待的 RuntimeWarning 警告
- 修复了数据库查询中错误引用 progress 表 proficiency 列的问题（proficiency 列实际在 words 表中）
- 更新了版本日期格式

### v1.4.5 (2025-10-29)

- 修复听写队列长度控制问题，确保严格按照设置数量显示单词
- 改进 has_next_in_queue 方法，增加空队列检查以避免索引错误
- 修改 next_in_queue 方法，在返回单词前先检查队列是否存在和索引有效性
- 在\_next_word_in_queue 方法中添加队列结束预检查，避免尝试获取第 11 个单词
- 更新\_check_answer 方法中的队列结束判断逻辑，使用精确的索引比较
- 修改\_skip_word 方法，增加队列结束检查以避免跳过后显示额外单词
- 移除了 build_queue 方法中的 limit-1 补丁，改回直接使用 limit 保证用户期望的单词数量
- 优化今日统计信息收集逻辑，使用 set 避免重复计数，确保 accuracy 计算准确
- 改进 current_queue_index 的计算方式，使用 min/max 保证数值在合理范围内

### v1.4.3 (2025-10-29)

- 实现超时单词影响权重功能，确保听写中超时的单词被视为未掌握
- 修复队列控制精度问题，确保设置的听写单词数量准确（如设置 10 个只听写 10 个）
- 在 dictation_page.py 中新增\_handle_timeout 方法，专门处理单词超时情况
- 优化\_skip_word 方法，确保跳过的单词正确影响权重
- 增强 Stop_timer 方法的健壮性，添加 hasattr 检查
- 确保所有单词失败场景（跳过、拼写错误、超时）统一影响权重计算
- 优化日志记录，提供更详细的学习情况追踪
- 修复 PEP8 代码规范问题，提高代码质量

### v1.4.2 (2025-10-29)

- 实现今日学习进度检测与听写提醒逻辑功能
- 添加补丁规格文档并完善相关测试
- 在 word_manager.py 中添加 check_today_progress_completed 方法
- 修改 dictation_page.py，添加学习进度检查和用户提醒对话框
- 更新 learning.py，实现学习完成标记功能
- 优化 dictation_page.py 中的学习进度检查逻辑，允许用户在未完成今日学习时选择其他来源
- 大幅增强 word_manager.py 中的 get_today_learned_words 方法，提高单词检测准确率
- 改进 core/dictation.py 中的单词选择逻辑，实现"即使今天没学也可以听写往期单词"的需求
- 添加详细的日志记录，便于问题排查
- 在 word_manager.py 中添加 check_spelling 方法，修复听写页面中的拼写检查功能
- 在 dictation_page.py 中添加单个听写模式的自动/手动跳转设置功能

### v1.4.1 - 新增听写核心模块与学习功能增强

- 新增 core/dictation.py 核心模块，实现听写练习的底层逻辑
- 更新 core/learning.py，增强学习功能的实现
- 优化 ui/dictation_page.py，提升听写页面的用户体验
- 改进 ui/review_page.py，完善复习功能的展示
- 完善 WordManager 和 AIManager 方法文档
- 添加 AI 功能检测机制详细文档

### v1.4.0 - AI 功能初始化改进与听写前置检查

- 修复 WordManager 中调用不存在的`is_ai_available()`方法的问题
- 添加`_test_ai_connection()`方法实现 AI 连接可用性测试
- 改进 AI 功能初始化逻辑，确保即使 AI 初始化失败应用也能正常运行
- 优化错误处理和日志记录，提供更详细的 AI 功能状态信息
- 实现听写功能前置检查：用户当天必须学习过单词才能进入听写页面
- 在 main_window.py 中添加单词学习状态检查逻辑
- 优化用户体验，提供清晰的操作引导

### v1.3.4 - 页面继承与参数一致性修复

- 修复页面继承问题：让 DictationPage 和 ReviewPage 继承自 tk.Frame，确保所有页面类具有一致的继承结构
- 修复参数传递一致性：确保所有页面都接受 settings_manager 参数，使配置能正确传递
- 改进字体配置：为所有页面添加统一的默认字体配置
- 优化页面初始化逻辑：修复了 LearningPage 初始化中的参数重复问题
- 更新页面组件的父组件引用：确保所有子组件正确绑定到父框架

### v1.3.3 - 项目文件清理

- 移除了 6 个无用的测试文件，包括 test_ai_fallback.py、test_fix.py 等
- 删除了过时的设计文档文件：AI Integration Design Book.md 和 learning_mode_definition.md
- 保持项目结构清晰，移除冗余文件

### v1.3.2 - AI 翻译判断功能优化

- 完全实现翻译判断功能交由 AI 处理
- 优化了 AI 管理器的初始化逻辑，实现延迟加载机制
- 改进了错误处理，确保 AI 调用失败时有备用逻辑
- 增强了翻译结果展示，包括视觉反馈和 AI 参考翻译
- 优化了翻译判断的提示词工程
- 修复了重复返回语句问题
- 为所有翻译方向（英译中/中译英）提供 AI 参考翻译
- 优化了跳过功能，为跳过的单词也提供 AI 翻译参考
- 延长了结果显示时间，提升学习体验
- 改进了错误处理和日志记录

### v1.3.1

- 修复了翻译判断逻辑中的错误
- 改进了同义词和特定单词处理
- 增强了日志记录功能

### v1.3.0

- 增强了翻译练习的用户反馈机制
- 添加了明确的对错提示信息，包含更详细的反馈内容
- 整合 AI 参考翻译功能，为英译汉提供补充参考
- 增加了结果显示的等待时间，提升用户体验
- 增强了翻译匹配算法，修复'diagram'等单词的翻译识别问题
- 添加了单词特定翻译映射，改进近义词识别
- 降低了字符匹配阈值，提高翻译识别准确率

### v1.2.0 (2025-10-27)

- 重大改进：英译汉模糊匹配算法重构
- 添加近义词识别功能，支持常见中文近义词映射
- 针对 minor 等特定单词的翻译识别优化
- 实现多维度匹配策略：完全匹配、近义词匹配、字符比例匹配、连续字符匹配
- 修复翻译检查函数潜在的 None 返回值 bug
- 优化短翻译的匹配逻辑，提高识别准确率
- 创建测试脚本 test_translation_matching.py 验证翻译匹配功能

### v1.1.4 (2025-10-26)

- 修复 LearningManager 中的 get_word_definition 方法，确保正确获取单词释义
- 解决 GUI 无法显示单词学习内容的问题
- 在 main_window.py 中添加了 pack(fill=tk.BOTH, expand=True)使 LearningPage 正确显示
- 修复 AttributeError: 'WordManager' object has no attribute 'scheduler'错误

### v1.1.1 (2025-10-26)

- 修复 LearningManager 初始化依赖问题，解决'WordManager' object has no attribute 'scheduler'错误
- 改进依赖注入机制，使 LearningManager 能正确使用 WordManager 提供的功能
- 优化 LearningPage 的 UI 加载逻辑
- 修复数据文件路径问题，确保正确读取和保存数据

### v1.1.0 - 新增理解练习模块

- **新功能：完形填空模块**
  - 创建了`modules/cloze_test.py`作为完形填空的核心控制器
  - 实现了在线（AI 生成）和离线（数据库加载）两种模式
  - 添加了题目生成、答题和评估功能
  - 创建了`ui/cloze_test_page.py`作为用户界面
- **新功能：阅读理解模块**
  - 创建了`modules/reading_comprehension.py`作为阅读理解的核心控制器
  - 支持多选题和主观题的生成和评估
  - 实现了在线和离线模式
  - 创建了`ui/reading_comprehension_page.py`作为用户界面
- **数据库扩展**
  - 创建了`modules/database.py`管理新功能的数据存储
  - 在现有`lexinote.db`中添加了`cloze_tests`和`reading_comprehensions`表
  - 实现了完整的 CRUD 操作
- **AI 服务扩展**
  - 创建了`modules/ai_service.py`处理新功能的 AI 交互
  - 实现了专门的提示词模板用于生成测试题目和评估答案
- **题库门户管理**
  - 创建了`modules/portal_manager.py`用于管理离线题库
  - 支持题目列表查看、删除、导出等功能
- **UI 集成**
  - 在主窗口添加了完形填空和阅读理解的导航按钮
  - 实现了统一的页面切换和状态管理机制

### v1.1.0 - 系统性能优化

- 实现了基于 SQLite 的数据库存储系统，替代原有的 JSON 文件存储
- 添加了 DatabaseManager 类，提供高效的数据库操作接口
- 优化了 DictationManager，支持数据库和文件存储的双模式切换
- 实现了 get_word_progress 方法，用于获取单词学习进度统计
- 设计了 dictation_history 和 progress 表结构，支持高效查询和更新
- 添加了内存缓存机制，减少数据库访问频率
- 实现了数据迁移功能，确保旧数据平滑过渡到新存储模式
- 优化了错误处理和日志记录，提高系统稳定性

### v1.0.0 (2025-10-25)

- 基础单词管理功能
- 翻译练习模式
- 听写练习模式
- 单词复习模式
- 简单的进度跟踪

## 项目架构

### 目录结构

```
├── core/            # 核心功能模块
│   ├── ai_interface.py  # AI接口管理
│   └── learning.py      # 学习逻辑模块
├── data/            # 用户数据存储目录
│   ├── word_list.json   # 单词库文件
│   ├── word_progress.json # 学习进度数据
│   └── user_settings.json # 用户设置数据
├── ui/              # 用户界面模块
│   ├── dictation_page.py  # 听写练习页面
│   ├── learning_page.py   # 学习模式页面
│   ├── main_window.py     # 主窗口
│   ├── review_page.py     # 复习页面
│   └── translation_page.py # 翻译练习页面
├── word_manager.py  # 单词管理核心类
├── audio_player.py  # 音频播放功能
├── logger.py        # 日志记录功能
├── requirements.txt # 项目依赖
├── main.py          # 应用程序入口
├── README.md        # 项目说明
└── DEVELOPER_DOCS.md # 开发者文档
```

### 核心模块说明

#### WordManager

- **职责**：负责单词的增删改查、管理单词权重和学习进度、提供翻译检查功能
- **主要方法**：
  - `get_random_word(exclude_words=None)`：获取随机单词进行练习，可选排除指定单词
  - `get_weighted_random_word(exclude_words=None)`：根据单词权重随机选择单词
  - `check_translation(word, user_translation, update_stats=True)`：检查翻译正确性并更新学习统计
  - `translate_text(text, mode)`：翻译文本（英 → 中/中 → 英）
  - `update_word_weight(word, is_correct, time_spent)`：更新单词权重，考虑正确与否和响应时间，影响练习时的出现频率
  - `update_word_familiarity(word, delta)`：更新单词熟悉度（0-1 范围）
  - `add_wrong_word(word)`：记录错误单词并增加其权重
  - `get_today_learned_words()`：获取今日学习的单词列表，用于听写功能前置检查
  - `get_word_example(word)`：获取单词例句，包含英文例句和中文翻译
  - `get_example_sentence(word)`：兼容性方法，调用 get_word_example
  - `is_ai_available()`：检查 AI 功能是否可用，包括模块导入检查和 Ollama 服务连接测试
  - `get_words_by_criteria(criteria)`：根据条件获取单词，支持筛选不熟悉、困难单词和长度限制
  - `_init_ai_manager()`：初始化 AI 管理器（延迟加载）
  - `_test_ai_connection()`：测试 AI 连接是否可用，通过发送实际请求验证
- **设计特点**：
  - 作为 UI 和 AI 功能之间的桥梁
  - 从 v1.3.2 版本开始完全使用 AI 进行翻译判断
  - 实现了延迟加载 AIManager 的机制，提高启动效率
  - 包含完善的错误处理和日志记录
  - v1.4.0 版本改进了 AI 连接测试机制，确保准确判断 AI 功能可用性
  - 实现了基于熟悉度和错误次数的智能单词推荐系统

#### AIManager (core/ai_interface.py)

- **职责**：封装 Ollama API 调用，提供 AI 相关功能
- **主要方法**：
  - `translate(text, mode)`：翻译文本（英 → 中/中 → 英）
  - `generate_text(prompt)`：生成文本内容
  - `check_translation(expected, user_input, is_english_to_chinese)`：判断翻译是否正确
  - `example(word)`：为单词生成例句（注意：方法名为 example 而非 generate_example）
  - `evaluate_spelling(word, user_input)`：评估拼写准确性
- **设计特点**：
  - 使用 requests 直接调用 Ollama API，不依赖 ollama 模块
  - 实现错误处理和降级服务机制
  - 封装提示词工程，优化 AI 输出质量
  - 返回标准化的错误信息，方便上层调用者处理

#### LearningManager (core/learning.py)

- **职责**：实现学习模式的核心逻辑，管理单词学习过程
- **主要方法**：
  - `get_next_word()`：获取下一个要学习的单词
  - `update_mastery_level(word, rating)`：根据用户评分更新单词掌握度
  - `get_word_definition(word)`：获取单词释义
  - `get_word_progress()`：获取单词学习进度
- **设计特点**：
  - 基于记忆曲线的学习算法
  - 个性化的学习进度跟踪
  - 智能的单词推荐系统
  - 实现依赖注入，避免紧耦合

#### AudioPlayer

- **职责**：提供单词发音功能
- **主要方法**：
  - `play_pronunciation(word)`：播放单词发音
  - `stop()`：停止播放
- **设计特点**：
  - 支持多平台音频播放
  - 包含错误处理和失败恢复机制

### 新增AI助手模块（v1.6.0）

#### AIAssistantPage（ui/ai_assistant_page.py）

- **职责**：提供AI英语学习助手界面，支持多种学习任务类型
- **主要功能**：
  - 单词解释与例句生成
  - 语法讲解
  - 写作批改
  - 口语练习指导
  - 阅读理解辅导
  - 听力练习建议
  - 词汇量测试
  - 英语知识点总结
- **设计特点**：
  - 使用流式响应提升用户体验
  - 异步处理避免UI卡顿
  - 支持多种难度级别设置
  - 任务类型模板化，优化AI输出质量
  - 实时连接状态检测

### 模块交互关系

```
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│   UI模块    │ ────>│ WordManager  │ ────>│  AIManager    │
│ (ui/*.py)   │ <─── │ (核心桥梁)   │ <─── │(core/ai_interface.py)
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
                     │   数据文件       │
                     │  (data/*.json)  │
                     └─────────────────┘
```

### 数据流向说明

1. **UI 层到逻辑层**：

   - 用户操作触发 UI 事件
   - UI 调用 WordManager 提供的方法
   - WordManager 根据需要调用 AIManager 或 LearningManager
   - 听写功能前置检查：main_window.py 调用 WordManager.get_today_learned_words()验证用户学习状态

2. **逻辑层到数据层**：

   - WordManager 读写单词库和学习进度
   - LearningManager 读写用户学习记录
   - 所有数据操作遵循先读再写的原则，避免覆盖数据
   - word_familiarity.json 存储单词熟悉度和最后学习时间，用于实现日期筛选

3. **数据层到 UI 层**：
   - WordManager 将处理结果返回给 UI
   - UI 根据返回结果更新界面展示
   - 错误信息通过日志记录并在 UI 适当位置提示用户
   - 听写功能前置检查失败时，通过 messagebox 显示友好提示

### 听写功能前置检查实现

从 v1.4.0 版本开始，系统实现了听写功能前置检查机制，具体实现如下：

1. **检查逻辑**：

   - 在 main_window.py 的\_show_dictation_page()方法中，调用 word_manager.get_today_learned_words()获取今日学习的单词
   - 如果返回空列表，表示用户当天未学习单词，显示提示对话框
   - 只有当今日有学习记录时，才允许进入听写页面

2. **用户体验优化**：

   - 提供清晰的错误提示，指导用户先进行单词学习
   - 记录用户操作行为到日志，便于后续分析
   - 保持界面简洁，避免用户在不适当的时机进入听写练习

3. **技术实现**：
   - 使用 datetime 模块获取当前日期
   - 从 word_familiarity.json 中提取单词学习时间信息
   - 使用 Tkinter 的 messagebox 模块显示友好提示
   - 实现日期字符串比较，精确匹配今天的学习记录

### AI 功能检测机制

从 v1.4.0 版本开始，系统实现了全面的 AI 功能检测机制，确保用户体验的稳定性：

1. **双层检测机制**：

   - 模块导入检测：在\_initialize_ai_manager()方法中尝试导入 AIManager
   - 服务连接检测：在 is_ai_available()方法中测试 Ollama 服务连接
   - 请求响应检测：在\_test_ai_connection()方法中发送实际请求验证功能可用性

2. **降级处理策略**：

   - 当 AI 功能不可用时，get_word_example()方法提供硬编码的基础例句作为备用
   - 所有 AI 调用都包含 try-except 捕获，确保系统在 AI 不可用时仍能正常运行
   - 错误信息通过 logger 记录，便于排查问题

3. **日志记录**：
   - AI 初始化、连接测试、功能调用都有详细的日志记录
   - 清晰标识 AI 功能的可用性状态，方便调试
   - 记录所有 AI 相关错误，包括模块导入失败、服务连接失败等

### 新增理解类练习模块说明 (Cloze / Reading)

从 v1.1.0 开始引入两个理解类练习模块：完形填空（ClozeTestModule）和阅读理解（ReadingComprehensionModule），位于 `modules/` 目录下。以下为开发者应知的实现细节与注意点：

- 目录与文件：
  - `modules/cloze_test.py`：完形填空控制器，负责加载题目、准备显示格式、提交答案并调用 AIService 评估。
  - `modules/reading_comprehension.py`：阅读理解控制器，支持选择题与主观题的逐题或一次性提交评估。
  - `modules/ai_service.py`：与 AIManager（core/ai_interface.py）配合，负责生成题目和对主观题进行 AI 评估。
  - `modules/database.py`：管理题库的 SQLite 存取（表 `cloze_tests`、`reading_comprehensions`）。

注意事项与约定：

1. AI 输出契约与解析

- 在向 AI 请求生成题目或评估主观题时，必须在 prompt 中明确要求“只返回 JSON 对象”，并提供 JSON schema。
- 实际中 AI 可能返回带注释或多余文本。为了提高健壮性，项目中新增 `modules/utils.py::extract_json_from_text(text)`，用于：
  - 直接尝试 json.loads(text)
  - 若失败，使用正则提取文本中的第一对花括号内容并解析
- 在 `AIService.evaluate_reading_answer` 中，如果首次解析失败，系统会自动重试一次并提示 AI “仅返回 JSON”，如仍失败会记录原始响应到日志并返回评估失败提示。

2. 字段兼容性

- 由于不同 prompt/模型返回的字段名可能不同（例如完形填空 AI 端可能用 `answers` 或 `answer`），`ClozeTestModule` 已实现字段兼容层：
  - 若返回含 `answers` 而无 `answer`，模块会复制 `answers` 到 `answer` 字段。
  - 选项可接受 AI 返回的 `text`（分号分隔）或 `options` 列表两种格式，模块会标准化为 `{'blank': int, 'options': [str,...]}`。

3. 数据库与保存

- `modules/database.py` 提供 CRUD 方法，请务必使用该接口保存/读取题目，避免直接操作底层 SQLite 文件。

4. 调试建议

- 若 AI 返回解析失败，可在日志中查找 `解析AI评估结果失败，原始返回` 条目；也可以直接在 `cache/ai_text/` 中保存原始响应以便后续分析（可按需实现）。

5. 示例用法（同步）

```python
from modules.ai_service import AIService
from modules.cloze_test import ClozeTestModule

ai = AIService()
cloze = ClozeTestModule()

# 在线生成并保存题目
test = ai.generate_cloze_test(level='中级', topic='环境')
if test:
   display = cloze.get_test_by_id(test['id'])
   print(display['content'])

# 本地评估
is_correct, eval_text, explanation = cloze.submit_answer('apple,run,...')
print(is_correct, eval_text)
```

6. 单元测试

- 推荐为生成与解析逻辑添加单元测试，尤其是 AI 返回非标准格式时的解析/重试逻辑。

### 开发环境设置

#### 必要依赖

- Python 3.12+
- 依赖库：见 requirements.txt
- Ollama 服务（用于 AI 功能）

#### 开发流程

1. 克隆仓库：`git clone https://github.com/CherryPainter/LexiNote.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 确保 Ollama 服务正在运行（默认端口 11434）
4. 运行程序：`python main.py`

## 设置监听器与运行时生效（开发者指南）

为支持用户在运行时修改设置并立即生效，项目引入了 SettingsManager 的监听器机制（`register_listener` / `unregister_listener`）。开发者在实现或修改 UI 页面时请注意以下约定：

- 在页面/组件初始化时注册必要的监听器，示例：

```python
# 在页面 __init__ 中
self.settings_manager.register_listener('auto_mode_review', self._on_auto_mode_review_change)
```

- 在页面销毁或切换时注销监听器，避免内存泄漏或对已经销毁组件的回调。

```python
# 页面关闭或切换前
self.settings_manager.unregister_listener('auto_mode_review', self._on_auto_mode_review_change)
```

- 监听器回调应尽量轻量：只执行 UI 更新（显示/隐藏按钮、启停计时器、设置变量等）。若需执行耗时任务，请在回调内启动后台线程。

- 如果回调需要修改 tkinter 组件，使用 `widget.after(0, func)` 将操作调度到主线程，以避免线程安全问题。

- 常见情形：
  - 切换到自动模式：隐藏手动“下一步”按钮，并在合适条件（答对/答错/例句显示）触发延迟自动跳转。
  - 切换到手动模式：立即显示“下一步”按钮，取消任何自动跳转（或让下一次自动跳转失效）。

通过上述约定，设置变更能在正在进行的练习中即时生效，不需要重启应用。请在修改 UI 行为时同时更新 `API_DOCUMENTATION.md` 中的示例，以便其他开发者参考。

## AI 翻译判断说明

从 v1.3.2 版本开始，翻译判断功能完全交由 AI 处理，具有以下特点：

1. **AI 优先判断**：系统默认使用 AI 来判断翻译的正确性，提供更准确、更智能的判断结果
2. **双向支持**：同时支持英译中和中译英的 AI 判断
3. **备用机制**：当 AI 服务不可用时，系统会自动回退到原有的匹配逻辑
4. **视觉反馈**：判断结果会通过醒目的颜色和背景闪烁提供清晰的视觉提示
5. **AI 参考翻译**：无论翻译是否正确，都提供 AI 的参考翻译，帮助用户更好地学习
6. **状态显示**：在状态栏显示当前的判断方式（AI 或系统），保持透明度

### 提示词工程

系统使用精心设计的提示词来确保 AI 判断的准确性：

- 明确的任务指令（判断翻译是否正确）
- 提供原始词语和用户翻译
- 要求简洁的二选一回答（正确/错误）
- 避免添加额外解释，确保结果易于解析

### 错误处理

所有 AI 调用都包含完善的错误处理机制：

- 捕获所有可能的异常，确保程序稳定运行
- 记录详细的错误日志，便于排查问题
- 自动回退到备用逻辑，保证功能可用性

#### AIManager

- 封装 Ollama API 调用
- 提供翻译、例句生成、拼写评估等功能
- 实现错误处理和降级服务

#### 学习模式

- 基于记忆曲线的学习算法
- 个性化的学习进度跟踪
- 智能的单词推荐系统

## 开发规范

### 代码规范

- 遵循 PEP8 编码规范
- 类名使用 PascalCase
- 函数名和变量名使用小写+下划线
- 为所有公共函数添加文档字符串

### 数据存储

- 所有用户数据统一保存在 data/目录下
- 使用 JSON 格式存储数据
- 写入前先读取并合并旧数据，避免覆盖

### 错误处理

- 所有用户输入和外部调用需 try/except 捕获
- 重要操作都写入 logger.py 记录
- 不要在 AI 逻辑中直接 exit()程序

### 版本控制

- 使用 git 进行版本控制
- 每次重大修改更新版本号：v1.0.0 → v1.1.0
- 所有核心逻辑变更记录在 DEVELOPER_DOCS.md
# AI 杈撳嚭濂戠害銆丣SON 瑙ｆ瀽涓庨噸璇曪紙琛ュ厖璇存槑锛?

涓轰簡璁?AI 璋冪敤鍦ㄧ湡瀹炶繍琛屼腑鏇寸ǔ瀹氥€佸彲璋冭瘯锛岄」鐩伒寰互涓嬬害瀹氬苟鎻愪緵浜嗚緟鍔╁伐鍏凤細

1. 杈撳嚭濂戠害锛堟帹鑽愶級

- 瀹屽舰濉┖锛堢敓鎴愶級绀轰緥濂戠害锛?

```json
{
  "id": "string",
  "content": "甯﹀崰浣嶇鐨勯鐩枃鏈紝浣跨敤 [[_]] 鎴栫被浼兼爣璁拌〃绀虹┖",
  "blanks": [
    { "blank": 1, "options": ["閫夐」A", "閫夐」B", "閫夐」C"], "answer": "閫夐」A" },
    { "blank": 2, "options": ["閫夐」X", "閫夐」Y"], "answer": "閫夐」Y" }
  ],
  "explanation": "(鍙€? 瑙ｆ瀽鎴栫ず渚嬬瓟妗?
}
```

- 闃呰鐞嗚В锛堜富瑙傞 AI 璇勪及锛夌ず渚嬪绾︼細

```json
{
  "score": 0, // 鏁存暟 0-100
  "feedback": "绠€鐭弽棣堬紙閫傚悎 UI 鏄剧ず锛?,
  "reason": "璇︾粏瑙ｉ噴锛堝彲閫夛級"
}
```

瀵归€夋嫨棰樼被鐨勮瘎浼帮紝涔熷厑璁镐娇鐢ㄧ畝鍗曠殑 `{ "correct": true, "feedback": "..." }` 褰㈡€併€?

2. 瑙ｆ瀽宸ュ叿

- 椤圭洰鍦?`modules/utils.py` 涓彁渚?`extract_json_from_text(text)`锛?

  - 浼樺厛灏濊瘯鐩存帴 `json.loads`銆?
  - 鑻ュけ璐ワ紝浼氬皾璇曚粠鏂囨湰涓娊鍙栭涓?JSON 瀵硅薄锛堝厛闈炶椽濠紝鍐嶈椽濠尮閰嶏級銆?
  - 杩斿洖瑙ｆ瀽鍚庣殑 Python 瀵硅薄鎴?`None`銆?

- 鍦?`modules/ai_service.py` 涓涓昏棰樿瘎浼拌皟鐢ㄥ仛浜嗕袱杞瓥鐣ワ細
  1. 棣栨鐢ㄥ父瑙?prompt 璇锋眰 AI 缁欏嚭 JSON銆傝嫢 `extract_json_from_text` 鎴愬姛鍒欑户缁€?
  2. 鑻ヨВ鏋愬け璐ワ紝鍚?AI 鍙戦€佷竴娆″甫鏈夆€滃彧杩斿洖 JSON锛屼笉瑕佷换浣曡В閲婃垨澶氫綑鏂囧瓧鈥濈殑琛ュ厖鎻愮ず骞堕噸璇曚竴娆°€?
  3. 鑻ヤ粛澶辫触锛岃褰曞師濮?AI 杩斿洖鍒版棩蹇?缂撳瓨锛屽苟杩斿洖瑙ｆ瀽澶辫触鐨勫閿欑粨鏋滐紙閬垮厤闃诲鐢ㄦ埛娴佺▼锛夈€?

3. 鏃ュ織涓庡璁?

- 褰撹В鏋愬け璐ユ椂锛屼唬鐮佷細鍦ㄦ棩蹇椾腑鍐欏叆甯︽爣绛剧殑鍘熷 AI 鏂囨湰锛堝 `瑙ｆ瀽AI璇勪及缁撴灉澶辫触锛屽師濮嬭繑鍥?`锛夛紝渚夸簬绂荤嚎鍒嗘瀽銆?
- 寤鸿鍚敤骞朵繚鐣?`cache/ai_text/` 鐩綍锛堝凡鍦ㄩ」鐩腑棰勭暀锛夛紝鎶婂け璐ユ垨閲嶈鐨?AI 鍘熸枃淇濆瓨涓?JSON 鏂囦欢渚涗簨鍚庡垎鏋愩€?

4. 寮€鍙戣€呬娇鐢ㄧず渚嬶紙鍚屾/蹇€熼獙璇侊級

```python
from modules.utils import extract_json_from_text
from modules.ai_service import AIService

ai = AIService()

# 鍋囧畾 ai.call_some_api 杩斿洖鍘熷瀛楃涓?
raw = ai._call_ollama_sync('...')
obj = extract_json_from_text(raw)
if obj is None:
    # 璁板綍骞?鎴栬Е鍙戦噸璇曢€昏緫
    ai.logger.warn('鏃犳硶瑙ｆ瀽 AI 杩斿洖锛屽凡璁板綍鍘熸枃')
else:
    # 澶勭悊 obj
    pass
```

5. 鍗曞厓娴嬭瘯寤鸿锛堝繀鍋氶」锛?

- 涓?`extract_json_from_text` 缂栧啓娴嬭瘯鐢ㄤ緥锛?

  - 涓ユ牸 JSON
  - JSON 鍓嶅悗鍖呭惈璇存槑鏂囧瓧锛坋.g. "Answer:\n{...}"锛?
  - JSON 琚澶栫殑瑙ｉ噴鍖呭洿锛堟ā鍨嬪父瑙佽涓猴級
  - 瀹屽叏鏃犳晥鏂囨湰锛堝簲杩斿洖 None锛?

- 瀵?`AIService.evaluate_reading_answer` 鍐欓泦鎴愭祴璇曪細
  - 妯℃嫙妯″瀷杩斿洖涓ユ牸 JSON锛堟鏌ュ垎鏁?鍙嶉瑙ｆ瀽姝ｇ‘锛?
  - 妯℃嫙杩斿洖甯﹁В閲婄殑 JSON锛坋xtract_json 鑳芥娊鍙栵級
  - 妯℃嫙杩斿洖鏃犳硶瑙ｆ瀽鐨勬枃鏈紙妫€鏌ヤ唬鐮佽蛋鍒伴噸璇曚笌闄嶇骇鍒嗘敮骞惰褰曟棩蹇楋級

6. 鍦?UI 涓帴鍏ユ祦寮忚緭鍑猴紙灏忔彁绀猴級

- `core/ai_interface.py` 宸叉敮鎸佹祦寮忓洖璋冿細鍚屾/寮傛鐨?public 鏂规硶閮芥帴鍙楀彲閫?`callback(chunk: str, done: bool)` 鍙傛暟銆?
- 鍦?UI锛堝 `ui/translation_page.py` / 绀轰緥锛変腑锛屼紶鍏ヤ竴涓皢鎺ユ敹鍒嗗潡骞剁敤 `widget.after(0, update_ui)` 瀹夊叏璋冨害鍒颁富绾跨▼鐨勫洖璋冿紝鍗冲彲瀹炵幇瀹炴椂鏂囧瓧娴佸睍绀恒€?

绀轰緥锛?

```python
def on_chunk(chunk, done):
    # 鍦ㄤ富绾跨▼鏇存柊 UI锛堝鏋滃湪鍏朵粬绾跨▼锛岄渶瑕佷娇鐢?widget.after)
    text_widget.insert('end', chunk)
    if done:
        text_widget.insert('end', '\n--- 瀹屾垚 ---\n')

ai_manager.translate('璇风炕璇?..', callback=on_chunk)
```

---

璇峰闃呰琛ュ厖鍐呭銆傛垜鍙互锛?

- 鐩存帴鎶婅繖閮ㄥ垎鍚堝苟鍒?`DEVELOPER_DOCS.md`锛堟垜浼氬皾璇曚竴娆″悎骞跺苟鍛婄煡缁撴灉锛夛紱鎴?
- 濡傛灉浣犳効鎰忓厛瀹￠槄锛忎慨鏀癸紝鍐嶈鎴戝悎骞讹紝鎴戜細鏍规嵁浣犵殑鍙嶉杩涜鏇存柊銆?
