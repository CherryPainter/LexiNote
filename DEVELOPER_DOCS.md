# 开发者文档

## 1. 项目概述
LexiNote 是一个个人英语学习工具，帮助用户管理单词库、学习单词和跟踪学习进度。

## 2. 版本历史

### v1.7.0 - 2025-11-13
- **功能增强**: 
  - AI补全单词属性功能增加了例句翻译字段(example_translation)
  - 修复了AI补全按钮显示"没有需要补全的"的问题
- **数据库更新**: 
  - 在words表中添加了example_translation字段
  - 更新了数据库迁移逻辑以支持新字段
  - 在update_word方法中添加了example_translation到valid_fields列表
- **AI响应解析改进**: 
  - 增强了JSON解析逻辑，处理转义下划线等特殊字符
  - 优化了AI响应提取流程，提高解析成功率
- **测试改进**: 创建了AI补全功能测试脚本，验证所有属性的完整性
- **Bug修复**: 
  - 修复了`get_words_missing_details`方法只检查空字符串而不检查NULL值的问题
  - 更新了SQL查询条件，同时检查NULL值和空字符串以正确识别需要补全的单词
  - 修复了ai_complete_word_details方法中只检查空字符串而忽略NULL值的问题，确保补全的单词信息能正确存入数据库

### v1.1.0 - 2025-11-13
- **重构单词学习模块**：将 LearningManager 拆分为多个独立组件，提高代码可维护性
- **新增组件**：
  - ForgettingCurve：实现艾宾浩斯遗忘曲线算法
  - WordSelector：负责单词选择和批次生成
  - LearningProgress：管理学习进度和统计信息
  - LearningScheduler：处理学习计划和调度
- **优化API**：简化 LearningManager 的初始化和方法调用
- **改进UI交互**：确保 LearningPage 与重构后的 API 兼容

### v1.0.0 - 初始版本
- 实现基本的单词管理功能
- 支持学习模式和测试模式
- 提供单词发音和例句功能
- 支持学习进度跟踪

## 3. 项目结构

```
LexiNote/
├── core/                  # 核心业务逻辑
│   ├── __init__.py
│   ├── learning.py        # 学习模块（重构后）
│   ├── word_manager.py    # 单词管理器
│   └── settings.py        # 设置管理器
├── ui/                    # 用户界面
│   ├── __init__.py
│   ├── main_window.py     # 主窗口
│   ├── learning_page.py   # 学习模式页面
│   ├── test_page.py       # 测试模式页面
│   └── components/        # UI组件
├── data/                  # 数据存储
├── utils/                 # 工具函数
│   ├── __init__.py
│   ├── audio_player.py    # 音频播放
│   └── logger.py          # 日志记录
├── main.py                # 程序入口
├── requirements.txt       # 依赖项
└── DEVELOPER_DOCS.md      # 开发者文档
```

## 4. 核心模块说明

### 4.1 学习模块 (core/learning.py)

#### 组件结构
- **ForgettingCurve**：计算单词的遗忘曲线和复习时间
- **WordSelector**：从单词库中选择合适的单词生成学习批次
- **LearningProgress**：管理学习进度、统计信息和保存/加载功能
- **LearningScheduler**：处理学习计划和调度
- **LearningManager**：整合所有组件，提供统一的学习接口

#### API 说明
```python
# 初始化
learning_manager = LearningManager(word_manager, audio_player)

# 获取学习批次
batch = learning_manager.get_batch(batch_size=10)

# 标记单词掌握度
learning_manager.mark_mastered(word)
learning_manager.mark_review(word)

# 保存和加载进度
learning_manager.save_progress(finished=True)
learning_manager.load_daily_progress()

# 获取统计信息
stats = learning_manager.get_current_stats()
```

## 5. 开发规范

### 5.1 命名规范
- 文件名：小写 + 下划线（如 `word_manager.py`）
- 变量名和函数名：小写 + 下划线（如 `get_random_word()`）
- 类名：PascalCase（如 `WordManager`）

### 5.2 代码质量
- 所有代码必须符合 PEP8 规范
- 使用 flake8 检查代码质量
- 为所有类和方法添加详细注释

### 5.3 数据管理
- 所有用户数据统一保存在 `data/` 目录下
- 使用相对路径访问数据文件
- 写入 JSON 前必须先读取并合并旧数据，避免覆盖

### 5.4 错误处理
- 所有用户输入和外部调用需 try/except 捕获
- 不在 AI 逻辑中直接 exit() 程序
- 所有重要操作写入日志

## 6. 测试说明

### 6.1 单元测试
- 为核心功能编写单元测试
- 测试覆盖主要业务逻辑

### 6.2 集成测试
- 测试模块之间的交互
- 确保 UI 与业务逻辑正确集成

## 7. 部署说明

### 7.1 依赖安装
```bash
pip install -r requirements.txt
```

### 7.2 运行程序
```bash
python -m main
```

## 8. 未来计划

- 增加更多学习模式（如拼写练习、听力练习）
- 改进遗忘曲线算法
- 支持单词分类和标签
- 添加学习统计图表
