import os
import json
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict
from logger import log_error


class AudioCache:
    """音频缓存管理器"""
    
    def __init__(self, cache_dir: str):
        """初始化音频缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir
        self.index_file = os.path.join(cache_dir, 'cache_index.json')
        self.cache_index: Dict[str, dict] = {}
        self.max_cache_size = 500 * 1024 * 1024  # 500MB
        self.max_file_age = timedelta(days=30)  # 缓存文件最大保存30天
        
        self._init_cache()
    
    def _init_cache(self):
        """初始化缓存系统"""
        try:
            # 创建缓存目录
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            
            # 加载缓存索引
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
            
            # 验证缓存
            self._validate_cache()
            
        except Exception as e:
            log_error(f"初始化音频缓存失败: {str(e)}")
            self.cache_index = {}
    
    def _validate_cache(self):
        """验证缓存文件的完整性并清理过期文件"""
        current_time = datetime.now()
        invalid_keys = []
        
        for key, info in self.cache_index.items():
            file_path = os.path.join(self.cache_dir, info['filename'])
            last_access = datetime.fromisoformat(info['last_access'])
            
            # 检查文件是否存在且未过期
            if not os.path.exists(file_path) or \
               current_time - last_access > self.max_file_age:
                invalid_keys.append(key)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        log_error(f"删除过期缓存文件失败: {file_path}, 错误: {str(e)}")
        
        # 移除无效的缓存记录
        for key in invalid_keys:
            self.cache_index.pop(key, None)
        
        # 保存更新后的索引
        self._save_index()
        
        # 检查缓存大小并清理
        self._check_cache_size()
    
    def _save_index(self):
        """保存缓存索引到文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(f"保存缓存索引失败: {str(e)}")
    
    def _check_cache_size(self):
        """检查并控制缓存大小"""
        try:
            total_size = 0
            files_info = []
            
            # 计算总大小并收集文件信息
            for key, info in self.cache_index.items():
                file_path = os.path.join(self.cache_dir, info['filename'])
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    last_access = datetime.fromisoformat(info['last_access'])
                    files_info.append((key, size, last_access))
                    total_size += size
            
            # 如果超出限制，删除最旧的文件直到低于限制
            if total_size > self.max_cache_size:
                # 按最后访问时间排序
                files_info.sort(key=lambda x: x[2])
                
                for key, size, _ in files_info:
                    if total_size <= self.max_cache_size:
                        break
                        
                    info = self.cache_index[key]
                    file_path = os.path.join(self.cache_dir, info['filename'])
                    
                    try:
                        os.remove(file_path)
                        self.cache_index.pop(key)
                        total_size -= size
                    except Exception as e:
                        log_error(f"删除缓存文件失败: {file_path}, 错误: {str(e)}")
                
                # 保存更新后的索引
                self._save_index()
                
        except Exception as e:
            log_error(f"检查缓存大小时发生错误: {str(e)}")
    
    def get_cached_file(self, text: str, lang: str) -> Optional[str]:
        """获取缓存的音频文件路径
        
        Args:
            text: 要获取缓存的文本
            lang: 语言代码
            
        Returns:
            缓存文件路径，如果不存在则返回None
        """
        cache_key = self._generate_cache_key(text, lang)
        
        if cache_key in self.cache_index:
            info = self.cache_index[cache_key]
            file_path = os.path.join(self.cache_dir, info['filename'])
            
            if os.path.exists(file_path):
                # 更新最后访问时间
                info['last_access'] = datetime.now().isoformat()
                self._save_index()
                return file_path
                
            # 如果文件不存在，删除索引
            self.cache_index.pop(cache_key)
            self._save_index()
        
        return None
    
    def add_to_cache(self, text: str, lang: str, temp_file: str) -> Optional[str]:
        """将临时音频文件添加到缓存
        
        Args:
            text: 生成语音的文本
            lang: 语言代码
            temp_file: 临时文件路径
            
        Returns:
            缓存文件路径，如果添加失败则返回None
        """
        try:
            cache_key = self._generate_cache_key(text, lang)
            filename = f"{cache_key}.mp3"
            cache_path = os.path.join(self.cache_dir, filename)
            
            # 复制文件到缓存目录
            shutil.copy2(temp_file, cache_path)
            
            # 更新缓存索引
            self.cache_index[cache_key] = {
                'filename': filename,
                'text': text,
                'lang': lang,
                'last_access': datetime.now().isoformat()
            }
            
            # 保存索引
            self._save_index()
            
            # 检查缓存大小
            self._check_cache_size()
            
            return cache_path
            
        except Exception as e:
            log_error(f"添加文件到缓存失败: {text}, 错误: {str(e)}")
            return None
    
    def _generate_cache_key(self, text: str, lang: str) -> str:
        """生成缓存键
        
        Args:
            text: 文本内容
            lang: 语言代码
            
        Returns:
            缓存键字符串
        """
        # 使用文本和语言的组合生成唯一的缓存键
        content = f"{text}_{lang}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()