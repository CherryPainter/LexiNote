# 应用设置说明（SETTINGS.md）

本文档列出项目中常用的设置键、默认值、说明与生效时机，便于用户和开发者理解设置的影响范围。

## 常用设置键与默认值

- `auto_mode_word_learning`: `"manual"`

  - 说明：单词学习模块的模式，取值为 `"manual"` 或 `"auto"`。
  - 生效：实时生效（注册监听器的页面会立即响应）。

- `auto_mode_translation_practice`: `"manual"`

  - 说明：翻译练习模块的模式，取值为 `"manual"` 或 `"auto"`。
  - 生效：实时生效。

- `auto_mode_review`: `"manual"`

  - 说明：复习模块的模式，取值为 `"manual"` 或 `"auto"`。
  - 生效：实时生效。

- `auto_next_correct`: `False`

  - 说明：答对时是否自动跳到下一个（前提模块为 `auto` 或模块允许自动跳转）。
  - 生效：实时。

- `auto_next_wrong`: `False`

  - 说明：答错时是否自动跳到下一个。
  - 生效：实时。

- `auto_next_delay`: `1000`（毫秒）

  - 说明：自动跳转的延迟时间（毫秒）。
  - 生效：实时。

- `auto_next_example`: `False`
  - 说明：在复习页面中，例句显示后是否自动跳到下一个单词（与 `auto_mode_review` 配合）。
  - 生效：实时。

- `auto_next_familiar`: `False`
  - 说明：熟悉单词自动跳到下一个。
  - 生效：实时。

- `auto_next_difficult`: `False`
  - 说明：困难单词自动跳到下一个。
  - 生效：实时。

## 界面与显示设置

- `example_enabled`: `True` - 是否在练习中显示例句。
- `voice_enabled`: `True` - 是否启用语音发音功能。
- `voice_speed`: `1.0` - 发音速度调整（范围：0.5-3.0）。
- `dark_mode`: `False` - 是否启用深色模式。

## 语音合成设置

- `tts_provider`: `"gTTS"` - 语音合成提供商（目前仅支持 "gTTS"）。
- `tts_cache_enabled`: `True` - 是否启用语音缓存。
- `tts_cache_max_mb`: `500` - 语音缓存最大容量（MB）。

## 功能与性能设置

- `translation_mode`: `"ai_first"` - 翻译判定模式，取值为：
  - `"ai_first"`: 优先使用AI翻译
  - `"local_first"`: 优先使用本地翻译
  - `"local_only"`: 仅使用本地翻译

- `log_level`: `"INFO"` - 日志等级，取值为：
  - `"DEBUG"`: 调试模式，显示所有日志
  - `"INFO"`: 信息模式，显示正常信息和错误
  - `"ERROR"`: 错误模式，仅显示错误信息

## AI 模型设置

- `ai_model`: `"gemma3n:latest"` - 当前使用的AI模型名称（默认使用gemma3n:latest）。
  - 说明：指定应用使用的Ollama模型
  - 生效：实时生效，模型切换后立即应用

- `available_ai_models`: `[]` - 可用的AI模型列表。
  - 说明：存储用户手动添加的可用Ollama模型
  - 生效：实时生效，用于设置页面的模型选择下拉框

- `ai_summary_enabled`: `True` - 是否启用听写AI总结功能。
  - 说明：控制是否在听写练习后生成AI总结
  - 生效：实时生效，设置变更后立即应用

## 通过 SettingsManager 编程修改设置

示例：

```python
from core.settings_manager import SettingsManager

sm = SettingsManager()
# 修改翻译模块为自动模式
sm.set_auto_mode('translation_practice', 'auto')

# 或者直接通过 key 修改
sm.set_setting('auto_next_delay', 1500)
```

设置修改会触发已注册的监听器（若有），监听器应负责把设置变更映射到 UI 行为（显示/隐藏按钮、启动/取消定时器）。

## 生效注意事项（开发者）

- 监听器回调应尽量轻量，避免在回调中执行阻塞 I/O。
- 当回调需要访问 tkinter 组件时，使用 `widget.after(0, func)` 将操作调度回主线程。
- 页面在销毁前需要注销已注册监听器以避免对已销毁组件的回调。

## 常见问题

- Q: 我修改了设置但页面没有变化？
  - A: 请确保页面在初始化时已注册监听器，或在手动修改设置后刷新页面状态（读取当前设置并更新 UI）。
