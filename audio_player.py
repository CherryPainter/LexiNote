import os
import tempfile
from gtts import gTTS
from playsound import playsound
from logger import log_info, log_error
from audio_cache import AudioCache


class AudioPlayer:
    """音频播放器，负责播放单词发音"""
    
    def __init__(self):
        """初始化音频播放器"""
        self.temp_dir = tempfile.gettempdir()
        self.temp_files = []  # 跟踪临时文件
        self._check_and_create_temp_dir()
        
        # 尝试使用全局 CacheManager（如果存在），否则使用本地 AudioCache
        self.cache_manager = None
        try:
            from core.cache_manager import get_cache_manager
            self.cache_manager = get_cache_manager()
            log_info("使用全局 CacheManager 管理音频缓存")
        except Exception:
            # 回退到本地 AudioCache
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache', 'audio')
            self.cache = AudioCache(cache_dir)
            log_info("使用本地 AudioCache 管理音频缓存")
        
    def _check_and_create_temp_dir(self):
        """检查并创建临时目录"""
        try:
            audio_temp_dir = os.path.join(self.temp_dir, 'lexinote_audio')
            if not os.path.exists(audio_temp_dir):
                os.makedirs(audio_temp_dir)
            self.temp_dir = audio_temp_dir
        except Exception as e:
            log_error(f"创建临时目录失败: {str(e)}")
            # 回退到系统临时目录
            self.temp_dir = tempfile.gettempdir()
    
    def play_pronunciation(self, word: str, lang: str = 'en') -> bool:
        """播放单词发音
        
        Args:
            word: 要播放发音的单词
            lang: 语言代码，默认为英语('en')
            
        Returns:
            bool: 播放是否成功
        """
        if not word:
            log_error("播放失败：单词为空")
            return False
            
        if not self.is_available():
            log_error("播放失败：音频播放功能不可用")
            return False
        
        try:
            # 先检查缓存：优先使用全局 CacheManager
            cached_file = None
            if self.cache_manager:
                try:
                    cached_file = self.cache_manager.get_tts_cache(word, voice=lang)
                except Exception:
                    cached_file = None
            else:
                cached_file = self.cache.get_cached_file(word, lang)

            if cached_file:
                playsound(cached_file)
                log_info(f"从缓存播放单词发音: {word}")
                return True
            
            # 如果缓存中没有，生成新的音频文件
            temp_file = os.path.join(
                self.temp_dir, 
                f"temp_{abs(hash(word))}.mp3"
            )
            self.temp_files.append(temp_file)
            
            # 使用gTTS生成语音
            tts = gTTS(text=word, lang=lang, slow=False)
            tts.save(temp_file)
            
            # 添加到缓存（优先使用全局 CacheManager）
            cached_file = None
            if self.cache_manager:
                try:
                    # 读取临时文件字节并交给 CacheManager
                    with open(temp_file, 'rb') as f:
                        audio_bytes = f.read()
                    cached_file = self.cache_manager.set_tts_cache(word, audio_bytes, voice=lang)
                except Exception as e:
                    log_error(f"将音频添加到全局缓存失败: {str(e)}")
                    cached_file = None
            else:
                try:
                    cached_file = self.cache.add_to_cache(word, lang, temp_file)
                except Exception:
                    cached_file = None

            if cached_file:
                # 使用缓存的文件播放
                playsound(cached_file)
            else:
                # 如果缓存失败，使用临时文件
                playsound(temp_file)
            
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
            import gtts  # noqa
            import playsound  # noqa
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
            
    def cleanup(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                log_error(f"清理临时文件失败: {str(e)}")
        self.temp_files.clear()
    
    def cleanup_cache(self):
        """清理过期的缓存文件"""
        if hasattr(self, 'cache'):
            self.cache._validate_cache()
    
    def __del__(self):
        """析构时清理临时文件"""
        self.cleanup()