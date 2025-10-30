# LexiNote 开发文档

## 项目结构
```
├── data/              # 数据文件夹（相对路径）
├── cache/             # 缓存文件夹
├── core/              # 核心模块
│   ├── database_manager.py  # 数据库管理器
│   ├── ai_interface.py      # AI接口
├── modules/           # 功能模块
│   ├── ai_service.py        # AI服务
├── word_manager.py    # 单词管理器
├── logger.py          # 日志模块
├── .gitignore         # Git忽略文件
└── README.md          # 项目说明
```

## 版本更新日志

### v1.1.6
- **增强：** 优化AI提示模板，明确要求选择题选项必须使用英文，不允许使用中文选项，以增加学习的挑战性
### v1.1.5
- **修复：** 修复f-string中的JSON格式错误，转义大括号以避免与Python格式说明符冲突
### v1.1.4
- **增强：** 优化AI提示模板，明确要求选择题和简答题必须包含具体题目内容，禁止使用'Question X'等占位符
- **改进：** 完善提示模板中的示例格式，提供更清晰的问题格式指导

### v1.1.3
- **修复：** 解决阅读理解模块题目只显示'question'的问题
- **优化：** 增强AI服务生成题目时的错误检测和重试机制
- **优化：** 添加更详细的日志记录，便于调试问题

### v1.1.2
- **优化：** 整合AI服务连接检测，统一由WordManager在程序启动时检测，移除完形填空和阅读理解模块的独立检测逻辑

### v1.1.1
- **优化：** 阅读理解模块题目显示，使题目和每个选项都单独占一行，提高阅读体验

### v1.1.0
- **新增：** 实现通用的单词属性获取与存储机制
- **新增：** AI调用节流控制功能
- **更新：** 单词例句获取机制优化，实现按需存储
- **新增：** 改进了错误处理和日志记录
- **修复：** 修复了代码结构和语法错误，提高了系统稳定性
- **更新：** 将`update_word(word, translation)`重命名为`update_word_translation(word, translation)`以避免方法名冲突
- **增强：** JSON解析功能，优化了`extract_json_from_text`函数的鲁棒性
- **添加：** 更多的预处理和修复步骤，提高了从AI返回中提取JSON的成功率
- **更新：** 窗口几何设置，从1080x720调整为1650x980
- **改进：** 错误处理逻辑，增加了更详细的日志记录

### v1.0.0
- 初始版本
- 实现了基本的单词学习功能
- 实现了AI辅助翻译和解释功能
- 实现了阅读理解模块

## 功能概述

### 单词属性管理

#### get_and_save_word_attributes 方法
```python
def get_and_save_word_attributes(self, word: str, attributes: List[str] = None, async_mode=False, callback=None) -> Dict[str, str]:
    """
    获取并保存单词的属性（节流模式）
    
    只在数据库中对应字段为空时从AI获取数据并存储，已有内容的字段不调用AI
    
    优化说明：
    - 异步模式下实现了"先展示后保存"的优化流程
    - AI获取数据后立即返回给用户界面展示，数据库保存操作在后台异步进行
    - 这样可以避免数据库操作阻塞UI线程，提升用户体验
    - 每次调用时都会重新验证AI可用性，确保能及时检测到Ollama服务状态变化
    
    Args:
        word: 单词
        attributes: 需要获取的属性列表，可选值：['phonetic', 'example', 'meaning_en', 'tag']
        async_mode: 是否异步获取
        callback: 异步模式下的回调函数，接收参数：(attributes_dict: Dict[str, str])
        
    Returns:
        Dict[str, str]: 同步模式返回属性字典，异步模式返回None
    """
```

### AI 节流控制

#### 节流控制参数
- `_min_interval_ms`: 两次AI调用之间的最小间隔（毫秒），默认500ms
- `_max_calls_per_minute`: 每分钟最大AI调用次数，默认10次

#### set_throttle_limits 方法
```python
def set_throttle_limits(self, min_interval_ms: int = 500, max_calls_per_minute: int = 10):
    """
    设置AI调用节流限制
    
    Args:
        min_interval_ms: 两次调用之间的最小间隔(毫秒)
        max_calls_per_minute: 每分钟最大调用次数
    """
```

## 使用示例

### 获取并保存单词例句（带节流）

```python
# 初始化单词管理器
word_manager = WordManager()

# 设置节流限制（可选）
word_manager.set_throttle_limits(min_interval_ms=300, max_calls_per_minute=15)

# 异步获取单词例句（会自动检查节流限制）
def example_callback(example):
    print(f"获取到例句: {example}")

word_manager.get_word_example("example", async_mode=True, callback=example_callback)

# 获取多个属性
word_manager.get_and_save_word_attributes(
    "example", 
    attributes=['phonetic', 'example', 'meaning_en'], 
    async_mode=True, 
    callback=lambda attrs: print(f"获取到属性: {attrs}")
)
```

## 数据格式规范

### AI返回数据格式要求

AI系统需要返回以下格式的数据，以便正确存储到数据库：

1. **音标 (phonetic)**：仅返回标准音标字符串，如 "/ɪɡˈzɑːmpəl/"

2. **例句 (example)**：英文例句加中文翻译，格式为：
   ```
   This is an example sentence with the word "example". (这是一个包含"example"的例句。)
   ```

3. **英文释义 (meaning_en)**：纯英文的单词释义，如 "a thing characteristic of its kind or illustrating a general rule"

4. **标签 (tag)**：逗号分隔的标签列表，如 "名词,动词,常用"

### 数据库结构

单词表 (words) 结构如下：
- `id`: 主键
- `set_id`: 词库ID
- `word`: 单词
- `translation`: 翻译
- `phonetic`: 音标
- `example`: 例句
- `meaning_en`: 英文释义
- `tag`: 标签
- 其他学习相关字段

## 开发注意事项

1. **节流控制**：AI调用前必须检查节流限制，避免频繁调用导致性能问题或API限制

2. **数据存储**：只有当数据库中对应字段为空时才从AI获取数据并存储

3. **异步操作**：所有可能耗时的AI调用都应支持异步模式，避免阻塞UI线程

4. **错误处理**：所有用户输入和外部调用需使用try/except捕获异常，提供适当的错误提示

5. **日志记录**：所有重要操作都应记录日志，便于调试和问题排查

6. **代码规范**：遵循PEP8规范，保持代码风格一致
