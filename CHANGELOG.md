# CHANGELOG

## Unreleased

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

## [v1.6.0] - 2025-10-31
### Fixed
- 修复控制台日志重复打印问题
- 增强logger模块，避免重复添加处理器

### Changed
- 优化导航模块，实现页面懒加载和延迟初始化，解决切换模块时的卡顿问题

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
