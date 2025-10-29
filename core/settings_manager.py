import json
import os
import threading
from typing import Dict, Any

from logger import log_info, log_error
from .database_manager import DatabaseManager


class SettingsManager:
    """优化版设置管理器，使用数据库存储设置，支持缓存"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化设置管理器"""
        # 确保只初始化一次
        with self._lock:
            if not hasattr(self, '_initialized'):
                self.db_manager = DatabaseManager()
                self._settings_cache = {}  # 内存缓存
                self._cache_lock = threading.RLock()
                # 监听器：key -> list of callbacks(func(key, new_value))
                self._listeners = {}
                self._listeners_lock = threading.RLock()
                
                # 加载设置到缓存
                self._load_settings_to_cache()
                
                self._initialized = True
    
    def _load_settings_to_cache(self):
        """从数据库加载所有设置到缓存"""
        try:
            results = self.db_manager.execute_read("SELECT key, value FROM settings")
            
            with self._cache_lock:
                for row in results:
                    try:
                        self._settings_cache[row['key']] = json.loads(row['value'])
                    except json.JSONDecodeError:
                        # 如果解析失败，保存原始字符串
                        self._settings_cache[row['key']] = row['value']
            
            # 确保有默认设置
            self._ensure_default_settings()
            
            log_info("设置加载到缓存完成")
            
        except Exception as e:
            log_error(f"加载设置到缓存失败: {str(e)}")
            # 加载默认设置
            self._ensure_default_settings()
    
    def _ensure_default_settings(self):
        """确保默认设置存在"""
        default_settings = {
            "auto_next_correct": False,
            "auto_next_wrong": False,
            "example_enabled": True,
            "voice_enabled": True,
            "voice_speed": 1.0,
            "dark_mode": False,
            # 常用自动跳转/延迟设置（毫秒）
            "auto_next_delay": 1000,
            "auto_next_example": False,
            "auto_next_familiar": False,
            "auto_next_difficult": False,
            # 语音与缓存控制
            "tts_provider": "gTTS",
            "tts_cache_enabled": True,
            "tts_cache_max_mb": 500,
            # 日志等级
            "log_level": "INFO"
            ,
            # 翻译判定模式: ai_first / local_first / local_only
            "translation_mode": "ai_first",
            # 自动切换模式（manual/auto），分别控制单词学习模块、翻译练习模块与复习模块
            "auto_mode_word_learning": "manual",
            "auto_mode_translation_practice": "manual",
            "auto_mode_review": "manual"
        }
        
        with self._cache_lock:
            for key, value in default_settings.items():
                if key not in self._settings_cache:
                    self._settings_cache[key] = value
                    # 保存到数据库
                    self.db_manager.set_setting(key, value)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置值（优先从缓存获取）"""
        with self._cache_lock:
            if key in self._settings_cache:
                return self._settings_cache[key]
        
        # 如果缓存中没有，从数据库获取
        value = self.db_manager.get_setting(key, default)
        
        # 更新缓存
        # 注意：db_manager.get_setting 会返回 default 值当 key 不存在
        if value is not None:
            with self._cache_lock:
                self._settings_cache[key] = value
        elif default is not None:
            # 如果 DB 里没有但调用方提供了 default，则缓存并返回 default
            with self._cache_lock:
                self._settings_cache[key] = default
            value = default
        
        return value
    
    def set_setting(self, key: str, value: Any) -> bool:
        """设置设置值"""
        try:
            # 保存到数据库（DatabaseManager.set_setting 不一定返回结果）
            self.db_manager.set_setting(key, value)

            # 更新缓存
            with self._cache_lock:
                self._settings_cache[key] = value
            log_info(f"设置 {key} 已更新为 {value}")

            # 通知监听器（非阻塞）
            try:
                with self._listeners_lock:
                    listeners = list(self._listeners.get(key, []))
                for cb in listeners:
                    try:
                        cb(key, value)
                    except Exception as _e:
                        log_error(f"settings listener error for {key}: {_e}")
            except Exception:
                # 不应阻塞设置流程
                pass

            return True
            
        except Exception as e:
            log_error(f"设置 {key} 失败: {str(e)}")
            return False
    
    def toggle_auto_next_correct(self) -> bool:
        """切换答对后自动下一个设置"""
        current = self.get_setting("auto_next_correct", False)
        new_value = not current
        result = self.set_setting("auto_next_correct", new_value)
        if result:
            log_info(f"设置答对后自动下一个: {'开启' if new_value else '关闭'}")
        return result
    
    def toggle_auto_next_wrong(self) -> bool:
        """切换答错后自动下一个设置"""
        current = self.get_setting("auto_next_wrong", False)
        new_value = not current
        result = self.set_setting("auto_next_wrong", new_value)
        if result:
            log_info(f"设置答错后自动下一个: {'开启' if new_value else '关闭'}")
        return result
    
    def toggle_example_enabled(self) -> bool:
        """切换例句功能设置"""
        current = self.get_setting("example_enabled", True)
        new_value = not current
        result = self.set_setting("example_enabled", new_value)
        if result:
            log_info(f"设置例句功能: {'开启' if new_value else '关闭'}")
        return result
    
    def set_voice_speed(self, speed: float) -> bool:
        """设置语音速度"""
        # 限制速度范围
        speed = max(0.5, min(3.0, speed))
        return self.set_setting("voice_speed", speed)
    
    def toggle_dark_mode(self) -> bool:
        """切换深色模式"""
        current = self.get_setting("dark_mode", False)
        new_value = not current
        result = self.set_setting("dark_mode", new_value)
        if result:
            log_info(f"设置深色模式: {'开启' if new_value else '关闭'}")
        return result

    def register_listener(self, key: str, callback):
        """注册设置变更监听器，callback(signature: func(key, new_value))"""
        with self._listeners_lock:
            if key not in self._listeners:
                self._listeners[key] = []
            if callback not in self._listeners[key]:
                self._listeners[key].append(callback)

    def unregister_listener(self, key: str, callback):
        """注销监听器"""
        with self._listeners_lock:
            if key in self._listeners and callback in self._listeners[key]:
                self._listeners[key].remove(callback)

    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """一次性批量更新多个设置并触发监听器"""
        ok = True
        for k, v in settings.items():
            if not self.set_setting(k, v):
                ok = False
        return ok
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        with self._cache_lock:
            # 返回深拷贝以防外部修改内部缓存
            import copy
            return copy.deepcopy(self._settings_cache)

    def get_translation_mode(self) -> str:
        """获取翻译判定模式"""
        return self.get_setting("translation_mode", "ai_first")

    def set_translation_mode(self, mode: str) -> bool:
        """设置翻译判定模式，mode 应该是 'ai_first'|'local_first'|'local_only'"""
        if mode not in ("ai_first", "local_first", "local_only"):
            log_error(f"无效的 translation_mode: {mode}")
            return False
        return self.set_setting("translation_mode", mode)

    def get_auto_mode(self, module: str) -> str:
        """获取指定模块的自动切换模式。

        module 应为 'word_learning' | 'translation_practice' | 'review'
        返回 'manual' 或 'auto'
        """
        key_map = {
            'word_learning': 'auto_mode_word_learning',
            'translation_practice': 'auto_mode_translation_practice',
            'review': 'auto_mode_review'
        }
        key = key_map.get(module)
        if not key:
            log_error(f"未知模块: {module}")
            return 'manual'
        return self.get_setting(key, 'manual')

    def set_auto_mode(self, module: str, mode: str) -> bool:
        """设置指定模块的自动切换模式。

        mode 应为 'manual' 或 'auto'
        """
        if mode not in ('manual', 'auto'):
            log_error(f"无效的 auto mode: {mode}")
            return False
        key_map = {
            'word_learning': 'auto_mode_word_learning',
            'translation_practice': 'auto_mode_translation_practice',
            'review': 'auto_mode_review'
        }
        key = key_map.get(module)
        if not key:
            log_error(f"未知模块: {module}")
            return False
        return self.set_setting(key, mode)
    
    def reset_to_default(self) -> bool:
        """重置所有设置到默认值"""
        try:
            default_settings = {
                "auto_next_correct": False,
                "auto_next_wrong": False,
                "example_enabled": True,
                "voice_enabled": True,
                "voice_speed": 1.0,
                "dark_mode": False,
                "auto_next_delay": 1000,
                "auto_next_example": False,
                "auto_next_familiar": False,
                "auto_next_difficult": False,
                "tts_provider": "gTTS",
                "tts_cache_enabled": True,
                "tts_cache_max_mb": 500,
                "log_level": "INFO"
            }
            
            # 更新数据库
            for key, value in default_settings.items():
                self.db_manager.set_setting(key, value)
            
            # 更新缓存
            with self._cache_lock:
                self._settings_cache = default_settings.copy()
            
            log_info("所有设置已重置为默认值")
            return True
            
        except Exception as e:
            log_error(f"重置设置失败: {str(e)}")
            return False