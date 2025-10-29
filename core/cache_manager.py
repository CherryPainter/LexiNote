"""缓存管理器，负责管理AI生成的翻译和语音文件缓存"""
import os
import shutil
import hashlib
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from logger import log_info, log_error, log_warning


class CacheManager:
    """缓存管理器，提供文件缓存和内存缓存功能"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化缓存管理器"""
        # 确保只初始化一次
        with self._lock:
            if not hasattr(self, '_initialized'):
                # 缓存目录结构
                self.cache_root = 'cache'
                self.text_cache_dir = os.path.join(self.cache_root, 'ai_text')
                self.tts_cache_dir = os.path.join(self.cache_root, 'ai_tts')
                self.history_file = os.path.join(self.cache_root, 'ai_history.json')
                
                # 内存缓存
                self._memory_cache = {}  # 用于临时缓存
                self._cache_lock = threading.RLock()
                
                # 初始化缓存目录
                self._initialize_cache_directories()
                
                # 启动自动清理线程
                self._cleanup_interval = 24 * 3600  # 24小时
                self._stop_cleanup = False
                self._start_auto_cleanup()
                
                self._initialized = True
    
    def _initialize_cache_directories(self):
        """初始化缓存目录结构"""
        directories = [self.cache_root, self.text_cache_dir, self.tts_cache_dir]
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                log_info(f"初始化缓存目录: {directory}")
            except Exception as e:
                log_error(f"初始化缓存目录 {directory} 失败: {str(e)}")
    
    def _generate_cache_key(self, content: str) -> str:
        """生成缓存键
        
        Args:
            content: 内容字符串
            
        Returns:
            缓存键（MD5哈希值）
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_text_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """获取文本缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存数据，如果不存在返回None
        """
        # 先查内存缓存
        with self._cache_lock:
            if key in self._memory_cache:
                return self._memory_cache[key]
        
        # 查文件缓存
        cache_file = os.path.join(self.text_cache_dir, f"{self._generate_cache_key(key)}.json")
        if os.path.exists(cache_file):
            try:
                import json
                # 读取文件并更新访问时间/内存缓存时加锁，避免并发写入导致不一致
                with self._cache_lock:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    try:
                        os.utime(cache_file, None)
                    except Exception:
                        pass
                    # 更新内存缓存
                    self._memory_cache[key] = data

                return data
            except Exception as e:
                log_error(f"读取文本缓存失败: {str(e)}")
        
        return None
    
    def set_text_cache(self, key: str, data: Dict[str, Any], ttl: int = 30 * 24 * 3600):
        """设置文本缓存
        
        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 缓存过期时间（秒），默认30天
        """
        try:
            # 添加元数据
            cache_data = {
                'data': data,
                'created_at': datetime.now().isoformat(),
                'ttl': ttl,
                'access_count': 0
            }

            cache_file = os.path.join(self.text_cache_dir, f"{self._generate_cache_key(key)}.json")

            # 更新内存缓存并原子写入文件
            import json
            with self._cache_lock:
                self._memory_cache[key] = cache_data
                # 原子写法：先写入临时文件，再替换目标文件
                tmp_file = cache_file + '.tmp'
                with open(tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                try:
                    os.replace(tmp_file, cache_file)
                except Exception:
                    # 备用为os.rename
                    try:
                        os.rename(tmp_file, cache_file)
                    except Exception:
                        # 最后尝试直接写
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            log_error(f"保存文本缓存失败: {str(e)}")
    
    def get_tts_cache(self, text: str, voice: str = 'default') -> Optional[str]:
        """获取语音缓存
        
        Args:
            text: 文本内容
            voice: 语音类型
            
        Returns:
            缓存文件路径，如果不存在返回None
        """
        key = f"{voice}:{text}"
        cache_file = os.path.join(self.tts_cache_dir, f"{self._generate_cache_key(key)}.mp3")
        
        if os.path.exists(cache_file):
            try:
                # 更新访问时间时加锁，避免与清理/写入竞争
                with self._cache_lock:
                    try:
                        os.utime(cache_file, None)
                    except Exception:
                        pass
                return cache_file
            except Exception as e:
                log_error(f"访问语音缓存失败: {str(e)}")
        
        return None
    
    def set_tts_cache(self, text: str, audio_data: bytes, voice: str = 'default') -> Optional[str]:
        """设置语音缓存
        
        Args:
            text: 文本内容
            audio_data: 音频数据
            voice: 语音类型
            
        Returns:
            缓存文件路径，如果失败返回None
        """
        try:
            key = f"{voice}:{text}"
            cache_file = os.path.join(self.tts_cache_dir, f"{self._generate_cache_key(key)}.mp3")

            # 原子写入：先写入临时文件，然后原子替换
            tmp_file = cache_file + '.tmp'
            with self._cache_lock:
                with open(tmp_file, 'wb') as f:
                    f.write(audio_data)
                try:
                    os.replace(tmp_file, cache_file)
                except Exception:
                    try:
                        os.rename(tmp_file, cache_file)
                    except Exception:
                        # 如果替换失败，尽量清理临时文件并返回None
                        try:
                            if os.path.exists(tmp_file):
                                os.remove(tmp_file)
                        except Exception:
                            pass
                        log_error("保存语音缓存时替换文件失败")
                        return None

            return cache_file

        except Exception as e:
            log_error(f"保存语音缓存失败: {str(e)}")
            return None
    
    def record_ai_history(self, operation: str, input_text: str, response: str):
        """记录AI调用历史
        
        Args:
            operation: 操作类型（translate/example/tts/evaluate）
            input_text: 输入文本
            response: AI响应
        """
        try:
            import json

            # 读取/写入历史时加锁，避免并发读写导致损坏
            with self._cache_lock:
                history = []
                if os.path.exists(self.history_file):
                    try:
                        with open(self.history_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        history = []

                # 添加新记录
                new_record = {
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation,
                    'input': input_text[:200],  # 限制长度
                    'response': response[:500]  # 限制长度
                }

                history.append(new_record)

                # 只保留最近的1000条记录
                history = history[-1000:]

                # 原子写入历史文件
                tmp_file = self.history_file + '.tmp'
                with open(tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                try:
                    os.replace(tmp_file, self.history_file)
                except Exception:
                    try:
                        os.rename(tmp_file, self.history_file)
                    except Exception:
                        log_error('保存AI历史记录时替换文件失败')

        except Exception as e:
            log_error(f"记录AI历史失败: {str(e)}")
    
    def clean_old_cache(self, days: int = 30):
        """清理过期缓存
        
        Args:
            days: 保留天数，超过此天数的缓存将被清理
        """
        try:
            now = time.time()
            cutoff_time = now - (days * 24 * 3600)
            
            # 清理文本缓存
            text_removed = self._clean_directory(self.text_cache_dir, cutoff_time)
            
            # 清理语音缓存
            tts_removed = self._clean_directory(self.tts_cache_dir, cutoff_time)
            
            # 清理内存缓存
            self._clean_memory_cache()
            
            log_info(f"缓存清理完成: 移除文本缓存 {text_removed} 个，语音缓存 {tts_removed} 个")
            
        except Exception as e:
            log_error(f"清理缓存失败: {str(e)}")
    
    def _clean_directory(self, directory: str, cutoff_time: float) -> int:
        """清理指定目录中的过期文件
        
        Args:
            directory: 目录路径
            cutoff_time: 截止时间戳
            
        Returns:
            移除的文件数量
        """
        removed_count = 0
        
        if not os.path.exists(directory):
            return 0
        
        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_mtime = os.path.getmtime(filepath)
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
        except Exception as e:
            log_error(f"清理目录 {directory} 失败: {str(e)}")
        
        return removed_count
    
    def _clean_memory_cache(self):
        """清理内存缓存，保留最近使用的缓存项"""
        with self._cache_lock:
            # 保留前500个项
            if len(self._memory_cache) > 500:
                # 按访问时间排序（这里简化处理，保留最近添加的）
                # 实际项目中可以记录每个缓存项的访问时间
                keys_to_keep = list(self._memory_cache.keys())[-500:]
                self._memory_cache = {k: v for k, v in self._memory_cache.items() if k in keys_to_keep}
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        try:
            # 文本缓存数量
            text_count = len([f for f in os.listdir(self.text_cache_dir) if f.endswith('.json')])
            
            # 语音缓存数量
            tts_count = len([f for f in os.listdir(self.tts_cache_dir) if f.endswith('.mp3')])
            
            # 内存缓存数量
            memory_count = len(self._memory_cache)
            
            return {
                'text_cache_count': text_count,
                'tts_cache_count': tts_count,
                'memory_cache_count': memory_count,
                'total_cache_count': text_count + tts_count + memory_count
            }
            
        except Exception as e:
            log_error(f"获取缓存统计失败: {str(e)}")
            return {
                'text_cache_count': 0,
                'tts_cache_count': 0,
                'memory_cache_count': 0,
                'total_cache_count': 0
            }
    
    def _start_auto_cleanup(self):
        """启动自动清理线程"""
        def cleanup_thread():
            while not self._stop_cleanup:
                try:
                    # 等待指定的清理间隔
                    time.sleep(self._cleanup_interval)
                    # 执行清理
                    self.clean_old_cache()
                except Exception as e:
                    log_error(f"自动清理线程错误: {str(e)}")
                    # 避免错误后立即重试，等待一段时间
                    time.sleep(3600)  # 等待1小时
        
        # 启动线程
        thread = threading.Thread(target=cleanup_thread, daemon=True)
        thread.start()
        log_info("自动清理线程已启动")
    
    def clear_all_cache(self):
        """清除所有缓存"""
        try:
            # 清除内存缓存
            with self._cache_lock:
                self._memory_cache.clear()
            
            # 清除文本缓存
            if os.path.exists(self.text_cache_dir):
                shutil.rmtree(self.text_cache_dir)
                os.makedirs(self.text_cache_dir, exist_ok=True)
            
            # 清除语音缓存
            if os.path.exists(self.tts_cache_dir):
                shutil.rmtree(self.tts_cache_dir)
                os.makedirs(self.tts_cache_dir, exist_ok=True)
            
            # 清除历史记录
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            
            log_info("所有缓存已清除")
            
        except Exception as e:
            log_error(f"清除所有缓存失败: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        self._stop_cleanup = True
        log_info("缓存管理器资源清理完成")


# 全局缓存管理器实例
cache_manager = None

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例
    
    Returns:
        缓存管理器实例
    """
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
    return cache_manager