# LexiNote 更新日志

## v1.8.0 - 2025-11-01
### Changed
- 重构了听写功能，创建了独立的DictationManager类
- 优化了听写队列构建逻辑，支持从词库获取单词
- 改进了听写设置管理，统一使用SettingsManager接口
### Fixed
- 修复了'settings_manager.get_value'方法不存在的错误（替换为正确的get_setting方法）
- 修复了代码缩进问题
- 解决了词库关联问题，确保测试数据正确加载
- 修复了数据库表不存在的初始化问题

## v1.7.1 - 2025-10-31
### Fixed
- 修复单词练习页面例句点击功能无效问题：在main_window.py中为LearningPage实例化添加settings_manager参数

## v1.7.0 - 2025-10-31
### Changed
- 根据当前数据库结构重构了单词复习模块
- 在WordManager中新增了专用的get_words_for_review方法，直接从数据库获取复习单词
- 重构了update_word_familiarity方法，使用数据库中的proficiency字段进行熟悉度管理
- 优化了ReviewPage类，使用完整的单词数据，支持显示音标、英文解释等更多信息
- 改进了单词过滤逻辑，根据实际数据库字段进行过滤和排序
- 删除了临时测试脚本：test_ai_completion.py、test_ai_completion_fix.py、test_get_words.py、check_words.py、query_db.py，保持项目结构清晰

## v1.6.9 - 2025-10-31
### Fixed
- 修复单词复习模块中的数据库兼容性问题
- 优化update_word方法，增加列存在性检查，避免"no such column"错误
- 改进错误处理机制，提高系统稳定性

## [v1.6.8] - 2025-10-31
### Enhanced
- 完善离线模式选题功能，在离线状态下点击新题目时从离线题库随机读取且避免重复获取当前题目
- 提升用户体验，确保每次点击都能获得不同的练习内容

## [v1.6.7] - 2025-10-31
### Enhanced
- 优化阅读理解模块选择题格式，要求选项内容必须使用英文
- 增加学习挑战性，提升英语学习体验和语言环境沉浸感

## [v1.6.6] - 2025-10-31
### Fixed
- 修复阅读理解模块中的格式错误，解决"Invalid format specifier"异常问题
- 确保AI提示模板中的JSON格式正确解析，使阅读理解题目能够正常生成

## [v1.6.5] - 2025-10-31
### Enhanced
- 优化阅读理解模块AI提示模板，明确要求选择题和简答题必须包含具体题目内容
- 禁止AI使用'Question X'等占位符，确保生成的题目更加具体和有针对性
- 完善提示模板示例格式，提供更清晰的问题格式指导
### Fixed
- 修复了检查单词来源时出错：'Frame' object has no attribute 'show_page' 的错误，实现了正确的页面导航逻辑
- 修复了听写练习模块播放语音时显示单词的问题，现在只显示"已播放"状态而不显示单词内容，更符合听写初衷

## [v1.6.3] - 2025-10-25
### Fixed
- 修复了数据库批量写入日志显示问题：现在正确记录实际写入的记录数量

## [v1.6.2] - 2025-10-25
### Added
- 新增单词批量导入功能，支持从JSON文件批量导入单词到数据库
- 添加`modules/word_importer.py`模块，提供独立的单词导入功能
- 在`WordManager`类中添加`batch_import_words`方法，提供统一的批量导入接口
- 更新API文档，添加批量导入功能的详细说明

## [v1.6.1] - 2025-10-31
### Added
- 实现完形填空和阅读理解题目删除功能，包括确认对话框和删除日志记录
- 在数据库中添加delete_logs表，用于记录删除的题目数据以便恢复
### Fixed
- 修复scrollable_frame.py中Canvas.create_window方法的参数错误
- 修复cloze_test_page.py中缺少ttk导入的问题
- 修复main_window.py中ttk导入顺序问题
- 修复cloze_test_page.py中调用不存在的_on_options_configure方法的错误
- 修复删除按钮不响应问题，添加_current_mode属性正确跟踪实际使用的模式
### Changed
- 修改cloze_test_page.py中选项显示方式，改为水平排列并添加间距
- 在cloze_test.py和reading_comprehension.py中增强get_mode方法，准确反映当前实际使用的模式

## [v1.6.0] - 2025-10-29

### 新增功能
- 新增AI助手模块，提供智能英语学习辅助功能
- 支持8种学习任务类型：单词解释、语法讲解、写作批改、口语练习、阅读理解辅导、听力练习建议、词汇量测试、知识点总结
- 实现流式响应，提升用户体验
- 支持多种难度级别设置（初级、中级、高级）

### 优化改进
- 版本号更新为v1.6.0
- 更新开发文档，添加AI助手模块说明

## [v1.5.0] - 2025-10-31
### Added
- 创建通用滚动框架组件，统一管理滚动功能
- 模块级自动/手动控制（`auto_mode_word_learning`, `auto_mode_translation_practice`, `auto_mode_review`）。默认值为 `manual`。支持在运行时切换并立即生效。
- SettingsManager 支持监听器（`register_listener` / `unregister_listener`），用于通知 UI/模块在设置变更时即时响应。
### Changed
- 更新完形填空页面，添加选项区域滚动功能
- 更新阅读理解页面，添加内容区域滚动功能
- 更新翻译页面，添加主内容滚动功能
- 更新学习页面，添加单词卡片区域滚动功能
- 更新听写页面，添加主内容滚动功能
- 各 UI 页面（`ui/dictation_page.py`, `ui/translation_page.py`, `ui/review_page.py`）已注册并实现对对应 `auto_mode_*` 的回调，保证切换设置时实时更新 UI
### Fixed
- 修复页面内容超出屏幕显示范围时的挤压问题
- 确保所有页面在内容过多时可以正常滚动查看
- 修复AI连接测试中的超时问题
- 优化模型验证逻辑
- 改进JSON解析功能，支持代码块标记移除和字段名纠错

## v1.4.5 (2025-10-29)
- 修复听写队列长度控制问题，确保严格按照设置数量显示单词
- 改进 has_next_in_queue 方法，增加空队列检查以避免索引错误
- 修改 next_in_queue 方法，在返回单词前先检查队列是否存在和索引有效性
- 在_next_word_in_queue 方法中添加队列结束预检查，避免尝试获取第 11 个单词
- 更新_check_answer 方法中的队列结束判断逻辑，使用精确的索引比较
- 修改_skip_word 方法，增加队列结束检查以避免跳过后显示额外单词
- 移除了 build_queue 方法中的 limit-1 补丁，改回直接使用 limit 保证用户期望的单词数量
- 优化今日统计信息收集逻辑，使用 set 避免重复计数，确保 accuracy 计算准确
- 改进 current_queue_index 的计算方式，使用 min/max 保证数值在合理范围内

## v1.4.3 (2025-10-29)
- 实现超时单词影响权重功能，确保听写中超时的单词被视为未掌握
- 修复队列控制精度问题，确保设置的听写单词数量准确（如设置 10 个只听写 10 个）
- 在 dictation_page.py 中新增_handle_timeout 方法，专门处理单词超时情况
- 优化_skip_word 方法，确保跳过的单词正确影响权重
- 增强 Stop_timer 方法的健壮性，添加 hasattr 检查
- 确保所有单词失败场景（跳过、拼写错误、超时）统一影响权重计算
- 优化日志记录，提供更详细的学习情况追踪
- 修复 PEP8 代码规范问题，提高代码质量

## v1.4.2 (2025-10-29)
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

## v1.4.1 - 新增听写核心模块与学习功能增强
- 新增 core/dictation.py 核心模块，实现听写练习的底层逻辑
- 更新 core/learning.py，增强学习功能的实现
- 优化 ui/dictation_page.py，提升听写页面的用户体验
- 改进 ui/review_page.py，完善复习功能的展示
- 完善 WordManager 和 AIManager 方法文档
- 添加 AI 功能检测机制详细文档

## v1.4.0 - AI 功能初始化改进与听写前置检查
- 修复 WordManager 中调用不存在的`is_ai_available()`方法的问题
- 添加`_test_ai_connection()`方法实现 AI 连接可用性测试
- 改进 AI 功能初始化逻辑，确保即使 AI 初始化失败应用也能正常运行
- 优化错误处理和日志记录，提供更详细的 AI 功能状态信息
- 实现听写功能前置检查：用户当天必须学习过单词才能进入听写页面
- 在 main_window.py 中添加单词学习状态检查逻辑
- 优化用户体验，提供清晰的操作引导

## v1.3.4 - 页面继承与参数一致性修复
- 修复页面继承问题：让 DictationPage 和 ReviewPage 继承自 tk.Frame，确保所有页面类具有一致的继承结构
- 修复参数传递一致性：确保所有页面都接受 settings_manager 参数，使配置能正确传递
- 改进字体配置：为所有页面添加统一的默认字体配置
- 优化页面初始化逻辑：修复了 LearningPage 初始化中的参数重复问题
- 更新页面组件的父组件引用：确保所有子组件正确绑定到父框架

## v1.3.3 - 项目文件清理
- 移除了 6 个无用的测试文件，包括 test_ai_fallback.py、test_fix.py 等
- 删除了过时的设计文档文件：AI Integration Design Book.md 和 learning_mode_definition.md
- 保持项目结构清晰，移除冗余文件

## v1.3.2 - AI 翻译判断功能优化
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

## v1.3.1
- 修复了翻译判断逻辑中的错误
- 改进了同义词和特定单词处理
- 增强了日志记录功能

## v1.3.0
- 增强了翻译练习的用户反馈机制
- 添加了明确的对错提示信息，包含更详细的反馈内容
- 整合 AI 参考翻译功能，为英译汉提供补充参考
- 增加了结果显示的等待时间，提升用户体验
- 增强了翻译匹配算法，修复'diagram'等单词的翻译识别问题
- 添加了单词特定翻译映射，改进近义词识别
- 降低了字符匹配阈值，提高翻译识别准确率

## v1.2.0 (2025-10-27)
- 重大改进：英译汉模糊匹配算法重构
- 添加近义词识别功能，支持常见中文近义词映射
- 针对 minor 等特定单词的翻译识别优化
- 实现多维度匹配策略：完全匹配、近义词匹配、字符比例匹配、连续字符匹配
- 修复翻译检查函数潜在的 None 返回值 bug
- 优化短翻译的匹配逻辑，提高识别准确率
- 创建测试脚本 test_translation_matching.py 验证翻译匹配功能

## v1.1.6 (2025-10-30)
- 优化了例句生成和显示格式，去除繁杂内容，使例句更加简洁易读
- 修改了AI提示词，确保返回标准化的格式
- 添加了例句格式化处理，支持更清晰的中英文例句展示

## v1.1.5 (2025-10-30)
- 修复了LearningManager对象缺少current_index属性的错误，导致更新每日学习记录失败
- 优化了学习进度保存逻辑
- 修复了例句获取功能，现在在同步模式下也能从AI获取数据
  - 在 LearningManager 初始化时添加了 current_index 属性，初始值设为 -1
  - 优化了 AI 可用性检查逻辑，每次调用都重新验证 Ollama 服务状态
  - 修复了例句获取功能，现在在同步模式下也能从AI获取数据

## v1.1.1 - 修复 LearningManager 初始化依赖问题
- 修复 LearningManager 初始化依赖问题，解决 'WordManager' object has no attribute 'scheduler' 错误
- 改进依赖注入机制，使LearningManager能够正确使用WordManager提供的功能
- 优化 LearningPage 的 UI 加载逻辑
- 修复数据文件路径问题，确保正确读取和保存数据

## v1.1.0 - 新增理解练习模块与系统性能优化
### 新增功能模块
- 完整形填空模块
  - 创建了modules/cloze_test.py一个完整的形填空的核心控制器
  - 实现了在线（AI生成）和离线（数据库加载）两种模式
  - 添加了问题生成、回答问题和评估功能
  - 创建了ui/cloze_test_page.py作为用户界面
- 阅读理解模块
  - 创建了modules/reading_comprehension.py一个易于理解的核心控制器
  - 支持多选题和优势题的生成和评估
  - 实现了在线和离线模式
  - 创建了ui/reading_comprehension_page.py作为用户界面
- 数据库扩展
  - 创建了modules/database.py管理新功能的数据存储
  - 在现有中lexinote.db添加了cloze_tests和reading_comprehensions表
  - 实现了完整的 CRUD 操作
- 人工智能服务扩展
  - 创建了modules/ai_service.py处理新功能的人工智能交互
  - 实现了专门的提示词模板，用于生成问题测试和评估答案
- 题库门户管理
  - 创建了modules/portal_manager.py用于管理离线题库
  - 支持主题列表查看、删除、导出等功能
- UI集成
  - 在主窗口添加了完整的形填空和阅读理解的导航按钮
  - 实现了统一的页面切换和状态管理机制

### 系统性能优化
- 实现了基于 SQLite 的数据库存储系统，替代原有的 JSON 文件存储
- 添加了DatabaseManager类，提供高效的数据库操作接口
- 优化了DictationManager，支持数据库和文件存储的双模式切换
- 实现了 get_word_progress 方法，用于获取单词学习进度统计
- 设计了dictation_history和进度表结构，支持高效查询和更新
- 增加了内存服务器机制，减少数据库访问频率
- 实现了数据迁移功能，确保旧数据平滑过渡到新的存储模式
- 优化了错误处理和日志记录，提高系统稳定性

## v1.0.0 (2025-10-25)
### 基础功能
- 基础单词管理功能
- 翻译练习模式
- 听写练习模式
- 单词复习模式
- 简单的进度轨迹
