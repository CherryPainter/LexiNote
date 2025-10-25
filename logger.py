import logging
import datetime
import os

# 确保日志目录存在
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录器
logger = logging.getLogger('lexinote')
logger.setLevel(logging.INFO)

# 创建日志文件名
log_file = os.path.join(log_dir, f'lexinote_{datetime.datetime.now().strftime("%Y-%m-%d")}.log')

# 创建文件处理器
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_info(message):
    """记录信息级别日志"""
    logger.info(message)


def log_error(message):
    """记录错误级别日志"""
    logger.error(message)


def log_warning(message):
    """记录警告级别日志"""
    logger.warning(message)


def log_debug(message):
    """记录调试级别日志"""
    logger.debug(message)


def log_exercise_start(exercise_type):
    """记录练习开始"""
    logger.info(f"开始 {exercise_type} 练习")


def log_wrong_word(word, user_input):
    """记录错误单词"""
    logger.info(f"错误单词: {word}, 用户输入: {user_input}")


def log_translation_failure(word):
    """记录翻译失败"""
    logger.error(f"翻译失败: {word}")