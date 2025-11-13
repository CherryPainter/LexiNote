from word_manager import WordManager

# 创建WordManager实例
word_manager = WordManager()

# 调用get_words_missing_details方法
words_to_complete = word_manager.get_words_missing_details(10)

print(f'找到需要补全的单词数量: {len(words_to_complete)}')

for word in words_to_complete[:5]:  # 只显示前5个
    print(f'Word: {word["word"]}, Example: [{word["example"]}], Phonetic: [{word["phonetic"]}], Tag: [{word["tag"]}], Meaning_en: [{word["meaning_en"]}]')