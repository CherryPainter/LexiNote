# 开发者文档

## 1. 项目概述
LexiNote 是一个个人英语学习工具，帮助用户管理单词库、学习单词和跟踪学习进度。

## 2. 版本历史

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
├── core/                # 核心功能模块
│   ├── ai_interface.py  # AI接口管理
│   ├── database_manager.py # 数据库管理
│   ├── learning.py      # 学习逻辑模块
│   ├── cache_manager.py # 缓存管理
│   ├── settings_manager.py # 设置管理
│   └── dictation.py     # 听写核心逻辑
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
│   └── components/      # UI组件
├── data/                # 数据文件目录
│   └── lexinote.db      # SQLite数据库文件
├── cache/               # 缓存目录
│   ├── ai_text/         # AI文本缓存
│   ├── ai_tts/          # AI语音缓存
│   └── audio/           # 音频缓存
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

## 8. 未来计划

- 增加更多学习模式（如拼写练习、听力练习）
- 改进遗忘曲线算法
- 支持单词分类和标签
- 增强学习统计功能，添加更多图表类型和数据维度
