# AI 输出契约、JSON 解析与重试（补充说明）

为了让 AI 调用在真实运行中更稳定、可调试，项目遵循以下约定并提供了辅助工具：

1. 输出契约（推荐）

- 完形填空（生成）示例契约：

```json
{
  "id": "string",
  "content": "带占位符的题目文本，使用 [[_]] 或类似标记表示空",
  "blanks": [
    { "blank": 1, "options": ["选项A", "选项B", "选项C"], "answer": "选项A" },
    { "blank": 2, "options": ["选项X", "选项Y"], "answer": "选项Y" }
  ],
  "explanation": "(可选) 解析或示例答案"
}
```

- 阅读理解（主观题 AI 评估）示例契约：

```json
{
  "score": 0, // 整数 0-100
  "feedback": "简短反馈（适合 UI 显示）",
  "reason": "详细解释（可选）"
}
```

对选择题类的评估，也允许使用简单的 `{ "correct": true, "feedback": "..." }` 形态。

2. 解析工具

- 项目在 `modules/utils.py` 中提供 `extract_json_from_text(text)`：

  - 优先尝试直接 `json.loads`。
  - 若失败，会尝试从文本中抽取首个 JSON 对象（先非贪婪，再贪婪匹配）。
  - 返回解析后的 Python 对象或 `None`。

- 在 `modules/ai_service.py` 中对主观题评估调用做了两轮策略：
  1. 首次用常规 prompt 请求 AI 给出 JSON。若 `extract_json_from_text` 成功则继续。
  2. 若解析失败，向 AI 发送一次带有“只返回 JSON，不要任何解释或多余文字”的补充提示并重试一次。
  3. 若仍失败，记录原始 AI 返回到日志/缓存，并返回解析失败的容错结果（避免阻塞用户流程）。

3. 日志与审计

- 当解析失败时，代码会在日志中写入带标签的原始 AI 文本（如 `解析AI评估结果失败，原始返回:`），便于离线分析。
- 建议启用并保留 `cache/ai_text/` 目录（已在项目中预留），把失败或重要的 AI 原文保存为 JSON 文件供事后分析。

4. 开发者使用示例（同步/快速验证）

```python
from modules.utils import extract_json_from_text
from modules.ai_service import AIService

ai = AIService()

# 假定 ai.call_some_api 返回原始字符串
raw = ai._call_ollama_sync('...')
obj = extract_json_from_text(raw)
if obj is None:
    # 记录并/或触发重试逻辑
    ai.logger.warn('无法解析 AI 返回，已记录原文')
else:
    # 处理 obj
    pass
```

5. 单元测试建议（必做项）

- 为 `extract_json_from_text` 编写测试用例：

  - 严格 JSON
  - JSON 前后包含说明文字（e.g. "Answer:\n{...}"）
  - JSON 被额外的解释包围（模型常见行为）
  - 完全无效文本（应返回 None）

- 对 `AIService.evaluate_reading_answer` 写集成测试：
  - 模拟模型返回严格 JSON（检查分数/反馈解析正确）
  - 模拟返回带解释的 JSON（extract_json 能抽取）
  - 模拟返回无法解析的文本（检查代码走到重试与降级分支并记录日志）

6. 在 UI 中接入流式输出（小提示）

- `core/ai_interface.py` 已支持流式回调：同步/异步的 public 方法都接受可选 `callback(chunk: str, done: bool)` 参数。
- 在 UI（如 `ui/translation_page.py` / 示例）中，传入一个将接收分块并用 `widget.after(0, update_ui)` 安全调度到主线程的回调，即可实现实时文字流展示。

示例：

```python
def on_chunk(chunk, done):
    # 在主线程更新 UI（如果在其他线程，需要使用 widget.after)
    text_widget.insert('end', chunk)
    if done:
        text_widget.insert('end', '\n--- 完成 ---\n')

ai_manager.translate('请翻译...', callback=on_chunk)
```

---

请审阅该补充内容。我可以：

- 直接把这部分合并到 `DEVELOPER_DOCS.md`（我会尝试一次合并并告知结果）；或
- 如果你愿意先审阅／修改，再让我合并，我会根据你的反馈进行更新。
