import os
import logging
import datetime

# 日志级别映射
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}


class Logger:
    """
    日志管理器类，负责配置和处理应用程序日志
    """

    def __init__(self, log_dir: str = 'data/logs', log_level: str = 'INFO'):
        """
        初始化日志管理器

        Args:
            log_dir: 日志文件保存目录
            log_level: 日志级别，默认为INFO
        """
        self.log_dir = log_dir
        self.log_level = LOG_LEVEL_MAP.get(log_level.upper(), logging.INFO)

        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)

        # 配置日志记录器
        self.logger = logging.getLogger('LexiNote')
        self.logger.setLevel(self.log_level)

        # 清除已有的处理器，避免重复配置
        self.logger.handlers.clear()

        # 设置处理器
        self._setup_handlers()

    def _setup_handlers(self):
        """
        设置日志处理器，包括控制台和文件处理器
        """
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        log_file = os.path.join(
            self.log_dir,
            f'lexinote_{datetime.datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def info(self, message: str):
        """
        记录INFO级别的日志

        Args:
            message: 日志消息
        """
        self.logger.info(message)

    def error(self, message: str):
        """
        记录ERROR级别的日志

        Args:
            message: 日志消息
        """
        self.logger.error(message)

    def warning(self, message: str):
        """
        记录WARNING级别的日志

        Args:
            message: 日志消息
        """
        self.logger.warning(message)

    def debug(self, message: str):
        """
        记录DEBUG级别的日志

        Args:
            message: 日志消息
        """
        self.logger.debug(message)

    def log_exercise_start(self, mode: str, word_count: int):
        """
        记录练习开始日志

        Args:
            mode: 练习模式
            word_count: 单词数量
        """
        self.info(f"开始{mode}练习，共{word_count}词")

    def log_exercise_end(self, mode, correct_count, total_count):
        """
        记录练习结束日志

        Args:
            mode: 练习模式
            correct_count: 正确数量
            total_count: 总数量
        """
        # 计算正确率，避免除以零错误
        if total_count > 0:
            accuracy = (correct_count / total_count) * 100
        else:
            accuracy = 0
        # 将日志消息拆分为更小的部分以符合PEP8行长度限制
        log_msg = f"{mode}练习结束，正确率: "
        log_msg += f"{accuracy:.1f}% ({correct_count}/{total_count})"
        self.info(log_msg)

    def log_word_error(self, word: str, user_input: str):
        """
        记录错误单词日志

        Args:
            word: 正确单词
            user_input: 用户输入
        """
        self.warning(f"单词错误: {word} -> {user_input}")

    def log_translation_failure(self, word: str, error_msg: str):
        """
        记录翻译失败日志

        Args:
            word: 单词
            error_msg: 错误信息
        """
        self.error(f"翻译失败 - {word}: {error_msg}")

    def log_word_added(self, word: str, translation: str):
        """
        记录单词添加日志

        Args:
            word: 单词
            translation: 翻译
        """
        self.info(f"添加单词: {word} -> {translation}")

    def log_word_deleted(self, word: str):
        """
        记录单词删除日志

        Args:
            word: 单词
        """
        self.info(f"删除单词: {word}")


# 创建全局日志实例
global_logger = Logger()


# 兼容旧版API的函数
def log_info(message: str):
    global_logger.info(message)


def log_error(message: str):
    global_logger.error(message)


def log_warning(message: str):
    global_logger.warning(message)


def log_debug(message: str):
    global_logger.debug(message)


def log_exercise_start(mode: str, word_count: int):
    global_logger.log_exercise_start(mode, word_count)


def log_exercise_end(mode: str, correct_count: int, total_count: int):
    global_logger.log_exercise_end(mode, correct_count, total_count)


def log_word_error(word: str, user_input: str):
    global_logger.log_word_error(word, user_input)


def log_wrong_word(word: str, user_input: str):
    """
    记录单词错误日志（向后兼容函数）

    Args:
        word: 正确单词
        user_input: 用户输入
    """
    # 保持向后兼容性，内部调用log_word_error
    log_word_error(word, user_input)


def log_translation_failure(word: str, error_msg: str):
    global_logger.log_translation_failure(word, error_msg)


def log_word_added(word: str, translation: str):
    global_logger.log_word_added(word, translation)


def log_word_deleted(word: str):
    global_logger.log_word_deleted(word)
