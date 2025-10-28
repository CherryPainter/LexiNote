# LexiNote API 文档

本文档详细描述了LexiNote项目中各个核心模块的API接口、参数说明和返回值类型。

## 目录

- [WordManager API](#wordmanager-api)
- [AIManager API](#aimanager-api)
- [LearningManager API](#learningmanager-api)
- [AudioPlayer API](#audioplayer-api)
- [UI模块接口](#ui模块接口)

## WordManager API

WordManager是项目的核心类，负责单词管理和练习功能。

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

AIManager负责与Ollama API交互，提供AI相关功能。

### 初始化

```python
def __init__(self, logger=None):
    """初始化AIManager
    
    Args:
        logger: 日志记录器实例，可选
    """
```

### AI功能方法

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

```python
def evaluate_spelling(self, word, user_input):
    """评估拼写准确性
    
    Args:
        word (str): 正确的单词
        user_input (str): 用户输入
        
    Returns:
        dict: {"correct": bool, "similarity": float, "feedback": str}
    """
```

### 状态检查方法

#### is_available

```python
def is_available(self):
    """检查AI服务是否可用
    
    Returns:
        bool: 可用返回True，不可用返回False
    """
```

## LearningManager API

LearningManager实现学习模式的核心逻辑。

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

AudioPlayer提供单词发音功能。

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

DictationManager负责听写练习的核心逻辑管理，包括队列控制和单词结果记录。

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

## UI模块接口

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

#### _play_word

```python
def _play_word(self):
    """播放当前单词发音并启动计时器
    """
```

#### _check_answer

```python
def _check_answer(self):
    """检查用户输入答案的正确性
    
    记录结果并影响单词权重
    """
```

#### _handle_timeout

```python
def _handle_timeout(self):
    """处理单词超时情况
    
    将超时单词视为未掌握，增加其复习权重
    记录超时信息并更新UI显示
    """
```

#### _stop_timer

```python
def _stop_timer(self):
    """停止当前计时器
    
    安全处理，确保计时器ID存在
    """
```

#### _skip_word

```python
def _skip_word(self):
    """跳过当前单词
    
    记录跳过操作，增加单词复习权重
    """
```

#### _next_word_in_queue

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

- 所有API方法都遵循统一的错误处理约定
- 可能的异常会被捕获并返回适当的默认值
- 错误信息会通过logger记录
- 布尔返回值的方法通常成功返回True，失败返回False
- 可能返回None的方法在文档中有明确说明