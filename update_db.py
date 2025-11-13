import sqlite3
import os

# 连接到数据库
db_path = os.path.join('data', 'lexinote.db')

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("更新exercise_sessions表结构...")

# 检查并添加缺失的列
cursor.execute("PRAGMA table_info(exercise_sessions)")
existing_columns = [col[1] for col in cursor.fetchall()]

# 需要的列及其类型
required_columns = {
    'mode': 'TEXT NOT NULL',
    'source': 'TEXT NOT NULL',
    'difficulty': 'TEXT',
    'batch_size': 'INTEGER',
    'total_words': 'INTEGER',
    'duration': 'INTEGER',
    'correct_words': 'INTEGER',
    'accuracy': 'REAL'
}

# 添加缺失的列
for col_name, col_type in required_columns.items():
    if col_name not in existing_columns:
        if 'NOT NULL' in col_type:
            # 对于NOT NULL列，先添加允许NULL的列，然后设置默认值
            temp_col_type = col_type.replace('NOT NULL', '')
            print(f"  添加列(允许NULL): {col_name}")
            cursor.execute(f"ALTER TABLE exercise_sessions ADD COLUMN {col_name} {temp_col_type}")
            
            # 更新所有行的默认值
            if col_type.startswith('TEXT'):
                default_value = "''"
            elif col_type.startswith('INTEGER'):
                default_value = "0"
            elif col_type.startswith('REAL'):
                default_value = "0.0"
            else:
                default_value = "''"
            
            print(f"  更新默认值: {col_name}")
            cursor.execute(f"UPDATE exercise_sessions SET {col_name} = {default_value}")
        else:
            cursor.execute(f"ALTER TABLE exercise_sessions ADD COLUMN {col_name} {col_type}")
            print(f"  ✓ 添加列: {col_name}")
    else:
        print(f"  ✓ 列已存在: {col_name}")

conn.commit()

# 再次检查表结构
print("\n更新后的表结构:")
cursor.execute("PRAGMA table_info(exercise_sessions)")
columns = cursor.fetchall()

for col in columns:
    print(f"  {col[1]} - {col[2]}")

conn.close()
print("\n数据库表结构更新完成！")