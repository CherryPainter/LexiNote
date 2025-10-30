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

### v1.1.0
- **新增：** 实现通用的单词属性获取与存储机制
- **新增：** AI调用节流控制功能
- **更新：** 单词例句获取机制优化，实现按需存储
- **新增：** 改进了错误处理和日志记录
- **修复：** 修复了代码结构和语法错误，提高了系统稳定性
- **更新：** 将`update_word(word, translation)`重命名为`update_word_translation(word, translation)`以避免方法名冲突

## 功能概述

### 单词属性管理

#### get_and_save_word_attributes 方法
```python
def get_and_save_word_attributes(self, word: str, attributes: List[str] = None, async_mode=False, callback=None) -> Dict[str, str]:
    """
    获取并保存单词的属性（节流模式）
    
    只在数据库中对应字段为空时从AI获取数据并存储，已有内容的字段不调用AI
    
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
