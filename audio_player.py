import os
import tempfile
from gtts import gTTS
from playsound import playsound
from logger import log_info, log_error


class AudioPlayer:
    """音频播放器，负责播放单词发音"""
    
    def __init__(self):
        """初始化音频播放器"""
        self.temp_dir = tempfile.gettempdir()
    
    def play_pronunciation(self, word, lang='en'):
        """播放单词发音
        
        Args:
            word: 要播放发音的单词
            lang: 语言代码，默认为英语('en')
            
        Returns:
            bool: 播放是否成功
        """
        try:
            if not word:
                log_error("播放失败：单词为空")
                return False
            
            # 生成临时音频文件路径
            temp_file = os.path.join(self.temp_dir, f"pronunciation_{hash(word)}.mp3")
            
            # 使用gTTS生成语音
            tts = gTTS(text=word, lang=lang, slow=False)
            tts.save(temp_file)
            
            # 播放语音
            playsound(temp_file)
            
            # 播放完成后删除临时文件
            try:
                os.remove(temp_file)
            except:
                pass  # 忽略删除失败
            
            log_info(f"播放单词发音: {word}")
            return True
        except Exception as e:
            log_error(f"播放单词发音失败: {word}, 错误: {str(e)}")
            return False
    
    def play_chinese_pronunciation(self, text):
        """播放中文发音
        
        Args:
            text: 要播放发音的中文文本
            
        Returns:
            bool: 播放是否成功
        """
        return self.play_pronunciation(text, lang='zh-cn')
    
    def is_available(self):
        """检查音频播放功能是否可用"""
        try:
            # 尝试导入必要的库
            import gtts
            import playsound
            return True
        except ImportError:
            log_error("音频播放功能不可用：缺少必要的库")
            return False
    
    def install_requirements(self):
        """安装必要的依赖
        
        Returns:
            bool: 安装是否成功
        """
        try:
            import subprocess
            import sys
            
            # 安装gTTS
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gTTS'])
            
            # 安装playsound
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playsound'])
            
            log_info("成功安装音频播放依赖")
            return True
        except Exception as e:
            log_error(f"安装音频播放依赖失败: {str(e)}")
            return False