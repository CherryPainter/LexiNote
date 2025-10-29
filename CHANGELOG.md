# CHANGELOG

## Unreleased

- Feature: 模块级自动/手动控制（`auto_mode_word_learning`, `auto_mode_translation_practice`, `auto_mode_review`）。默认值为 `manual`。支持在运行时切换并立即生效。
- Feature: SettingsManager 支持监听器（`register_listener` / `unregister_listener`），用于通知 UI/模块在设置变更时即时响应。
- Fix: 各 UI 页面（`ui/dictation_page.py`, `ui/translation_page.py`, `ui/review_page.py`）已注册并实现对对应 `auto_mode_*` 的回调，保证切换设置时实时更新 UI（显示/隐藏下一步按钮、触发延迟自动跳转等）。
- Docs: 新增 `SETTINGS.md`, `TESTS.md`, 更新 `API_DOCUMENTATION.md`, `DEVELOPER_DOCS.md` 与 `README.md`，说明运行时设置生效与监听器使用方法。

## v1.4.5 (2025-10-31)

- (历史条目保留于 DEVELOPER_DOCS.md)
