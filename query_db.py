import sqlite3
import os

# 连接数据库
db_path = os.path.join('data', 'lexinote.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询test_ai_new单词的所有字段
cursor.execute('SELECT * FROM words WHERE word = ?', ('test_ai_new',))
row = cursor.fetchone()

if row:
    # 获取列名
    columns = [desc[0] for desc in cursor.description]
    
    # 创建字典
    word_data = dict(zip(columns, row))
    
    # 打印所有字段
    print('数据库中单词的所有字段:')
    for key, value in word_data.items():
        print(f'{key}: {value}')
    
    # 特别检查example_translation字段
    print(f'\nexample_translation字段值: {word_data.get("example_translation")}')
    print(f'example_translation字段类型: {type(word_data.get("example_translation"))}')
else:
    print('未找到单词')

conn.close()