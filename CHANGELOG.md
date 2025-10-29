# CHANGELOG

## Unreleased

## [v1.6.0] - 2025-10-29
### Added
- 创建通用滚动框架组件，统一管理滚动功能
### Changed
- 更新完形填空页面，添加选项区域滚动功能
- 更新阅读理解页面，添加内容区域滚动功能
- 更新翻译页面，添加主内容滚动功能
- 更新学习页面，添加单词卡片区域滚动功能
- 更新听写页面，添加主内容滚动功能
### Fixed
- 修复页面内容超出屏幕显示范围时的挤压问题
- 确保所有页面在内容过多时可以正常滚动查看

- Feature: 模块级自动/手动控制（`auto_mode_word_learning`, `auto_mode_translation_practice`, `auto_mode_review`）。默认值为 `manual`。支持在运行时切换并立即生效。
- Feature: SettingsManager 支持监听器（`register_listener` / `unregister_listener`），用于通知 UI/模块在设置变更时即时响应。
- Fix: 各 UI 页面（`ui/dictation_page.py`, `ui/translation_page.py`, `ui/review_page.py`）已注册并实现对对应 `auto_mode_*` 的回调，保证切换设置时实时更新 UI（显示/隐藏下一步按钮、触发延迟自动跳转等）。
- Docs: 新增 `SETTINGS.md`, `TESTS.md`, 更新 `API_DOCUMENTATION.md`, `DEVELOPER_DOCS.md` 与 `README.md`，说明运行时设置生效与监听器使用方法。

## [v1.6.0] - 2025-10-31
### Fixed
- 修复控制台日志重复打印问题
- 增强logger模块，避免重复添加处理器

## [v1.5.0] - 2025-10-31
### Fixed
- 修复AI连接测试中的超时问题
- 优化模型验证逻辑
- 改进JSON解析功能，支持代码块标记移除和字段名纠错

## v1.4.5 (2025-10-31)

- (历史条目保留于 DEVELOPER_DOCS.md)
