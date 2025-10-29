# LexiNote API 文档

本文档详细描述了 LexiNote 项目中各个核心模块的 API 接口、参数说明和返回值类型。

## 目录

- [WordManager API](#wordmanager-api)
- [AIManager API](#aimanager-api)
- [LearningManager API](#learningmanager-api)
- [AudioPlayer API](#audioplayer-api)
- [AI助手模块](#ai助手模块)
- [UI 模块接口](#ui模块接口)

## WordManager API

WordManager 是项目的核心类，负责单词管理和练习功能。

### 初始化

```python
def __init__(self, logger=None):
    """初始化WordManager

    Args:
        logger: 日志记录器实例，可选
    """
```

### 单词管理方法

#### get_random_word

```python
def get_random_word(self):
    """获取一个随机单词进行练习

    Returns:
        dict: 包含单词信息的字典
        {"word": str, "translation": str, "weight": float, "mastery": float}
    """
```

#### add_word

```python
def add_word(self, word, translation):
    """添加新单词到单词库

    Args:
        word (str): 英文单词
        translation (str): 中文翻译

    Returns:
        bool: 添加成功返回True，失败返回False
    """
```

#### update_word

```python
def update_word(self, word, translation):
    """更新单词翻译

    Args:
        word (str): 要更新的单词
        translation (str): 新的翻译

    Returns:
        bool: 更新成功返回True，失败返回False
    """
```

#### delete_word

```python
def delete_word(self, word):
    """删除单词

    Args:
        word (str): 要删除的单词

    Returns:
        bool: 删除成功返回True，失败返回False
    """
```

### 学习功能方法

#### check_translation

```python
def check_translation(self, expected, user_input, is_english_to_chinese=True):
    """使用AI检查翻译是否正确

    Args:
        expected (str): 期望的翻译
        user_input (str): 用户输入的翻译
        is_english_to_chinese (bool): 是否为英译中方向

    Returns:
        tuple: (bool, str) - (是否正确, AI参考翻译)
    """
```

#### translate_text

```python
def translate_text(self, text, mode="en2zh"):
    """翻译文本

    Args:
        text (str): 要翻译的文本
        mode (str): 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)

    Returns:
        str: 翻译后的文本
    """
```

#### update_word_progress

```python
def update_word_progress(self, word, is_correct):
    """更新单词学习进度

    Args:
        word (str): 单词
        is_correct (bool): 用户回答是否正确
    """
```

#### get_error_words

```python
def get_error_words(self, limit=None):
    """获取用户错误率较高的单词

    Args:
        limit (int): 返回数量限制

    Returns:
        list: 错误单词列表
    """
```

### 数据存储方法

#### save_progress

```python
def save_progress(self):
    """保存学习进度到文件

    Returns:
        bool: 保存成功返回True，失败返回False
    """
```

#### load_progress

```python
def load_progress(self):
    """从文件加载学习进度

    Returns:
        bool: 加载成功返回True，失败返回False
    """
```

## AIManager API

AIManager 负责与 Ollama API 交互，提供 AI 相关功能。

### 初始化

```python
def __init__(self, logger=None):
    """初始化AIManager

    Args:
        logger: 日志记录器实例，可选
    """
```

### AI 功能方法

#### translate

```python
def translate(self, text, mode="en2zh"):
    """翻译文本

    Args:
        text (str): 要翻译的文本
        mode (str): 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)

    Returns:
        str: 翻译后的文本
    """
```

#### generate_text

```python
def generate_text(self, prompt):
    """根据提示词生成文本

    Args:
        prompt (str): 提示词

    Returns:
        str: 生成的文本
    """
```

#### check_translation

```python
def check_translation(self, expected, user_input, is_english_to_chinese=True):
    """判断翻译是否正确

    Args:
        expected (str): 原始词语
        user_input (str): 用户翻译
        is_english_to_chinese (bool): 是否为英译中方向

    Returns:
        tuple: (bool, str) - (是否正确, AI参考翻译)
    """
```

#### generate_example

```python
def generate_example(self, word):
    """为单词生成例句

    Args:
        word (str): 单词

    Returns:
        str: 包含单词的例句
    """
```

#### evaluate_spelling

````python
def evaluate_spelling(self, word, user_input):
    """评估拼写准确性

    Args:
        word (str): 正确的单词
        user_input (str): 用户输入

    Returns:
        dict: {"correct": bool, "similarity": float, "feedback": str}
    """

## Modules API (新模块)

### ClozeTestModule (modules/cloze_test.py)

```python
class ClozeTestModule:
    def __init__(self):
        """初始化完形填空模块"""

    def start_new_test(self, mode: str = None, level: str = "中级", topic: str = "通用") -> Optional[Dict]:
        """开始新的完形填空练习，返回题目数据或 None

        返回的题目字典示例：
        {
          'id': int,
          'title': str,
          'content': str,  # 含 [BLANK_1] 等占位
          'options': [ {'blank': 1, 'options': ['opt1','opt2','opt3','opt4']}, ... ]
        }
        """

    def submit_answer(self, user_answer: str) -> Tuple[bool, str, str]:
        """提交答案（逗号分隔），返回 (is_correct, evaluation_text, explanation)"""

    def get_test_by_id(self, test_id: int) -> Optional[Dict]:
        """按 ID 获取题目并返回同 start_new_test 的显示格式"""

    def get_all_tests(self) -> List[Dict]:
        """返回题库列表（id/title/source/date_created）"""


### ReadingComprehensionModule (modules/reading_comprehension.py)

```python
class ReadingComprehensionModule:
    def __init__(self):
        pass

    def start_new_test(self, mode: str = None, level: str = "中级", length: str = "短篇", question_count: int = 5) -> Optional[Dict]:
        """开始新的阅读理解题目，返回：
        {
          'id': int,
          'article': str,
          'questions': [str,...],
          'total_questions': int
        }
        """

    def submit_question_answer(self, question_index: int, user_answer: str) -> Tuple[bool, str, str]:
        """提交单题答案，返回 (is_correct, evaluation, explanation)。
        - 选择题使用简单字符串对比（A/B/C/D）
        - 主观题使用 AI 评估（返回 JSON 包含 is_acceptable/score/feedback）
        """

    def submit_all_answers(self, user_answers: List[str]) -> Tuple[float, List[Dict]]:
        """提交全部答案并返回总分与各题结果"""


### AIService (modules/ai_service.py)

```python
class AIService:
    def __init__(self):
        """封装对 AI 的高级调用（生成题目与评估）"""

    def generate_cloze_test(self, level: str = "中级", topic: str = "通用") -> Optional[Dict]:
        """请求 AI 生成完形填空并保存到数据库，返回题目字典（含 id）或 None"""

    def generate_reading_comprehension(self, level: str = "中级", length: str = "短篇", question_count: int = 5) -> Optional[Dict]:
        """请求 AI 生成阅读理解题目并保存到数据库，返回题目字典（含 id）或 None"""

    def evaluate_cloze_answer(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """对完形填空答案做简单对比返回 (is_correct, evaluation_text)"""

    def evaluate_reading_answer(self, user_answer: str, correct_answer: str, question_type: str = "选择题") -> Tuple[bool, str]:
        """主观题会调用 AI 评估，返回 (bool, human-readable evaluation)。

        注意：AI 可能返回带说明的文本，模块内部会尝试提取 JSON（is_acceptable/score/feedback），
        若首次解析失败会自动重试一次并要求 AI 仅返回 JSON，若仍失败将返回评估失败并记录原始响应。
        """

````

### utils.extract_json_from_text

```python
def extract_json_from_text(text: str) -> Optional[Any]:
    """尝试从自由文本中提取 JSON 对象并解析，若无法解析返回 None。"""
```

````

### 状态检查方法

#### is_available

```python
def is_available(self):
    """检查AI服务是否可用

    Returns:
        bool: 可用返回True，不可用返回False
    """
````

## LearningManager API

LearningManager 实现学习模式的核心逻辑。

### 初始化

```python
def __init__(self, word_manager, logger=None):
    """初始化LearningManager

    Args:
        word_manager: WordManager实例
        logger: 日志记录器实例，可选
    """
```

### 学习流程方法

#### get_next_word

```python
def get_next_word(self):
    """获取下一个要学习的单词

    Returns:
        dict: 单词信息字典或None
    """
```

#### update_mastery_level

```python
def update_mastery_level(self, word, rating):
    """更新单词掌握度

    Args:
        word (str): 单词
        rating (int): 用户评分(1-5)

    Returns:
        bool: 更新成功返回True
    """
```

#### get_word_definition

```python
def get_word_definition(self, word):
    """获取单词释义

    Args:
        word (str): 单词

    Returns:
        str: 单词释义
    """
```

### 进度管理方法

#### get_word_progress

```python
def get_word_progress(self):
    """获取单词学习进度

    Returns:
        dict: 单词进度数据
    """
```

#### save_progress

```python
def save_progress(self):
    """保存学习进度

    Returns:
        bool: 保存成功返回True
    """
```

#### load_progress

```python
def load_progress(self):
    """加载学习进度

    Returns:
        bool: 加载成功返回True
    """
```

## AudioPlayer API

AudioPlayer 提供单词发音功能。

### 初始化

```python
def __init__(self, logger=None):
    """初始化AudioPlayer

    Args:
        logger: 日志记录器实例，可选
    """
```

### 播放控制方法

#### play_pronunciation

```python
def play_pronunciation(self, word):
    """播放单词发音

    Args:
        word (str): 要发音的单词

    Returns:
        bool: 播放成功返回True，失败返回False
    """
```

#### stop

```python
def stop(self):
    """停止播放

    Returns:
        bool: 操作成功返回True
    """
```

## DictationManager API

DictationManager 负责听写练习的核心逻辑管理，包括队列控制和单词结果记录。

### 初始化

```python
def __init__(self, word_manager, logger=None):
    """初始化DictationManager

    Args:
        word_manager: WordManager实例
        logger: 日志记录器实例，可选
    """
```

### 队列管理方法

#### create_queue

```python
def create_queue(self, words, queue_size=10):
    """创建听写练习队列

    Args:
        words (list): 可选单词列表
        queue_size (int): 队列大小

    Returns:
        list: 创建的单词队列
    """
```

#### next_in_queue

```python
def next_in_queue(self):
    """获取队列中的下一个单词

    严格检查队列是否存在和索引有效性，确保不会返回超出队列范围的单词

    Returns:
        str: 单词字符串，如果队列为空或已到达队列末尾则返回None
    """
```

#### skip_current_word

```python
def skip_current_word(self):
    """跳过当前单词，确保队列索引正确更新

    Returns:
        bool: 跳过成功返回True
    """
```

#### has_next

```python
def has_next(self):
    """检查队列是否还有下一个单词

    包含空队列检查，确保在队列为None或空时返回False

    Returns:
        bool: 有下一个单词返回True
    """
```

#### get_current_position

```python
def get_current_position(self):
    """获取当前队列位置信息

    使用min/max保证数值在合理范围内，避免索引越界

    Returns:
        dict: 包含current和total信息的字典
    """
```

#### get_remaining_count

```python
def get_remaining_count(self):
    """获取剩余单词数量

    Returns:
        int: 剩余单词数
    """
```

### 结果记录方法

#### record_result

```python
def record_result(self, word, is_correct, time_spent=0):
    """记录单词练习结果，影响单词权重

    Args:
        word (str): 单词
        is_correct (bool): 是否正确
        time_spent (float): 花费的时间（秒）

    结果会被保存并用于统计准确率和影响单词复习权重
    """
```

## UI 模块接口

### MainWindow

```python
def __init__(self, root):
    """初始化主窗口

    Args:
        root: Tkinter根窗口实例
    """
```

#### switch_to_page

```python
def switch_to_page(self, page_name):
    """切换到指定页面

    Args:
        page_name (str): 页面名称("learning", "translation", "dictation", "review")
    """
```

### TranslationPage

```python
def __init__(self, parent, word_manager, audio_player):
    """初始化翻译练习页面

    Args:
        parent: 父窗口
        word_manager: WordManager实例
        audio_player: AudioPlayer实例
    """
```

#### start_exercise

```python
def start_exercise(self):
    """开始翻译练习
    """
```

#### check_answer

```python
def check_answer(self):
    """检查用户答案
    """
```

### LearningPage

```python
def __init__(self, parent, word_manager, learning_manager):
    """初始化学习页面

    Args:
        parent: 父窗口
        word_manager: WordManager实例
        learning_manager: LearningManager实例
    """
```

#### show_next_word

```python
def show_next_word(self):
    """显示下一个单词
    """
```

### DictationPage

```python
def __init__(self, parent, word_manager, audio_player):
    """初始化听写页面

    Args:
        parent: 父窗口
        word_manager: WordManager实例
        audio_player: AudioPlayer实例
    """
```

#### start_exercise

```python
def start_exercise(self):
    """开始听写练习

    根据用户选择的来源和数量创建单词队列并开始练习
    """
```

#### \_play_word

```python
def _play_word(self):
    """播放当前单词发音并启动计时器
    """
```

#### \_check_answer

```python
def _check_answer(self):
    """检查用户输入答案的正确性

    记录结果并影响单词权重
    """
```

#### \_handle_timeout

```python
def _handle_timeout(self):
    """处理单词超时情况

    将超时单词视为未掌握，增加其复习权重
    记录超时信息并更新UI显示
    """
```

#### \_stop_timer

```python
def _stop_timer(self):
    """停止当前计时器

    安全处理，确保计时器ID存在
    """
```

#### \_skip_word

```python
def _skip_word(self):
    """跳过当前单词

    记录跳过操作，增加单词复习权重
    """
```

#### \_next_word_in_queue

```python
def _next_word_in_queue(self):
    """获取并显示队列中的下一个单词

    更新进度显示
    """
```

### ReviewPage

```python
def __init__(self, parent, word_manager, audio_player):
    """初始化复习页面

    Args:
        parent: 父窗口
        word_manager: WordManager实例
        audio_player: AudioPlayer实例
    """
```

## 错误处理约定

- 所有 API 方法都遵循统一的错误处理约定
- 可能的异常会被捕获并返回适当的默认值
- 错误信息会通过 logger 记录
- 布尔返回值的方法通常成功返回 True，失败返回 False
- 可能返回 None 的方法在文档中有明确说明

## SettingsManager API (设置管理器)

SettingsManager 负责应用内配置的读取/写入、缓存以及变更通知（监听器）。下面列出常用方法与示例。

### register_listener / unregister_listener

```python
def register_listener(self, key: str, callback):
    """注册设置变更监听器。

    callback 的签名为 func(key, new_value)。当指定 key 的设置被修改时，回调会被异步（非阻塞）调用。
    """

def unregister_listener(self, key: str, callback):
    """注销先前注册的监听器。"""
```

示例（在 UI 页面或模块初始化时注册）：

```python
sm = SettingsManager()

def on_auto_mode_change(key, new_value):
    # key 例如: 'auto_mode_review'
    print(key, new_value)

sm.register_listener('auto_mode_review', on_auto_mode_change)
```

注意：回调应尽量保持轻量。如果需要执行耗时操作，请在回调内创建线程或使用主线程的事件调度（如 tkinter 的 after）。

### get_auto_mode / set_auto_mode

获取或设置模块级别的自动/手动控制。

```python
def get_auto_mode(self, module: str) -> str:
    """module 为 'word_learning' | 'translation_practice' | 'review'，返回 'manual' 或 'auto'"""

def set_auto_mode(self, module: str, mode: str) -> bool:
    """设置模块模式，mode 应为 'manual' 或 'auto'。返回是否设置成功。"""
```

示例：

```python
# 将复习模块切换为自动模式
sm.set_auto_mode('review', 'auto')

# 立即查询当前模式
print(sm.get_auto_mode('review'))  # 'auto'
```

### 典型设置键（与默认值）

- `auto_mode_word_learning`: 'manual' # 单词学习模块的手动/自动控制
- `auto_mode_translation_practice`: 'manual' # 翻译练习模块的手动/自动控制
- `auto_mode_review`: 'manual' # 复习模块的手动/自动控制
- `auto_next_correct`: False # 答对后是否自动跳转
- `auto_next_wrong`: False # 答错后是否自动跳转
- `auto_next_delay`: 1000 # 自动跳转延迟（毫秒）
- `auto_next_example`: False # 例句显示后是否自动下一个（复习页面）

这些设置的变更会触发相应的监听器（如果已注册），从而使 UI 在运行时即时响应设置变更（例如显示/隐藏“下一步”按钮、启用/禁用自动跳转）。

### 在 UI 中的使用建议

- 在页面初始化阶段注册监听器（例如 `ui/translation_page.py`、`ui/review_page.py`、`ui/dictation_page.py`），并在页面销毁或切换页面时注销监听器（`unregister_listener`）。
- 监听器应尽量只负责更新 UI 状态（例如隐藏/显示按钮、开启/关闭定时器），避免在监听器中执行阻塞操作。
- 若监听器需要与 tkinter 交互（修改组件），请使用 `widget.after(0, callback)` 的方式将修改调度回主线程。

### 示例：translation page 中的即时生效

在 `ui/translation_page.py` 中实现了对 `auto_mode_translation_practice` 的监听。行为示例：

- 当设置为 `auto` 时，翻译模块会根据 `auto_next_correct/auto_next_wrong` 的值决定是否在显示结果后自动跳转并隐藏手动“下一步”按钮。
- 当设置为 `manual` 时，会立即显示“下一步”按钮以便用户手动控制。

```python
# 页面初始化时注册
sm.register_listener('auto_mode_translation_practice', self._on_auto_mode_translation_practice_change)

# 回调示例
def _on_auto_mode_translation_practice_change(self, key, value):
    if value == 'auto':
        # 根据 auto_next_correct/auto_next_wrong 决定是否隐藏 next_button
        ...
    else:
        # 手动模式：显示 next_button
        ...
以上设计保证用户在设置变更后，无需重启应用即可立即看到生效效果。

## AI助手模块

AI助手模块提供智能英语学习辅助功能，支持多种学习任务类型。

### AIAssistantPage 类

`AIAssistantPage` 是AI助手的UI实现类，负责提供用户界面和交互。

#### 初始化

```python
def __init__(self, parent, main_window):
    """初始化AI助手页面
    
    Args:
        parent: 父窗口组件
        main_window: 主窗口实例
    """
```

#### on_show 方法

```python
def on_show(self):
    """当页面显示时调用，重新检查AI连接状态"""
```

### AI服务接口

AI助手模块使用现有的 `AIService` 类进行AI交互，主要通过 `ai_manager._ask_sync` 方法获取AI响应。

#### 任务类型支持

AI助手支持以下8种学习任务类型：

1. **单词解释与例句**：提供单词的中文解释、实用例句和使用场景
2. **语法讲解**：解释语法规则、提供例句和常见错误说明
3. **写作批改**：批改英语作文、指出错误并提供改进建议
4. **口语练习指导**：提供对话示例和语音语调建议
5. **阅读理解辅导**：帮助理解英语文章、解释难点
6. **听力练习建议**：推荐听力材料和练习方法
7. **词汇量测试**：设计词汇测试题和记忆技巧
8. **英语知识点总结**：系统整理英语知识点

#### 难度级别

- 初级：适合英语初学者
- 中级：适合有一定基础的学习者
- 高级：适合英语水平较高的学习者
