# 贡献指南

感谢您有兴趣为 LexiNote 项目贡献代码！本指南将帮助您了解如何参与项目开发、提交代码和解决问题。

## 目录

- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [分支管理](#分支管理)
- [Issue 和 Pull Request 流程](#issue和pull-request流程)
- [测试指南](#测试指南)
- [文档更新](#文档更新)

## 开发环境设置

### 必要依赖

- Python 3.12+
- git
- Ollama（用于 AI 功能测试）

### 安装步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/CherryPainter/LexiNote.git
   cd LexiNote
   ```

2. **创建虚拟环境（推荐）**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装开发依赖**

   ```bash
   pip install -r requirements.txt
   pip install flake8 pytest
   ```

4. **配置 Ollama**
   - 下载并安装 [Ollama](https://ollama.com/download)
   - 拉取所需模型：`ollama pull gemma3n:latest`
   - 确保 Ollama 服务在默认端口(11434)运行

## 代码规范

请严格遵守以下代码规范：

### PEP8 规范

- 使用 4 个空格进行缩进，不使用 Tab
- 行长度不超过 79 个字符
- 导入语句分组：标准库、第三方库、项目本地模块
- 类名使用 PascalCase
- 函数名和变量名使用小写+下划线
- 常量使用全大写+下划线

### 文档字符串

所有公共函数和类都必须包含文档字符串，遵循以下格式：

```python
def function_name(param1, param2):
    """函数功能描述

    Args:
        param1: 参数1的说明
        param2: 参数2的说明

    Returns:
        返回值的说明

    Raises:
        可能抛出的异常及其情况
    """
```

### 模块独立性

- 每个文件必须只做一件事
- UI 和逻辑层必须分离，不允许在 UI 文件中直接调用 AI 逻辑
- 所有 AI 调用都必须通过 WordManager 接口

### 数据管理

- 所有用户数据统一保存在数据库中，通过 DatabaseManager 接口访问
- 设置数据通过 SettingsManager 接口管理，支持实时生效和缓存机制
- 音频缓存通过 AudioCache 接口管理，支持自动清理过期缓存
- 使用相对路径访问数据文件，确保跨平台兼容性

### 错误处理

- 所有用户输入和外部调用需 try/except 捕获
- 不要在 AI 逻辑中直接 exit()程序
- 所有重要操作写入 logger.py 记录

## 提交规范

### 提交信息格式

```
<类型>: <简短描述>

[可选的详细描述]

Related to #<Issue编号>
```

### 提交类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式修改（不影响功能）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 示例

```
feat: 实现AI翻译判断功能

使用Ollama API实现智能翻译判断，包括：
1. 英译中和中译英双向支持
2. AI参考翻译展示
3. 失败自动回退机制

Related to #42
```

## 分支管理

- **main**: 主分支，稳定版本
- **develop**: 开发分支，包含最新开发功能
- **feature/\***: 新功能分支
- **fix/\***: Bug 修复分支
- **docs/\***: 文档更新分支

### 分支命名示例

- `feature/ai-translation`
- `fix/spelling-check`
- `docs/api-documentation`

## Issue 和 Pull Request 流程

### 创建 Issue

1. 搜索现有 Issue，避免重复
2. 选择合适的 Issue 模板
3. 清晰描述问题或功能请求
4. 添加适当的标签

### 提交 Pull Request

1. 从 develop 分支创建功能分支
2. 实现功能或修复 bug
3. 确保代码符合规范并通过检查
4. 编写或更新相关文档
5. 提交 PR，关联相关 Issue
6. 等待代码审查
7. 根据反馈进行修改
8. 合并到 develop 分支

## 测试指南

### 运行测试

```bash
pytest
```

### 编写测试

- 为新功能编写单元测试
- 确保测试覆盖关键功能点
- 使用模拟(mock)避免依赖外部服务

### 代码质量检查

```bash
flake8
```

## 文档更新

所有重要的代码更改都需要更新相关文档：

1. **DEVELOPER_DOCS.md**：更新版本历史和核心逻辑变更
2. **API_DOCUMENTATION.md**：更新 API 接口说明（如有变动）
3. **README.md**：更新功能说明（如添加新功能）

### 版本更新规则

# 文档与设置变更贡献指南

当您对项目做出功能、设置或运行时行为的更改时，请同时更新或新增对应的文档文件（以便使用者与其他开发者能快速理解变更）：

- 主要文档位置：

  - `README.md`：面向最终用户的功能说明与快捷使用指南
  - `API_DOCUMENTATION.md`：对外/开发者可调用的 API 接口说明（包含 `SettingsManager` 的监听器 API 示例）
  - `DEVELOPER_DOCS.md`：开发者指南与版本历史
  - `SETTINGS.md`：列出所有设置键、默认值、说明与生效时机
  - `CHANGELOG.md`：记录变更摘要

- 文档更新建议：

  1. 变更生效流程或新增设置（例如 `auto_mode_*`）时，务必在 `SETTINGS.md` 中列出新键、默认值与说明，并在 `API_DOCUMENTATION.md` 给出示例调用方式。
  2. 若引入运行时可即时生效的设置（例如通过 `SettingsManager.register_listener` 通知 UI），在 `DEVELOPER_DOCS.md` 中写明注册/注销监听器的约定与线程安全建议。
  3. 更新 `TESTS.md` 添加手动或自动化测试步骤，便于 QA 验证运行时行为。

- Settings/监听器贡献约定（开发者必须遵守）：
  1. 在修改设置键或默认值前，先在 `SETTINGS.md` 添加或修改对应条目。
  2. 若功能依赖监听器（例如 UI 页面响应 `auto_mode_review`），请在修改页面初始化代码时同时在 `API_DOCUMENTATION.md` 或 `DEVELOPER_DOCS.md` 中补充示例（如何注册与注销监听器）。
  3. 监听器回调应保持轻量；若需要执行耗时操作，回调中应启动后台线程或把 UI 修改通过 `widget.after(0, fn)` 调度到主线程。
  4. 页面在销毁或切换前必须注销已注册监听器，避免对已销毁对象的回调。

## 常用 Windows PowerShell 命令（贡献者参考）

下面是一些常用的本地开发/检查命令（适用于 Windows PowerShell）：

```powershell
# 安装依赖
pip install -r requirements.txt

# 激活虚拟环境（如果已创建）
.\venv\Scripts\Activate

# 运行应用
python main.py

# 运行测试
pytest -q

# 代码格式检查
flake8
```

## 提交文档的小提示

- 文档类更改使用 `docs:` 前缀提交，例如：

```
docs: 更新 SETTINGS.md，新增 auto_mode_* 配置说明
```

- 在 PR 描述中说明文档变更的文件列表与测试说明（如果适用）。

- 遵循语义化版本控制：`v{主版本}.{次版本}.{补丁}`
- 重大修改更新主版本号：`v1.0.0` → `v2.0.0`
- 新增功能更新次版本号：`v1.0.0` → `v1.1.0`
- Bug 修复更新补丁版本：`v1.0.0` → `v1.0.1`

## 行为准则

- 尊重他人，保持友好的交流
- 接受建设性批评并优雅地提供反馈
- 关注项目的最佳利益
- 帮助新贡献者

## 联系方式

如有任何问题或建议，请通过以下方式联系：

- Email: sqy3258731070@163.com
- GitHub: [CherryPainter](https://github.com/CherryPainter)

感谢您的贡献！
