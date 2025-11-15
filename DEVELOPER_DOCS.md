# 开发者文档

## 1. 项目说明
LexiNote 是一个个人英语学习工具，帮助用户管理单词表、学习单词和跟踪学习进度。

## 2. 版本历史

### v2.4.2 (2025-11-08)

### 1. 界面布局优化

- **统一滚动框架**：将整个完型填空内容区域（包括文章、选项、答案输入和结果显示）放入一个统一的滚动框架中，解决了元素挤压问题。
- **简化布局结构**：移除了选项区域的独立滚动框架，统一由外层滚动框架控制，提高了界面的一致性和可用性。

## v2.4.1 (2025-11-08)

### 1. 界面响应优化

- **后台线程初始化**：将完形填空页面的 ClozeTestModule 初始化移到后台线程，避免首次打开页面时因AI连接测试导致的UI阻塞，提升用户体验。
- **线程安全更新**：使用 `after(0, ...)` 方法确保UI更新在主线程中执行，避免线程安全问题。

### 2. AI服务优化

- **避免重复初始化**：优化了 AIService 的初始化流程，当传入 WordManager 实例时，直接使用其 AI 可用性检测结果，避免重复进行AI连接测试。
- **资源消耗减少**：减少了不必要的网络请求，降低了系统资源消耗，提高了启动速度。

### v2.4.0 - 2025-11-08
### 核心逻辑变更

#### 滚动组件优化
- **统一滚动框架实现**：将设置页面的自定义滚动实现替换为通用的 create_scrollable_frame 函数
- **增强鼠标滚轮支持**：为所有使用滚动框架的页面添加完整的鼠标滚轮支持
- **修复事件处理问题**：解决了子组件可能拦截鼠标滚轮事件的问题

#### 设置功能修复
- **修复重置设置错误**：将不存在的 _load_ai_models 方法调用改为正确的 _load_ai_models_async 方法
- **增强错误处理**：确保所有方法调用都有适当的存在性检查

### v2.1.0 - 2025-10-25
### 核心逻辑变更

#### 设置模块UI优化
- **异步加载AI模型**：将AI模型加载改为异步方式（使用after()延迟加载）
- **避免UI阻塞**：在加载AI模型时显示"加载中..."提示并禁用相关控件
- **提升用户体验**：防止因AI模型加载时间过长导致界面卡顿或无响应

#### 自动切换功能修复
- **修复方法调用错误**：将不存在的get_auto_mode()方法改为正确的get_setting()方法
- **统一设置获取方式**：翻译页面和复习页面使用相同的设置获取逻辑
- **删除重复代码**：清理复习页面中重复定义的_on_auto_mode_review_change方法

#### 翻译判定模式实现
- **添加translation_mode参数**：为WordManager.check_translation方法添加翻译判定模式参数
- **实现三种判断策略**：
  - ai_first：优先AI判断，失败后回退本地判断
  - local_first：优先本地判断，失败后尝试AI判断
  - local_only：仅使用本地判断，不调用AI
- **更新调用方式**：翻译页面传递当前设置的翻译判定模式给WordManager
- **修复显示错误**：根据实际使用的判断模式显示正确的文本描述

### v2.0.0 - 2025-11-18
- **翻译系统升级**：
  - **翻译数据结构优化**：将单词翻译从简单字符串升级为支持多词性多义项的结构化数据
  - **兼容性处理**：实现了同时支持旧格式(string)和新格式(array)的翻译处理逻辑
  - **展示模块更新**：
    - 修改了`get_translation`方法，添加`format_output`参数支持多种输出格式
    - 新增`_format_translation`方法，实现翻译格式的灵活转换
    - 确保UI各页面能正确显示新格式的翻译数据
  - **翻译判断模块更新**：
    - 更新`check_translation`方法，支持从多词性多义项结构中提取候选翻译
    - 优化翻译归一化处理，提高翻译判断的准确性
  - **AI补全模块更新**：
    - 更新`get_word_details`方法的提示词，要求AI返回结构化的中文释义
    - 在`ai_complete_word_details`方法中添加中文释义处理逻辑，转换为多词性多义项结构
  - **数据库管理更新**：
    - 扩展`get_word_translation`方法的返回类型，支持字符串和列表字典结构
    - 添加JSON格式解析逻辑，处理新的翻译结构
  - **旧数据迁移**：
    - 新增`migrate_old_translations`方法，实现旧格式翻译数据的自动转换
    - 支持将现有的字符串格式翻译拆分为结构化的多词性多义项数据
  - **测试与验证**：
    - 创建`test_translation_system.py`测试脚本，验证所有模块的兼容性和协调性
    - 确保新旧格式数据的无缝转换和处理
  - **API兼容性**：保持原有API接口不变，确保向后兼容

- **AI模型切换功能**：
  - **SettingsManager扩展**：添加了AI模型相关设置的管理功能
    - 新增`get_ai_model`和`set_ai_model`方法，用于获取和设置当前使用的AI模型
    - 新增`get_available_ai_models`和`set_available_ai_models`方法，用于管理可用AI模型列表
    - 在默认设置中添加了`ai_model`和`available_ai_models`字段
  - **AIManager增强**：支持动态切换模型功能
    - 新增`set_model`方法，用于动态切换AI模型
    - 新增`_is_model_available`方法，用于测试模型可用性
    - 修改初始化方法，支持从SettingsManager获取当前设置的模型
  - **设置页面重设计**：添加AI模型切换UI界面
    - 新增AI模型设置标签页
    - 实现模型选择下拉框，显示可用的Ollama模型
    - 添加模型管理按钮：添加模型、测试模型、刷新模型列表
    - 支持用户添加自定义Ollama模型并测试可用性
  - **功能特性**：
    - 自动检测本地Ollama服务中的可用模型
    - 支持用户手动添加和测试Ollama模型
    - 实时更新模型选择列表
    - 模型切换后立即生效，无需重启应用

### v1.11.2 - 2025-11-17
- **系统性能与资源优化**：
  - **日志执行逻辑优化**：修改了main_window.py及各页面的显示逻辑，确保页面切换日志按照实际执行顺序记录，提高日志可读性和调试效率
  - **AIManager单例实现**：重构了ai_manager.py，实现单例模式，避免重复初始化AI管理器，减少资源消耗和初始化时间
  - **模块冗余初始化修复**：
    - 更新了AIService类构造函数，支持接受外部WordManager实例
    - 修改了AI助手、阅读理解和完形填空模块，使其共享主窗口的WordManager实例
    - 实现了模块间资源共享，提高了系统整体性能
  - **AI连接测试优化**：
    - 改进了_is_ai_available和_test_ai_connection方法，优先使用WordManager的AI可用性检测结果
    - 避免重复测试AI连接，减少不必要的网络请求和延迟
    - 修复了"AI服务连接测试成功"重复出现的问题，确保日志记录准确
  - **代码结构优化**：
    - 增强了模块间的依赖注入机制
    - 提高了代码的可维护性和扩展性
    - 确保了AI服务的一致性和可靠性

### v1.11.1 - 2025-11-16
- **文本格式化修复**：
  - 修复了文本格式化中的星号(*)显示问题
  - 增强了列表处理，确保无序列表标记正确替换为•符号
  - 改进了行内格式处理，分离粗体和斜体的处理逻辑
  - 新增星号清理机制，移除残留的多余星号
  - 优化了格式化流程，避免格式冲突和遗漏
  - 重构了TextFormatter类的实现，提高了代码可维护性

### v1.11.0 - 2025-11-15
- **学习统计页面重写**：
  - 创建了 `ui/statistics_page.py` 文件，实现了 `StatisticsPage` 类，提供全新的学习统计页面
  - 添加了综合统计卡片，展示已学单词、总练习次数、正确率、学习天数等关键指标
  - 实现了本周学习趋势图表，直观展示每日学习情况
  - 添加了熟练度分布图表，可视化不同掌握程度的单词比例
  - 新增词库统计和最近学习记录展示功能
  - 重写了 `ui/main_window.py` 中的 `_show_statistics` 方法，使用新的 `StatisticsPage` 类替代原有实现
  - 采用页面缓存机制，提高统计页面切换效率
  - 修复了图表绘制问题，确保数据可视化的准确性

### v1.13.0 - 2025-11-17
- **词库管理模块AI补全功能改进**:
  - 修改了`get_words_missing_details`方法，增加了对`example_translation`字段的检查
  - 优化了`ai_complete_word_details`方法，确保只有当`example_translation`缺失时才会更新该字段
  - 提高了AI补全功能的准确性和完整性
  - 修复了之前AI补全功能可能导致的权限问题

### v1.10.0 - 2025-11-14
- **全新统计模块**：
  - 创建了 `statistics.py` 文件，实现了 `StatisticsManager` 类
  - 提供了全面的学习统计功能：基本统计、每日统计、每周统计、熟练度分布统计、词库统计、最近进度记录、综合统计
  - 更新了 `WordManager` 类，使其使用新的统计模块
  - 确保了数据统计的准确性和一致性

### v1.9.0 - 2025-11-13
- **学习批次管理增强**: 
  - 在LearningManager类中新增adjust_batch_size方法，支持动态调整学习批次大小
  - 实现了批次扩展功能：可以在现有批次基础上添加新单词
  - 实现了批次缩减功能：可以减少当前批次的单词数量
  - 确保调整后保持学习进度（当前索引、掌握和复习计数）
  - 新单词选择算法：优先选择掌握度低的单词，避免重复选择

### v1.8.0 - 2025-11-01
- **听写功能重构**: 
  - 创建了独立的DictationManager类，专门负责听写功能的管理
  - 优化了听写队列构建逻辑，支持从词库获取单词
  - 改进了听写设置管理，统一使用SettingsManager接口
- **Bug修复**: 
  - 修复了'settings_manager.get_value'方法不存在的错误（替换为正确的get_setting方法）
  - 修复了代码缩进问题
  - 解决了词库关联问题，确保测试数据正确加载
  - 修复了数据库表不存在的初始化问题

### v1.7.1 - 2025-10-31
- **Bug修复**: 
  - 修复单词练习页面例句点击功能无效问题：在main_window.py中为LearningPage实例化添加settings_manager参数

### v1.7.0 - 2025-11-13
- **功能增强**: 
  - AI补全单词属性功能增加了例句翻译字段(example_translation)
  - 修复了AI补全按钮显示"没有需要补全的"的问题
- **数据库更新**: 
  - 在words表中添加了example_translation字段
  - 更新了数据库迁移逻辑以支持新字段
  - 在update_word方法中添加了example_translation到valid_fields列表
- **AI响应解析改进**: 
  - 增强了JSON解析逻辑，处理转义下划线等特殊字符
  - 优化了AI响应提取流程，提高解析成功率
- **测试改进**: 创建了AI补全功能测试脚本，验证所有属性的完整性
- **Bug修复**: 
  - 修复了`get_words_missing_details`方法只检查空字符串而不检查NULL值的问题
  - 更新了SQL查询条件，同时检查NULL值和空字符串以正确识别需要补全的单词
  - 修复了ai_complete_word_details方法中只检查空字符串而忽略NULL值的问题，确保补全的单词信息能正确存入数据库
- **日志系统重构**: 将logger.py从函数式设计重构为面向对象设计，创建Logger类，保留原有函数接口以确保兼容性，提高代码可维护性和扩展性

### v1.1.0 - 2025-11-13
- **重构单词学习模块**：将 LearningManager 拆分为多个独立组件，提高代码可维护性
- **新增组件**：
  - ForgettingCurve：实现艾宾浩斯遗忘曲线算法
  - WordSelector：负责单词选择和批次生成
  - LearningProgress：管理学习进度和统计信息
  - LearningScheduler：处理学习计划和调度
- **优化API**：简化 LearningManager 的初始化和方法调用
- **改进UI交互**：确保 LearningPage 与重构后的 API 兼容

### v1.0.0 - 初始版本
- 实现基本的单词管理功能
- 支持学习模式和测试模式
- 提供单词发音和例句功能
- 支持学习进度跟踪

## 3. 项目结构

```
LexiNote/
├── main.py              # 程序入口
├── word_manager.py      # 单词管理核心逻辑
├── audio_player.py      # 音频播放模块
├── audio_cache.py       # 音频缓存管理
├── logger.py            # 日志记录模块
├── statistics.py        # 统计功能模块
├── app.ico              # 应用程序图标
├── core/                # 核心功能模块
│   ├── ai_interface.py  # AI接口管理
│   ├── database_manager.py # 数据库管理
│   ├── learning.py      # 学习逻辑模块
│   ├── cache_manager.py # 缓存管理
│   ├── settings_manager.py # 设置管理
│   ├── dictation.py     # 听写核心逻辑
│   └── text_formatter.py # 文本格式化工具
├── modules/             # 功能模块
│   ├── ai_service.py    # AI服务
│   ├── cloze_test.py    # 完形填空模块
│   ├── database.py      # 数据库操作
│   ├── portal_manager.py # 题库门户管理
│   ├── reading_comprehension.py # 阅读理解模块
│   ├── utils.py         # 工具函数
│   └── word_importer.py # 单词导入工具
├── ui/                  # 用户界面
│   ├── main_window.py   # 主窗口
│   ├── dictation_page.py # 听写练习页面
│   ├── translation_page.py # 翻译练习页面
│   ├── review_page.py   # 单词复习页面
│   ├── learning_page.py # 学习模式页面
│   ├── settings_page.py # 设置页面
│   ├── ai_assistant_page.py # AI英语助手页面
│   ├── statistics_page.py # 学习统计页面
│   ├── cloze_test_page.py # 完形填空页面
│   ├── reading_comprehension_page.py # 阅读理解页面
│   ├── word_set_page.py # 词库管理页面
│   └── components/      # UI组件
│       ├── loading_dialog.py # 加载对话框组件
│       └── scrollable_frame.py # 滚动框架组件
├── data/                # 数据文件目录
│   ├── lexinote.db      # SQLite数据库文件
│   └── logs/            # 日志文件目录
├── requirements.txt     # 依赖列表
├── README.md            # 项目说明
├── API_DOCUMENTATION.md # API文档
├── CHANGELOG.md         # 更新日志
├── CONTRIBUTING.md      # 贡献指南
├── DEVELOPER_DOCS.md    # 开发者文档
├── SETTINGS.md          # 设置说明
└── TESTS.md             # 测试说明
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

#### 核心API
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

#### 核心API
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

#### 4.3.1 AI接口模块 (core/ai_interface.py)
- 管理与AI服务的交互
- 提供统一的AI接口（翻译、语音合成等）
- 处理AI请求和响应

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

#### 4.4.1 AI服务模块 (modules/ai_service.py)
- 提供AI翻译、语法分析等服务
- 实现与外部AI服务的集成

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

| 表名 | 描述 |
|------|------|
| word_sets | 词库信息表 |
| words | 单词表 |
| progress | 学习进度表 |
| settings | 设置表 |
| ai_cache | AI 缓存表 |
| cloze_tests | 完形填空表 |
| reading_comprehensions | 阅读理解表 |
| delete_logs | 删除日志表 |
| dictation_sessions | 听写会话表 |
| exercise_sessions | 练习会话表 |

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
   - 无外键关联，独立存储AI缓存数据
   - 描述：存储AI请求和响应的缓存，提高性能

### 8.4 数据访问

所有数据库操作都通过以下模块进行：

1. **core/database_manager.py**: 主要的数据库管理器，负责单词管理相关的数据库操作
2. **modules/database.py**: 理解类练习（完形填空、阅读理解）的数据库操作

### 8.5 版本迁移

系统会自动检测数据库版本并进行必要的迁移，包括：
- 为旧版本单词表添加 `set_id` 列并关联到默认词库
- 添加新的字段（如 `phonetic`, `example`, `meaning_en`, `tag`, `example_translation`）
- 创建必要的索引以提高查询性能

## 9. 未来计划

- 增加更多学习模式（如拼写练习、听力练习）
- 改进遗忘曲线算法
- 支持单词分类和标签
- 增强学习统计功能，添加更多图表类型和数据维度
