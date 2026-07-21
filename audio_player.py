import os
import tempfile
import asyncio
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

        说明：仅使用 edge-tts（微软 Edge 神经语音，免费、无需 API key、国内通常可达、
        音质好）作为发音后端。不再使用 gTTS（连 Google 端点，国内不可达、每次白等超时），
        也不做离线 pyttsx3 兜底。edge-tts 未安装或连接失败时直接返回 False。
        """
        if not word:
            log_error("播放失败：单词为空")
            return False

        # 仅使用 edge-tts 发音
        if self._play_edge_tts(word, lang):
            return True

        log_error(f"播放单词发音失败: {word}")
        return False

    def _run_async(self, coro):
        """在同步上下文中运行协程。Tkinter 回调内无 asyncio 事件循环，直接 asyncio.run；
        万一已有 running loop（防御性），则临时新建 loop 执行后再关闭。"""
        try:
            asyncio.run(coro)
        except RuntimeError as e:
            if "already running" in str(e):
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(coro)
                finally:
                    loop.close()
            else:
                raise

    def _play_edge_tts(self, word: str, lang: str = 'en') -> bool:
        """在线发音（edge-tts）：微软 Edge 神经语音，免费、无需 API key、国内通常可达、
        音质优于系统离线语音。失败（未安装/网络不通）时返回 False，由调用方继续回退。

        Args:
            word: 要发音的文本
            lang: 语言代码（'en' / 'zh-cn' 等）

        Returns:
            bool: 发音是否成功
        """
        try:
            import edge_tts  # noqa
        except Exception:
            # 未安装 edge-tts：明确提示，方便用户排查（否则界面只是无声）
            log_error("发音失败：未安装 edge-tts，请执行 pip install edge-tts")
            return False

        # 根据语言选择神经语音
        if str(lang).startswith('zh'):
            voice = 'zh-CN-XiaoxiaoNeural'
        else:
            voice = 'en-US-AriaNeural'

        # 缓存 key 加 edge- 前缀，避免与 gTTS 缓存冲突
        cache_voice = f"edge-{lang}"

        try:
            # 优先命中缓存
            if self.cache_manager:
                try:
                    cached_file = self.cache_manager.get_tts_cache(word, voice=cache_voice)
                    if cached_file:
                        playsound(cached_file)
                        log_info(f"从缓存播放（edge-tts）: {word}")
                        return True
                except Exception:
                    pass

            temp_file = os.path.join(self.temp_dir, f"edge_{abs(hash(word))}_{lang}.mp3")
            self.temp_files.append(temp_file)

            async def _gen():
                communicate = edge_tts.Communicate(word, voice)
                await communicate.save(temp_file)

            self._run_async(_gen())

            # 校验是否生成了有效音频
            if not (os.path.exists(temp_file) and os.path.getsize(temp_file) > 0):
                return False

            # 写入缓存（优先全局 CacheManager）
            cached_file = None
            if self.cache_manager:
                try:
                    with open(temp_file, 'rb') as f:
                        audio_bytes = f.read()
                    cached_file = self.cache_manager.set_tts_cache(word, audio_bytes, voice=cache_voice)
                except Exception:
                    cached_file = None

            playsound(cached_file or temp_file)
            log_info(f"edge-tts 播放单词发音: {word} (voice={voice})")
            return True
        except Exception as e:
            log_info(f"edge-tts 发音不可用（{word}），继续回退: {str(e)}")
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
        """检查音频播放功能是否可用：playsound 与 edge-tts 均存在。"""
        try:
            import playsound  # noqa
        except ImportError:
            log_error("音频播放功能不可用：缺少 playsound")
            return False
        try:
            import edge_tts  # noqa
            return True
        except ImportError:
            log_error("音频播放功能不可用：缺少 edge-tts，请执行 pip install edge-tts")
            return False

    def install_requirements(self):
        """安装必要的依赖

        Returns:
            bool: 安装是否成功
        """
        try:
            import subprocess
            import sys

            # 安装playsound（音频播放）
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playsound'])

            # 安装edge-tts（微软 Edge 神经语音，免费、无需 API key、国内可达，唯一发音后端）
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'edge-tts'])

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
