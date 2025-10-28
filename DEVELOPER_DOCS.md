# 开发者文档

## 版本历史

### v1.4.5 (2025-10-31)
- 修复听写队列大小控制问题，确保严格按照设置的数量显示单词
- 改进has_next_in_queue方法，增加空队列检查以避免索引错误
- 修改dictation_page中的队列结束判断逻辑，使用精确的索引比较
- 在build_queue方法最后增加额外的队列长度限制，确保不会返回超过指定数量的单词

### v1.4.3 (2025-10-30)

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

### v1.1.0 (2025-10-26)

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
