import json
import os
from typing import Dict, Any

from logger import log_info, log_error


class SettingsManager:
    """设置管理器，负责存储和管理用户设置"""
    
    def __init__(self):
        """初始化设置管理器"""
        self.data_dir = 'data'
        self.settings_file = os.path.join(self.data_dir, 'settings.json')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载设置
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """加载设置数据"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # 返回默认设置
            default_settings = {
                "auto_next_correct": False,  # 答对后自动下一个
                "auto_next_wrong": False,   # 答错后自动下一个
                "example_enabled": True,    # 启用例句功能
                "voice_enabled": True,      # 启用发音功能
                "voice_speed": 1.0,         # 发音速度
                "dark_mode": False          # 深色模式
            }
            # 保存默认设置
            self._save_settings(default_settings)
            return default_settings
        except Exception as e:
            log_error(f"加载设置失败: {str(e)}")
            # 返回最小默认设置
            return {"auto_next_correct": False, "auto_next_wrong": False, "example_enabled": True}
    
    def _save_settings(self, settings: Dict[str, Any]) -> bool:
        """保存设置数据"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            log_error(f"保存设置失败: {str(e)}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """设置设置值"""
        try:
            self.settings[key] = value
            return self._save_settings(self.settings)
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