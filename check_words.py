from core.database_manager import DatabaseManager

db = DatabaseManager()
words = db.execute_read('SELECT id, word, example, phonetic, tag, meaning_en FROM words WHERE set_id = 1 LIMIT 10')

for word in words:
    print(f'ID: {word["id"]}, Word: {word["word"]}, Example: [{word["example"]}], Phonetic: [{word["phonetic"]}], Tag: [{word["tag"]}], Meaning_en: [{word["meaning_en"]}]')