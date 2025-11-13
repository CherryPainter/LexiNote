import sqlite3
import os

# 连接到数据库
db_path = os.path.join('data', 'lexinote.db')

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查exercise_sessions表的结构
print("检查exercise_sessions表结构:")
cursor.execute("PRAGMA table_info(exercise_sessions)")
columns = cursor.fetchall()

for col in columns:
    print(f"  {col[1]} - {col[2]}")

conn.close()