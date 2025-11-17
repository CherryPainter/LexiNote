# LexiNote API 文档

本文档详细描述了 LexiNote 项目中各个核心模块的 API 接口、参数说明和返回值类型。

## 模块功能概述

### 单词批量导入模块

新增的`word_importer.py`模块提供了从JSON文件批量导入单词到数据库的功能。该模块既可以作为独立脚本运行，也可以通过`WordManager`接口调用。

**主要特性**：
- 支持从标准JSON格式批量导入单词
- 自动处理重复单词和无效数据
- 提供详细的导入统计信息
- 完整的错误处理和日志记录
- 支持作为独立脚本或通过API调用

## 目录

- [单词批量导入模块](#单词批量导入模块)
- [WordManager API](#wordmanager-api)
  - [基础单词操作](#基础单词操作)
  - [词库管理操作](#词库管理操作)
  - [单词操作接口](#单词操作接口)
  - [导入导出功能](#导入导出功能)
  - [学习功能方法](#学习功能方法)
- [AIManager API](#aimanager-api)
- [LearningManager API](#learningmanager-api)
- [AudioPlayer API](#audioplayer-api)
- [AI助手模块](#ai助手模块)
- [UI 模块接口](#ui模块接口)

## 单词批量导入模块 API

### WordImporter 类

```python
class WordImporter:
    """
    单词批量导入器类，负责从JSON文件导入单词到数据库
    
    提供独立的单词导入功能，可作为脚本直接运行或通过WordManager调用
    """
    
    def __init__(self):
        """
        初始化WordImporter
        """
    
    def import_from_json_file(self, json_file_path: str, set_id: int = None) -> Tuple[bool, Dict]:
        """
        从JSON文件导入单词到数据库
        
        参数:
            json_file_path: JSON文件路径，文件格式应为 {"word1": "translation1", "word2": "translation2", ...}
            set_id: 词库ID，默认为默认词库
        
        返回:
            Tuple[bool, Dict]: 导入是否成功和统计信息
            统计信息包含以下字段：
                - success: 布尔值，表示导入是否成功
                - total: 整数，文件中总单词数量
                - imported: 整数，成功导入的单词数量
                - skipped: 整数，跳过的单词数量（包括重复和无效单词）
                - errors: 列表，包含错误信息（如果有）
        """
```

### 便捷函数

```python
def import_words_from_json(json_file_path: str, set_id: int = None) -> Dict:
    """
    便捷函数：从JSON文件批量导入单词
    
    参数:
        json_file_path: JSON文件路径
        set_id: 词库ID，默认为默认词库
    
    返回:
        Dict: 导入结果统计信息，包含以下字段：
            - success: 布尔值，表示导入是否成功
            - total: 整数，文件中总单词数量
            - imported: 整数，成功导入的单词数量
            - skipped: 整数，跳过的单词数量（包括重复和无效单词）
            - errors: 列表，包含错误信息（如果有）
    """


## WordManager API

WordManager 是项目的核心类，负责单词管理、词库管理、学习进度跟踪和AI功能调用。

### 批量导入单词

```python
def batch_import_words(self, json_data, set_id: int = None) -> Dict:
    """
    批量导入单词到数据库
    
    参数:
        json_data: JSON数据，可以是文件路径或字典对象
        set_id: 词库ID，默认为默认词库
    
    返回:
        Dict: 导入结果统计信息，包含以下字段：
            - success: 布尔值，表示导入是否成功
            - total: 整数，文件中总单词数量
            - imported: 整数，成功导入的单词数量
            - skipped: 整数，跳过的单词数量（包括重复和无效单词）
            - errors: 列表，包含错误信息（如果有）
    """
```

### 初始化

```python
def __init__(self, statistics_manager: Optional[StatisticsManager] = None):
    """初始化WordManager

    Args:
        statistics_manager: 统计管理器实例，如果为None则自动创建
    """
```

### 单词管理方法

#### get_random_word

```python
def get_random_word(self, exclude_words: List[str] = None) -> Optional[str]:
    """获取随机单词

    Args:
        exclude_words: 排除的单词列表

    Returns:
        str: 随机单词，如果没有可用单词返回None
    """
```

#### add_word

```python
def add_word(self, word: str, translation: str) -> bool:
    """添加单词

    Args:
        word: 单词
        translation: 翻译

    Returns:
        bool: 添加成功返回True，失败返回False
    """
```

#### update_word

```python
def update_word(self, word_id, **kwargs):
    """
    更新单词信息
    
    参数:
        word_id (int): 单词ID
        **kwargs: 要更新的字段，如translation, phonetic, example, meaning_en, tag等
    
    返回:
        bool: 更新成功返回True，失败返回False
    """
```

#### delete_word

```python
def delete_word(self, word_id):
    """
    删除单词
    
    参数:
        word_id (int): 单词ID
    
    返回:
        bool: 删除成功返回True，失败返回False
    """
```

### 词库管理操作

#### get_all_word_sets

```python
def get_all_word_sets(self):
    """
    获取所有词库列表
    
    返回:
        list: 词库字典列表，每个字典包含id, name, description, word_count等信息
    """
```

#### get_word_set_by_id

```python
def get_word_set_by_id(self, set_id):
    """
    根据ID获取词库信息
    
    参数:
        set_id (int): 词库ID
    
    返回:
        dict or None: 词库信息字典，不存在时返回None
    """
```

#### get_word_set_by_name

```python
def get_word_set_by_name(self, name):
    """
    根据名称获取词库信息
    
    参数:
        name (str): 词库名称
    
    返回:
        dict or None: 词库信息字典，不存在时返回None
    """
```

#### get_active_word_set

```python
def get_active_word_set(self):
    """
    获取当前激活的词库
    
    返回:
        dict or None: 当前激活的词库信息，无激活词库时返回None
    """
```

#### set_active_word_set

```python
def set_active_word_set(self, set_id):
    """
    设置当前激活的词库
    
    参数:
        set_id (int): 词库ID
    
    返回:
        bool: 设置成功返回True，失败返回False
    """
```

#### create_word_set

```python
def create_word_set(self, name, description=''):
    """
    创建新的词库
    
    参数:
        name (str): 词库名称
        description (str): 词库描述
    
    返回:
        dict or None: 新创建的词库信息，失败返回None
    """
```

#### delete_word_set

```python
def delete_word_set(self, set_id):
    """
    删除词库（默认词库不可删除）
    
    参数:
        set_id (int): 词库ID
    
    返回:
        bool: 删除成功返回True，失败返回False
    """
```

### 单词操作接口

#### get_words_from_active_set

```python
def get_words_from_active_set(self, keyword=None, limit=None, offset=None, order_by='id', sort_order='asc'):
    """
    从当前激活的词库获取单词列表
    
    参数:
        keyword (str, optional): 搜索关键词
        limit (int, optional): 返回结果数量限制
        offset (int, optional): 分页偏移量
        order_by (str, optional): 排序字段
        sort_order (str, optional): 排序顺序 ('asc' 或 'desc')
    
    返回:
        list: 单词字典列表
    """
```

#### get_words_by_set_id

```python
def get_words_by_set_id(self, set_id, keyword=None, limit=None, offset=None, order_by='id', sort_order='asc'):
    """
    根据词库ID获取单词列表
    
    参数:
        set_id (int): 词库ID
        keyword (str, optional): 搜索关键词
        limit (int, optional): 返回结果数量限制
        offset (int, optional): 分页偏移量
        order_by (str, optional): 排序字段
        sort_order (str, optional): 排序顺序 ('asc' 或 'desc')
    
    返回:
        list: 单词字典列表
    """
```

#### add_word_to_active_set

```python
def add_word_to_active_set(self, word, translation, phonetic='', example='', meaning_en='', tag=''):
    """
    向当前激活的词库添加单词
    
    参数:
        word (str): 英文单词
        translation (str): 中文翻译
        phonetic (str, optional): 音标
        example (str, optional): 例句
        meaning_en (str, optional): 英文释义
        tag (str, optional): 词性标签
    
    返回:
        dict or None: 新添加的单词信息，失败返回None
    """
```

#### update_word

```python
def update_word(self, word_id, **kwargs):
    """
    更新单词信息
    
    参数:
        word_id (int): 单词ID
        **kwargs: 要更新的字段，如translation, phonetic等
    
    返回:
        bool: 更新成功返回True，失败返回False
    """
```

#### delete_word

```python
def delete_word(self, word_id):
    """
    删除单词
    
    参数:
        word_id (int): 单词ID
    
    返回:
        bool: 删除成功返回True，失败返回False
    """
```

### 导入导出功能

#### import_word_set_from_json

```python
def import_word_set_from_json(self, json_file_path):
    """
    从JSON文件导入词库数据
    
    参数:
        json_file_path (str): JSON文件路径
    
    返回:
        dict: 导入结果，包含success, message, word_count等字段
    """
```

#### export_word_set_to_json

```python
def export_word_set_to_json(self, set_id, output_file_path):
    """
    导出词库到JSON文件
    
    参数:
        set_id (int): 词库ID
        output_file_path (str): 输出文件路径
    
    返回:
        dict: 导出结果，包含success, message, word_count等字段
    """
```

#### batch_import_words

```python
def batch_import_words(self, file_path, set_id=None):
    """
    批量导入单词到当前激活的词库
    
    参数:
        file_path (str): JSON文件路径
        set_id (int, optional): 词库ID，若为None则使用当前激活词库
    
    返回:
        dict: 导入统计信息，包含total, imported, failed, errors等字段
    """
```

### 学习功能方法

#### get_words_for_review

```python
def get_words_for_review(self, filter_type='all', limit=20):
    """
    获取用于复习的单词列表
    
    参数:
        filter_type (str): 过滤类型 ('all', 'unfamiliar', 'familiar', 'difficult')
        limit (int): 返回结果数量限制
    
    返回:
        list: 单词字典列表
    """
```

#### update_word_familiarity

```python
def update_word_familiarity(self, word_id, is_correct):
    """
    更新单词熟悉度
    
    参数:
        word_id (int): 单词ID
        is_correct (bool): 用户回答是否正确
    
    返回:
        bool: 更新成功返回True，失败返回False
    """
```

#### update_word_proficiency

```python
def update_word_proficiency(self, word_id, proficiency):
    """
    更新单词熟练度
    
    参数:
        word_id (int): 单词ID
        proficiency (float): 熟练度值 (0.0-1.0)
    
    返回:
        bool: 更新成功返回True，失败返回False
    """
```

#### get_word_familiarity

```python
def get_word_familiarity(self, word_id):
    """
    获取单词熟悉度
    
    参数:
        word_id (int): 单词ID
    
    返回:
        float: 熟悉度值 (0.0-1.0)
    """
```

#### get_learning_stats

```python
def get_learning_stats(self):
    """
    获取学习统计信息
    
    返回:
        dict: 包含学习统计信息的字典
    """
```

#### get_familiar_words

```python
def get_familiar_words(self, threshold=0.7, limit=None):
    """
    获取熟悉的单词列表
    
    参数:
        threshold (float): 熟悉度阈值
        limit (int): 返回结果数量限制
    
    返回:
        list: 单词字典列表
    """
```

#### get_unfamiliar_words

```python
def get_unfamiliar_words(self, threshold=0.3, limit=None):
    """
    获取不熟悉的单词列表
    
    参数:
        threshold (float): 熟悉度阈值
        limit (int): 返回结果数量限制
    
    返回:
        list: 单词字典列表
    """
```

#### get_difficult_words

```python
def get_difficult_words(self, limit=None):
    """
    获取困难单词列表
    
    参数:
        limit (int): 返回结果数量限制
    
    返回:
        list: 单词字典列表
    """
```

#### get_today_learned_words

```python
def get_today_learned_words(self):
    """
    获取今日学习的单词列表
    
    返回:
        list: 单词字典列表
    """
```

#### add_wrong_word

```python
def add_wrong_word(self, word_id):
    """
    添加错误单词记录
    
    参数:
        word_id (int): 单词ID
    
    返回:
        bool: 添加成功返回True，失败返回False
    """
```

#### get_wrong_words

```python
def get_wrong_words(self, limit=None):
    """
    获取错误单词列表
    
    参数:
        limit (int): 返回结果数量限制
    
    返回:
        list: 单词字典列表
    """
```

#### get_progress

```python
def get_progress(self, set_id=None):
    """
    获取学习进度
    
    参数:
        set_id (int, optional): 词库ID，默认使用当前激活词库
    
    返回:
        dict: 包含学习进度信息的字典
    """
```

#### start_exercise

```python
def start_exercise(self, exercise_type, set_id=None):
    """
    开始练习
    
    参数:
        exercise_type (str): 练习类型
        set_id (int, optional): 词库ID，默认使用当前激活词库
    
    返回:
        bool: 开始成功返回True，失败返回False
    """
```

### AI辅助功能

#### get_translation

```python
def get_translation(self, word, mode="en2zh"):
    """
    获取单词翻译
    
    参数:
        word (str): 要翻译的单词
        mode (str): 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)
    
    返回:
        str: 翻译后的文本
    """
```

#### check_translation

```python
def check_translation(self, word_id, user_translation, mode="local_first"):
    """
    检查翻译是否正确
    
    参数:
        word_id (int): 单词ID
        user_translation (str): 用户输入的翻译
        mode (str): 检查模式 ('local_first', 'local_only', 'ai_first')
    
    返回:
        dict: 包含检查结果的字典
    """
```

#### ai_complete_word_details

```python
def ai_complete_word_details(self, word_id):
    """
    使用AI补全单词详细属性
    
    参数:
        word_id (int): 单词ID
    
    返回:
        bool: 补全成功返回True，失败返回False
    """
```

#### get_words_missing_details

```python
def get_words_missing_details(self, limit=10):
    """
    获取缺少详细属性的单词列表
    
    参数:
        limit (int): 返回结果数量限制
    
    返回:
        list: 单词字典列表
    """
```

#### get_word_example

```python
def get_word_example(self, word_id):
    """
    获取单词例句
    
    参数:
        word_id (int): 单词ID
    
    返回:
        str: 单词例句
    """
```

#### check_spelling

```python
def check_spelling(self, word, user_input):
    """
    检查拼写是否正确
    
    参数:
        word (str): 正确单词
        user_input (str): 用户输入
    
    返回:
        dict: 包含拼写检查结果的字典
    """
```

#### is_ai_available

```python
def is_ai_available(self):
    """
    检查AI服务是否可用
    
    返回:
        bool: AI服务可用返回True，否则返回False
    """
```

### 缓存管理

#### clear_cache

```python
def clear_cache(self, cache_type=None):
    """
    清除缓存
    
    参数:
        cache_type (str, optional): 缓存类型，默认为清除所有缓存
    
    返回:
        bool: 清除成功返回True，失败返回False
    """
```

### 其他功能

#### get_word_count

```python
def get_word_count(self, set_id=None):
    """
    获取单词数量
    
    参数:
        set_id (int, optional): 词库ID，默认使用当前激活词库
    
    返回:
        int: 单词数量
    """
```

#### get_weighted_random_word

```python
def get_weighted_random_word(self, set_id=None):
    """
    根据权重获取随机单词
    
    参数:
        set_id (int, optional): 词库ID，默认使用当前激活词库
    
    返回:
        dict or None: 单词字典或None
    """
```

#### update_word_weight

```python
def update_word_weight(self, word_id, weight):
    """
    更新单词权重
    
    参数:
        word_id (int): 单词ID
        weight (float): 权重值
    
    返回:
        bool: 更新成功返回True，失败返回False
    """
```

#### get_and_save_word_attributes

```python
def get_and_save_word_attributes(self, word):
    """
    获取并保存单词属性
    
    参数:
        word (str): 单词
    
    返回:
        dict or None: 包含单词属性的字典或None
    """
```

## AIManager API

AIManager 负责与 Ollama API 交互，提供 AI 相关功能。位于 `core/ai_interface.py`。

### 初始化

```python
def __init__(self, model=None):
    """初始化AIManager（单例模式，只在第一次创建实例时执行）

    Args:
        model: 使用的Ollama模型名称，如果为None则从设置中获取
    """
```

### AI 功能方法

#### translate

```python
async def translate(self, text: str, mode: str = "en2zh", callback=None) -> str:
    """异步翻译文本

    Args:
        text: 要翻译的文本
        mode: 翻译模式，"en2zh"(英→中)或"zh2en"(中→英)
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        str: 翻译后的文本
    """
```

#### translate_sync

```python
def translate_sync(self, text: str, mode: str = "en2zh", callback=None) -> str:
    """同步翻译文本（兼容旧接口）

    Args:
        text: 要翻译的文本
        mode: 翻译模式
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        str: 翻译后的文本
    """
```

#### example

```python
async def example(self, word: str, callback=None) -> str:
    """异步为单词生成例句

    Args:
        word: 要生成例句的单词
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        str: 包含例句和翻译的文本（格式：英文例句|中文翻译）
    """
```

#### example_sync

```python
def example_sync(self, word: str, callback=None) -> str:
    """同步生成例句（兼容旧接口）

    Args:
        word: 要生成例句的单词
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        str: 包含例句和翻译的文本（格式：英文例句|中文翻译）
    """
```

#### get_word_details

```python
async def get_word_details(self, word: str, callback=None) -> str:
    """异步获取单词的详细属性

    Args:
        word: 要获取详细属性的单词
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        str: 包含单词详细属性的JSON字符串
    """
```

#### get_word_details_sync

```python
def get_word_details_sync(self, word: str, callback=None) -> str:
    """同步获取单词的详细属性（兼容旧接口）

    Args:
        word: 要获取详细属性的单词
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        str: 包含单词详细属性的JSON字符串
    """
```

#### evaluate

```python
async def evaluate(self, expected: str, user_input: str, callback=None) -> dict:
    """异步评估听写结果

    Args:
        expected: 期望的正确单词
        user_input: 用户输入的单词
        callback: 用于处理流式输出的回调函数，接收参数：(chunk: str, done: bool)

    Returns:
        dict: 评估结果字典，包含是否正确、错误原因等信息
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

## Modules API

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
```

### utils.extract_json_from_text

```python
def extract_json_from_text(text: str) -> Optional[Any]:
    """尝试从自由文本中提取 JSON 对象并解析，若无法解析返回 None。"""
```

## LearningManager API

LearningManager 是学习模式的核心协调器，整合各个学习相关模块，提供统一的API接口。位于 `core/learning.py`。

### 初始化

```python
def __init__(self, word_manager, audio_player):
    """初始化学习管理器

    Args:
        word_manager: 单词管理器实例
        audio_player: 音频播放器实例
    """
```

### 学习流程方法

#### get_batch

```python
def get_batch(self, batch_size: int = 10) -> List[Dict]:
    """获取学习单词批次

    Args:
        batch_size: 批次大小，默认10个单词

    Returns:
        List[Dict]: 单词列表
    """
```

#### mark_mastered

```python
def mark_mastered(self, word: str):
    """标记单词为已掌握

    Args:
        word: 单词
    """
```

#### mark_review

```python
def mark_review(self, word: str):
    """标记单词需要复习

    Args:
        word: 单词
    """
```

### 进度管理方法

#### save_progress

```python
def save_progress(self, finished=False) -> bool:
    """保存学习进度

    Args:
        finished: 是否完成本批次学习

    Returns:
        bool: 是否保存成功
    """
```

## AudioPlayer API

AudioPlayer 提供单词发音功能，支持缓存管理。

### 初始化

```python
def __init__(self):
    """初始化音频播放器
    """
```

### 发音播放方法

#### play_pronunciation

```python
def play_pronunciation(self, word: str, lang: str = 'en') -> bool:
    """播放单词发音

    Args:
        word: 要播放发音的单词
        lang: 语言代码，默认为英语('en')

    Returns:
        bool: 播放是否成功
    """
```

#### play_chinese_pronunciation

```python
def play_chinese_pronunciation(self, text):
    """播放中文发音

    Args:
        text: 要播放发音的中文文本

    Returns:
        bool: 播放是否成功
    """
```

### 状态检查方法

#### is_available

```python
def is_available(self):
    """检查音频播放功能是否可用

    Returns:
        bool: 功能可用返回True
    """
```

### 管理方法

#### install_requirements

```python
def install_requirements(self):
    """安装必要的依赖

    Returns:
        bool: 安装是否成功
    """
```

#### cleanup

```python
def cleanup(self):
    """清理临时文件
    """
```

#### cleanup_cache

```python
def cleanup_cache(self):
    """清理过期的缓存文件
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

## 统计模块

统计模块提供全面的学习统计功能，包括单词学习统计、练习进度统计、每日学习情况统计和学习趋势分析。

### StatisticsManager 类

`StatisticsManager` 是统计模块的核心类，负责处理所有学习统计相关功能。

#### 初始化

```python
def __init__(self, db_manager: DatabaseManager):
    """初始化统计管理器
    
    Args:
        db_manager: 数据库管理器实例
    """
```

#### get_total_word_count

```python
def get_total_word_count(self) -> int:
    """获取总单词数
    
    Returns:
        int: 总单词数
    """
```

#### get_learned_word_count

```python
def get_learned_word_count(self) -> int:
    """获取已学习单词数
    
    Returns:
        int: 已学习单词数（熟练度大于0的单词）
    """
```

#### get_total_practice_count

```python
def get_total_practice_count(self) -> int:
    """获取总练习次数
    
    Returns:
        int: 总练习次数
    """
```

#### get_total_correct_count

```python
def get_total_correct_count(self) -> int:
    """获取总正确次数
    
    Returns:
        int: 总正确次数
    """
```

#### get_overall_accuracy

```python
def get_overall_accuracy(self) -> float:
    """获取总体正确率
    
    Returns:
        float: 总体正确率（0.0-1.0）
    """
```

#### get_daily_stats

```python
def get_daily_stats(self, date: Optional[str] = None) -> Dict:
    """获取每日学习统计
    
    Args:
        date: 指定日期（格式：YYYY-MM-DD），默认获取今日统计
    
    Returns:
        Dict: 每日统计信息
    """
```

#### get_weekly_stats

```python
def get_weekly_stats(self) -> List[Dict]:
    """获取最近7天的学习统计
    
    Returns:
        List[Dict]: 包含最近7天统计信息的列表
    """
```

#### get_proficiency_stats

```python
def get_proficiency_stats(self) -> Dict[str, int]:
    """获取熟练度分布统计
    
    Returns:
        Dict: 各熟练度区间的单词数量
    """
```

#### get_word_set_stats

```python
def get_word_set_stats(self, set_id: Optional[int] = None) -> Dict:
    """获取词库统计信息
    
    Args:
        set_id: 词库ID，默认获取所有词库统计
    
    Returns:
        Dict: 词库统计信息
    """
```

#### get_recent_progress

```python
def get_recent_progress(self, limit: int = 10) -> List[Dict]:
    """获取最近的学习进度记录
    
    Args:
        limit: 返回记录数限制，默认10条
    
    Returns:
        List[Dict]: 最近的学习进度记录
    """
```

#### get_summary_stats

```python
def get_summary_stats(self) -> Dict:
    """获取综合统计信息
    
    Returns:
        Dict: 综合统计信息
    """
```
