# 听写练习模块重构计划

## 1. 现有系统分析

### 1.1 数据库结构
- **dictation_history**：记录听写历史，包括单词、用户输入、是否正确、相似度、练习日期
- **exercise_sessions**：记录练习会话，包括练习类型、开始时间、结束时间
- **progress**：记录单词学习进度，用于计算熟练度
- **words**：存储单词信息，包括熟练度字段

### 1.2 核心功能
- 支持单个听写和队列听写模式
- 支持不同单词来源（今日学习、全词库随机、熟词库）
- 自动发音播放
- 答案检查和结果记录
- 基本的统计功能

### 1.3 用户界面
- 模式选择界面
- 练习界面（播放按钮、输入框、检查/跳过/退出按钮）
- 结果显示

## 2. 重构目标

### 2.1 功能增强
- ✅ 完善会话管理，记录练习会话详情
- ✅ 实现个性化单词选择算法
- ✅ 增强进度跟踪和统计功能
- ✅ 添加错误单词自动复习机制
- ✅ 支持设置每日听写目标
- ✅ 实现多难度级别

### 2.2 用户体验改进
- ✅ 提供实时详细反馈
- ✅ 显示练习进度和正确率
- ✅ 支持暂停/继续功能
- ✅ 增强统计图表展示
- ✅ 提供个性化设置选项

### 2.3 代码优化
- ✅ 分离数据访问层和业务逻辑
- ✅ 优化异步操作性能
- ✅ 增强错误处理和日志记录
- ✅ 提高代码可维护性和扩展性

## 3. 数据库结构优化

### 3.1 增强 dictation_history 表
```sql
ALTER TABLE dictation_history ADD COLUMN session_id INTEGER REFERENCES exercise_sessions(id);
```

### 3.2 增强 exercise_sessions 表
```sql
ALTER TABLE exercise_sessions ADD COLUMN duration INTEGER;
ALTER TABLE exercise_sessions ADD COLUMN total_words INTEGER;
ALTER TABLE exercise_sessions ADD COLUMN correct_words INTEGER;
ALTER TABLE exercise_sessions ADD COLUMN accuracy FLOAT;
ALTER TABLE exercise_sessions ADD COLUMN source TEXT;
ALTER TABLE exercise_sessions ADD COLUMN mode TEXT;
```

### 3.3 添加 dictation_settings 表
```sql
CREATE TABLE IF NOT EXISTS dictation_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER DEFAULT 1,
    auto_play BOOLEAN DEFAULT 1,
    play_interval INTEGER DEFAULT 3000,
    difficulty_level TEXT DEFAULT 'medium',
    daily_target INTEGER DEFAULT 20,
    review_frequency INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. 功能模块设计

### 4.1 会话管理模块
- `start_session()`：开始新的练习会话
- `end_session()`：结束当前练习会话并保存统计信息
- `get_current_session()`：获取当前会话信息

### 4.2 单词选择模块
- `select_word()`：基于用户历史和熟练度智能选择单词
- `select_words_batch()`：选择一批单词用于队列听写
- `select_review_words()`：选择需要复习的错误单词

### 4.3 进度跟踪模块
- `record_result()`：记录听写结果
- `update_progress()`：更新单词熟练度
- `get_stats()`：获取详细的统计信息
- `get_daily_progress()`：获取每日学习进度

### 4.4 用户设置模块
- `get_settings()`：获取用户听写设置
- `save_settings()`：保存用户听写设置

## 5. 用户界面优化

### 5.1 练习界面增强
- 添加进度条显示完成进度
- 显示当前会话的正确率
- 添加暂停/继续按钮
- 提供拼写建议功能

### 5.2 统计界面
- 显示每日/每周/每月学习统计
- 展示错误单词频率图表
- 显示学习趋势图
- 提供详细的会话历史记录

### 5.3 设置界面
- 允许自定义发音播放间隔
- 支持设置练习难度
- 允许设置每日听写目标
- 提供复习频率设置

## 6. 实施计划

### 6.1 第一阶段：数据库结构更新
- 更新现有表结构
- 创建新的设置表
- 迁移现有数据

### 6.2 第二阶段：核心功能实现
- 实现会话管理功能
- 优化单词选择算法
- 增强进度跟踪功能

### 6.3 第三阶段：用户界面优化
- 更新练习界面
- 添加统计界面
- 实现设置界面

### 6.4 第四阶段：测试和优化
- 进行功能测试
- 性能优化
- 用户体验测试

## 7. 预计收益

### 7.1 功能提升
- 更智能的单词选择
- 更完善的进度跟踪
- 个性化的练习体验

### 7.2 用户体验改进
- 更直观的界面设计
- 更详细的反馈信息
- 更灵活的设置选项

### 7.3 代码质量提升
- 更好的代码组织
- 更高的可维护性
- 更强的扩展性