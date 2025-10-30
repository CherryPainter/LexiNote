# LexiNote 更新日志

## [v1.6.4] - 2025-10-30
### Fixed
- 修复了检查单词来源时出错：'Frame' object has no attribute 'show_page' 的错误，实现了正确的页面导航逻辑

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

## [v1.5.0] - 2025-10-29
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

## [v1.5.0] - 2025-10-31
### Fixed
- 修复AI连接测试中的超时问题
- 优化模型验证逻辑
- 改进JSON解析功能，支持代码块标记移除和字段名纠错

## v1.4.5 (2025-10-31)

- (历史条目保留于 DEVELOPER_DOCS.md)
