from word_manager import WordManager

# 创建WordManager实例
word_manager = WordManager()

# 查找刚刚补全的单词
word_to_find = "test_ai_final"

# 获取当前激活词库的所有单词
words = word_manager.get_words_from_active_set()

# 查找特定单词
word_data = None
for word in words:
    if word["word"] == word_to_find:
        word_data = word
        break

if word_data:
    print('单词详细信息:')
    print(f'单词: {word_data.get("word")}')
    print(f'音标: {word_data.get("phonetic")}')
    print(f'词性: {word_data.get("tag")}')
    print(f'中文释义: {word_data.get("meaning")}')
    print(f'英语释义: {word_data.get("meaning_en")}')
    print(f'例句: {word_data.get("example")}')
    print(f'例句翻译: {word_data.get("example_translation")}')

    # 测试其他模块是否能获取这些属性
    print('\n验证其他模块是否能访问新属性:')
    # 检查返回的单词数据是否包含所有新属性
    new_attributes = ['phonetic', 'tag', 'meaning_en', 'example', 'example_translation']
    print('返回了所有新属性:', all(attribute in word_data for attribute in new_attributes))
    print('所有新属性都有值:', all(word_data.get(attribute) for attribute in new_attributes))
else:
    print(f'未找到单词: {word_to_find}')