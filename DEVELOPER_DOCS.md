# 开发者文档

## 版本历史

### v1.4.0 - AI功能初始化改进与听写前置检查
- 修复WordManager中调用不存在的`is_ai_available()`方法的问题
- 添加`_test_ai_connection()`方法实现AI连接可用性测试
- 改进AI功能初始化逻辑，确保即使AI初始化失败应用也能正常运行
- 优化错误处理和日志记录，提供更详细的AI功能状态信息
- 实现听写功能前置检查：用户当天必须学习过单词才能进入听写页面
- 在main_window.py中添加单词学习状态检查逻辑
- 优化用户体验，提供清晰的操作引导

### v1.3.4 - 页面继承与参数一致性修复
- 修复页面继承问题：让DictationPage和ReviewPage继承自tk.Frame，确保所有页面类具有一致的继承结构
- 修复参数传递一致性：确保所有页面都接受settings_manager参数，使配置能正确传递
- 改进字体配置：为所有页面添加统一的默认字体配置
- 优化页面初始化逻辑：修复了LearningPage初始化中的参数重复问题
- 更新页面组件的父组件引用：确保所有子组件正确绑定到父框架

### v1.3.3 - 项目文件清理
- 移除了6个无用的测试文件，包括test_ai_fallback.py、test_fix.py等
- 删除了过时的设计文档文件：AI Integration Design Book.md和learning_mode_definition.md
- 保持项目结构清晰，移除冗余文件

### v1.3.2 - AI翻译判断功能优化
- 完全实现翻译判断功能交由AI处理
- 优化了AI管理器的初始化逻辑，实现延迟加载机制
- 改进了错误处理，确保AI调用失败时有备用逻辑
- 增强了翻译结果展示，包括视觉反馈和AI参考翻译
- 优化了翻译判断的提示词工程
- 修复了重复返回语句问题
- 为所有翻译方向（英译中/中译英）提供AI参考翻译
- 优化了跳过功能，为跳过的单词也提供AI翻译参考
- 延长了结果显示时间，提升学习体验
- 改进了错误处理和日志记录

### v1.3.1
- 修复了翻译判断逻辑中的错误
- 改进了同义词和特定单词处理
- 增强了日志记录功能

### v1.3.0
- 增强了翻译练习的用户反馈机制
- 添加了明确的对错提示信息，包含更详细的反馈内容
- 整合AI参考翻译功能，为英译汉提供补充参考
- 增加了结果显示的等待时间，提升用户体验
- 增强了翻译匹配算法，修复'diagram'等单词的翻译识别问题
- 添加了单词特定翻译映射，改进近义词识别
- 降低了字符匹配阈值，提高翻译识别准确率

### v1.2.0 (2025-10-27)
- 重大改进：英译汉模糊匹配算法重构
- 添加近义词识别功能，支持常见中文近义词映射
- 针对minor等特定单词的翻译识别优化
- 实现多维度匹配策略：完全匹配、近义词匹配、字符比例匹配、连续字符匹配
- 修复翻译检查函数潜在的None返回值bug
- 优化短翻译的匹配逻辑，提高识别准确率
- 创建测试脚本test_translation_matching.py验证翻译匹配功能

### v1.1.4 (2025-10-26)
- 修复LearningManager中的get_word_definition方法，确保正确获取单词释义
- 解决GUI无法显示单词学习内容的问题
- 在main_window.py中添加了pack(fill=tk.BOTH, expand=True)使LearningPage正确显示
- 修复AttributeError: 'WordManager' object has no attribute 'scheduler'错误

### v1.1.1 (2025-10-26)
- 修复LearningManager初始化依赖问题，解决'WordManager' object has no attribute 'scheduler'错误
- 改进依赖注入机制，使LearningManager能正确使用WordManager提供的功能
- 优化LearningPage的UI加载逻辑
- 修复数据文件路径问题，确保正确读取和保存数据

### v1.1.0 (2025-10-26)
- 集成AI功能（使用gemma:7b模型）
- 添加翻译、例句生成、拼写评估功能
- 实现AI功能降级服务
- 添加用户学习建议生成功能
- 集成本地AI功能，通过requests直接调用Ollama API
- 创建 core/ai_interface.py 实现AIManager类
- 添加学习模式功能，实现主动单词记忆
- 创建 core/learning.py 核心逻辑模块
- 创建 ui/learning_page.py 用户界面模块
- 新增 word_progress.json 数据文件存储学习进度
- 实现基于掌握度的权重调整算法
- 更新主界面导航菜单，优化用户体验
- 创建test_ai_fallback.py测试脚本验证降级机制

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
  - `get_random_word()`：获取随机单词进行练习
  - `check_translation(word, user_translation, update_stats)`：检查翻译正确性并更新学习统计
  - `translate_text(text, mode)`：翻译文本（英→中/中→英）
  - `update_word_progress(word, is_correct)`：更新单词学习进度
  - `save_progress()`：保存学习进度到文件
  - `_init_ai_manager()`：初始化AI管理器（延迟加载）
  - `_test_ai_connection()`：测试AI连接是否可用
  - `get_today_learned_words()`：获取今日学习的单词列表
- **设计特点**：
  - 作为UI和AI功能之间的桥梁
  - 从v1.3.2版本开始完全使用AI进行翻译判断
  - 实现了延迟加载AIManager的机制，提高启动效率
  - 包含完善的错误处理和日志记录
  - v1.4.0版本改进了AI连接测试机制，确保准确判断AI功能可用性

#### AIManager (core/ai_interface.py)
- **职责**：封装Ollama API调用，提供AI相关功能
- **主要方法**：
  - `translate(text, mode)`：翻译文本
  - `generate_text(prompt)`：生成文本内容
  - `check_translation(expected, user_input, is_english_to_chinese)`：判断翻译是否正确
  - `generate_example(word)`：为单词生成例句
  - `evaluate_spelling(word, user_input)`：评估拼写准确性
- **设计特点**：
  - 使用requests直接调用Ollama API，不依赖ollama模块
  - 实现错误处理和降级服务机制
  - 封装提示词工程，优化AI输出质量

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

1. **UI层到逻辑层**：
   - 用户操作触发UI事件
   - UI调用WordManager提供的方法
   - WordManager根据需要调用AIManager或LearningManager

2. **逻辑层到数据层**：
   - WordManager读写单词库和学习进度
   - LearningManager读写用户学习记录
   - 所有数据操作遵循先读再写的原则，避免覆盖数据

3. **数据层到UI层**：
   - WordManager将处理结果返回给UI
   - UI根据返回结果更新界面展示
   - 错误信息通过日志记录并在UI适当位置提示用户

### 开发环境设置

#### 必要依赖
- Python 3.12+
- 依赖库：见requirements.txt
- Ollama服务（用于AI功能）

#### 开发流程
1. 克隆仓库：`git clone https://github.com/CherryPainter/LexiNote.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 确保Ollama服务正在运行（默认端口11434）
4. 运行程序：`python main.py`



## AI翻译判断说明

从v1.3.2版本开始，翻译判断功能完全交由AI处理，具有以下特点：

1. **AI优先判断**：系统默认使用AI来判断翻译的正确性，提供更准确、更智能的判断结果
2. **双向支持**：同时支持英译中和中译英的AI判断
3. **备用机制**：当AI服务不可用时，系统会自动回退到原有的匹配逻辑
4. **视觉反馈**：判断结果会通过醒目的颜色和背景闪烁提供清晰的视觉提示
5. **AI参考翻译**：无论翻译是否正确，都提供AI的参考翻译，帮助用户更好地学习
6. **状态显示**：在状态栏显示当前的判断方式（AI或系统），保持透明度

### 提示词工程

系统使用精心设计的提示词来确保AI判断的准确性：
- 明确的任务指令（判断翻译是否正确）
- 提供原始词语和用户翻译
- 要求简洁的二选一回答（正确/错误）
- 避免添加额外解释，确保结果易于解析

### 错误处理

所有AI调用都包含完善的错误处理机制：
- 捕获所有可能的异常，确保程序稳定运行
- 记录详细的错误日志，便于排查问题
- 自动回退到备用逻辑，保证功能可用性

#### AIManager
- 封装Ollama API调用
- 提供翻译、例句生成、拼写评估等功能
- 实现错误处理和降级服务

#### 学习模式
- 基于记忆曲线的学习算法
- 个性化的学习进度跟踪
- 智能的单词推荐系统

## 开发规范

### 代码规范
- 遵循PEP8编码规范
- 类名使用PascalCase
- 函数名和变量名使用小写+下划线
- 为所有公共函数添加文档字符串

### 数据存储
- 所有用户数据统一保存在data/目录下
- 使用JSON格式存储数据
- 写入前先读取并合并旧数据，避免覆盖

### 错误处理
- 所有用户输入和外部调用需try/except捕获
- 重要操作都写入logger.py记录
- 不要在AI逻辑中直接exit()程序

### 版本控制
- 使用git进行版本控制
- 每次重大修改更新版本号：v1.0.0 → v1.1.0
- 所有核心逻辑变更记录在DEVELOPER_DOCS.md