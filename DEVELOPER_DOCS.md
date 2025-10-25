# LexiNote - 开发者文档

## 版本历史

## v1.1.3 (当前版本)

### 修复内容
- 修复LearningManager中的get_word_definition方法，确保正确获取单词释义
- 解决GUI无法显示单词学习内容的问题
- 实现专门的测试脚本验证学习模式功能
- 在main_window.py中添加了pack(fill=tk.BOTH, expand=True)使LearningPage正确显示

## v1.1.1

### 修复内容
- 修复LearningManager初始化依赖问题，解决'WordManager' object has no attribute 'scheduler'错误
- 改进依赖注入机制，使LearningManager能正确使用WordManager提供的功能
- 优化日志处理，添加LoggerWrapper确保日志记录正常工作
- 修复数据文件路径问题，确保正确读取和保存数据

### v1.1.0
- 添加学习模式功能，实现主动单词记忆
- 创建 core/learning.py 核心逻辑模块
- 创建 ui/learning_page.py 用户界面模块
- 新增 word_progress.json 数据文件存储学习进度
- 实现基于掌握度的权重调整算法
- 更新主界面导航菜单，优化用户体验

### v1.0.0 (2025-10-25)
- 初始版本发布
- 实现核心功能模块
  - 单词管理器 (WordManager)
  - 音频播放器 (AudioPlayer)
  - 日志系统 (Logger)
- 用户界面实现
  - 主窗口
  - 听写练习页面
  - 翻译练习页面
  - 单词复习页面
- 智能权重算法实现
- 数据持久化存储

## 核心逻辑设计

### 1. 单词管理系统

### 2. LearningManager
新增的学习模式管理器，负责主动学习流程控制、掌握度管理和权重调整。
- `get_batch(batch_size)`: 获取学习单词批次
- `mark_mastered(word)`: 标记单词为已掌握，调整权重和掌握度分数
- `mark_review(word)`: 标记单词需复习，调整权重和掌握度分数
- `play_pronunciation(word)`: 播放单词发音
- `save_progress()`: 保存学习进度并执行日衰减

#### 数据结构
- `word_dict.json`: 存储单词和翻译的映射关系
- `word_weights.json`: 存储单词的权重值
- `wrong_words.json`: 记录错误单词和错误次数
- `progress.json`: 记录学习进度统计信息
- `word_progress.json`: 新增文件，存储单词的学习进度信息：
  - `learned`: 是否已学习
  - `last_learned`: 最后学习时间
  - `mastery_score`: 掌握度分数（0.0-1.0）

#### 核心算法
- **权重计算**: 基于用户回答正确性动态调整单词权重
- **随机抽词**: 根据权重概率分布抽取单词，权重越高抽中概率越大
- **模糊匹配**: 翻译练习中使用的容错匹配算法
- **掌握度算法**: 
  - 标记已掌握：mastery_score = min(1.0, mastery_score + 0.25)
  - 标记需复习：mastery_score = max(0.0, mastery_score - 0.1)
  - 日衰减：weight = weight * 0.98（模拟遗忘过程）

### 2. 权重算法实现

```python
# 初始权重为1.0
# 错误时: 权重 += 0.5
# 正确时: 权重 *= 0.8 (最低权重限制为0.1)
# 每日衰减: 权重 *= 1.1 (最高权重限制为5.0)
```

### 3. 用户界面架构

采用模块化设计，主窗口通过Frame切换不同功能页面：
- `MainWindow`: 主窗口框架，负责页面切换和导航
- `LearningPage`: 新增的学习模式页面，实现单词学习的用户界面：
  - 单词卡片展示
  - 发音播放功能
  - 掌握度标记按钮
  - 批次学习流程控制
  - 键盘快捷操作支持
- `DictationPage`: 听写练习页面
- `TranslationPage`: 翻译练习页面
- `ReviewPage`: 单词复习页面

每个页面独立实现其功能，但共享WordManager实例。

## 关键模块说明

### WordManager

**主要职责**:
- 单词的增删改查操作
- 权重计算和管理
- 学习进度跟踪
- 数据持久化

**关键方法**:
- `add_word()`: 添加新单词
- `get_word_by_weight()`: 基于权重随机获取单词
- `update_word_weight()`: 更新单词权重
- `check_spelling()/check_translation()`: 验证答案

### AudioPlayer

**主要职责**:
- 使用gTTS生成单词语音
- 播放单词发音
- 管理临时音频文件

**关键方法**:
- `play_pronunciation()`: 播放英文单词发音
- `play_chinese_pronunciation()`: 播放中文发音
- `is_available()`: 检查音频功能可用性

### Logger

**主要职责**:
- 记录系统操作日志
- 记录错误信息
- 按日期保存日志文件

**关键方法**:
- `log_info()/log_error()/log_warning()`: 不同级别的日志记录
- `log_exercise_start()/log_wrong_word()`: 特定事件日志

## 数据一致性保证

- 所有JSON数据写入前先读取并合并旧数据，避免覆盖
- 使用try-except确保文件操作的安全性
- 关键操作记录日志，便于追踪问题

## 性能考虑

- 权重计算采用简单的算术运算，避免复杂计算
- 数据文件使用JSON格式，读写效率高
- 音频文件使用临时文件，避免磁盘占用

## 错误处理

- 所有用户输入都经过验证
- 网络操作（音频生成）有错误处理和重试机制
- 异常情况下提供友好的用户提示

## 安全考虑

- 使用相对路径访问数据文件，避免路径遍历攻击
- 临时文件使用hash命名，避免文件冲突
- 不存储敏感用户信息

## 扩展性设计

- 模块化结构便于添加新功能
- WordManager接口设计支持未来扩展
- UI界面采用Frame切换模式，便于添加新页面

## 未来开发方向

1. **AI集成**: 添加AI辅助翻译和评估功能
2. **数据分析**: 实现学习数据分析和可视化
3. **多用户支持**: 添加用户账户系统
4. **同步功能**: 实现多设备数据同步
5. **扩展练习模式**: 添加更多学习模式（如选择题、填空题等）