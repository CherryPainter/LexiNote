from word_manager import WordManager
import time

# 创建WordManager实例
word_manager = WordManager()

# 先检查当前需要补全的单词
print("===== 当前需要补全的单词 ====")
words_to_complete = word_manager.get_words_missing_details(5)
if not words_to_complete:
    print("没有需要补全的单词")
    exit(1)

# 打印第一个需要补全的单词信息
word = words_to_complete[0]
print(f"将测试补全单词: {word['word']}")
print(f"当前信息: example=[{word['example']}], phonetic=[{word['phonetic']}], tag=[{word['tag']}], meaning_en=[{word['meaning_en']}]")

# 模拟进度回调函数
def progress_callback(current, total, word):
    print(f"进度: {current}/{total} - 正在处理单词: {word}")

# 调用AI补全功能
print("\n===== 开始AI补全 ====")
completed_count = word_manager.ai_complete_word_details(callback=progress_callback)
print(f"补全完成，成功补全 {completed_count} 个单词")

# 延迟一下，确保数据库操作完成
time.sleep(2)

# 检查补全后的结果
print("\n===== 补全后的结果 ====")
# 获取补全后的单词信息
from core.database_manager import DatabaseManager
db = DatabaseManager()
updated_word = db.execute_read(f"SELECT * FROM words WHERE id = {word['id']}")[0]
print(f"单词: {updated_word['word']}")
print(f"example: [{updated_word['example']}]")
print(f"phonetic: [{updated_word['phonetic']}]")
print(f"tag: [{updated_word['tag']}]")
print(f"meaning_en: [{updated_word['meaning_en']}]")

# 验证是否有字段被更新
fields_updated = 0
if updated_word['example'] is not None and updated_word['example'] != '':
    fields_updated += 1
if updated_word['phonetic'] is not None and updated_word['phonetic'] != '':
    fields_updated += 1
if updated_word['tag'] is not None and updated_word['tag'] != '':
    fields_updated += 1
if updated_word['meaning_en'] is not None and updated_word['meaning_en'] != '':
    fields_updated += 1

print(f"\n===== 验证结果 ====")
if fields_updated > 0:
    print(f"✅ 成功！{fields_updated} 个字段被更新到数据库")
else:
    print(f"❌ 失败！没有字段被更新到数据库")