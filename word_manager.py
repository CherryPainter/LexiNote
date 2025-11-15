"""单词管理器，负责单词的增删改查、权重计算和练习功能"""
import os
import random
import threading
import sqlite3
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from collections import deque

from logger import log_info, log_error, log_warning
from core.database_manager import DatabaseManager
from statistics import StatisticsManager


class WordManager:
    """优化版单词管理器类，提供单词管理相关功能，支持异步操作和缓存"""

    def __init__(self, statistics_manager: Optional[StatisticsManager] = None):
        """初始化单词管理器
        
        Args:
            statistics_manager: 统计管理器实例，如果为None则自动创建
        """
        self.data_dir = 'data'
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 使用数据库管理器
        self.db_manager = DatabaseManager()
        
        # 初始化统计管理器
        if statistics_manager is None:
            self.statistics_manager = StatisticsManager(self.db_manager)
        else:
            self.statistics_manager = statistics_manager
        
        # 内存缓存
        self._word_cache = {}  # 单词翻译缓存
        self._weight_cache = {}  # 权重缓存
        self._cache_lock = threading.RLock()  # 缓存锁
        
        # 初始化错误单词字典
        self.wrong_words = {}

        # 单词熟悉度映射（在内存中缓存，避免频繁查询数据库）
        self.word_familiarity = {}
        
        # 当前激活的词库ID
        self.active_word_set_id = None
        
        # 初始化AI管理器（延迟加载方式）
        self.ai_manager = None
        self.ai_available = False
        
        # 节流控制相关
        self._throttle_lock = threading.RLock()
        self._recent_ai_calls = deque(maxlen=20)  # 最近20次AI调用时间
        self._min_interval_ms = 500  # 最小调用间隔(毫秒)
        self._max_calls_per_minute = 10  # 每分钟最大调用次数
        
        # 初始化状态标记
        self.is_initialized = False
        
        # 将耗时操作放在后台线程执行
        self._init_thread = threading.Thread(target=self._init_background, daemon=True)
        self._init_thread.start()
    
    def _init_background(self):
        """在后台线程中执行耗时的初始化操作"""
        try:
            # 加载当前激活的词库
            self._load_active_word_set()
            
            # 初始化AI管理器
            self._init_ai_manager()
            
            # 预热缓存
            self._warmup_cache()
            
            # 加载单词熟悉度到内存缓存
            self._load_word_familiarity()
            
            self.is_initialized = True
            log_info("WordManager初始化完成")
        except Exception as e:
            log_error(f"WordManager后台初始化失败: {str(e)}")
    
    def _warmup_cache(self):
        """预热缓存，加载常用数据到内存"""
        try:
            # 加载所有单词到缓存
            all_words = self.db_manager.get_all_words()
            for word in all_words[:100]:  # 限制加载数量，避免内存占用过大
                translation = self.db_manager.get_word_translation(word)
                if translation:
                    with self._cache_lock:
                        self._word_cache[word] = translation
            log_info(f"缓存预热完成，加载了{len(self._word_cache)}个单词")
        except Exception as e:
            log_error(f"缓存预热失败: {str(e)}")

    def _init_ai_manager(self):
        """初始化AI管理器（延迟加载，使用单例模式）"""
        try:
            from core.ai_interface import AIManager
            self.ai_manager = AIManager()  # 由于AIManager实现了单例模式，这里会返回已有的实例或创建新实例
            # 直接检查AI可用性，不再调用不存在的is_ai_available方法
            self.ai_available = self._test_ai_connection()
        except ImportError:
            log_warning("AI接口模块未找到，部分功能可能受限")
            self.ai_available = False
        except Exception as e:
            log_error(f"初始化AI管理器失败: {str(e)}")
            self.ai_available = False
    
    def _test_ai_connection(self) -> bool:
        """测试AI连接是否可用
        
        Returns:
            bool: AI连接是否可用
        """
        try:
            # 简单测试AI连接，只检查Ollama服务是否可用，不实际生成例句
            if self.ai_manager:
                # 使用try-except捕获可能的错误，避免在初始化过程中抛出异常
                try:
                    import requests
                    # 只检查Ollama服务的健康状态，不发送实际的生成请求
                    health_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                    if health_response.status_code == 200:
                        log_info("AI功能测试成功，服务可用")
                        return True
                    else:
                        log_info(f"AI功能测试失败: Ollama服务状态码 {health_response.status_code}")
                        return False
                except requests.RequestException as e:
                    log_warning(f"测试AI连接失败: Ollama服务未启动或不可访问 - {str(e)}")
                    return False
                except Exception as e:
                    log_warning(f"测试AI连接时发生未知错误: {str(e)}")
                    return False
        except Exception as e:
            log_warning(f"检查AI可用性时发生错误: {str(e)}")
            return False
        return False
    
    def _check_throttle_limit(self) -> bool:
        """检查是否超过节流限制
        
        Returns:
            bool: True表示可以调用AI，False表示需要限流
        """
        with self._throttle_lock:
            current_time = time.time()
            
            # 移除过期的调用记录
            while self._recent_ai_calls and current_time - self._recent_ai_calls[0] > 60:  # 超过1分钟的记录
                self._recent_ai_calls.popleft()
            
            # 检查每分钟调用次数限制
            if len(self._recent_ai_calls) >= self._max_calls_per_minute:
                log_info(f"AI调用频率限制: 每分钟最多{self._max_calls_per_minute}次")
                return False
            
            # 检查两次调用之间的最小间隔
            if self._recent_ai_calls and current_time - self._recent_ai_calls[-1] < self._min_interval_ms / 1000:
                log_info(f"AI调用间隔限制: 至少{self._min_interval_ms}毫秒")
                return False
            
            # 记录本次调用
            self._recent_ai_calls.append(current_time)
            return True
    
    def set_throttle_limits(self, min_interval_ms: int = 500, max_calls_per_minute: int = 10):
        """设置AI调用节流限制
        
        Args:
            min_interval_ms: 两次调用之间的最小间隔(毫秒)
            max_calls_per_minute: 每分钟最大调用次数
        """
        with self._throttle_lock:
            self._min_interval_ms = max(100, min_interval_ms)  # 最小100毫秒
            self._max_calls_per_minute = max(1, max_calls_per_minute)  # 至少1次/分钟
            log_info(f"已设置AI节流参数: 最小间隔{self._min_interval_ms}ms, 最大频率{self._max_calls_per_minute}次/分钟")
    
    def _load_data(self, file_path: str) -> dict:
        """加载数据文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 加载的数据，如果文件不存在则返回空字典
        """
        import json
        try:
            # 确保数据目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                log_info(f"数据文件不存在，创建空文件: {file_path}")
                # 创建空文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                return {}
            
            # 加载文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(f"加载数据文件失败: {file_path}, 错误: {str(e)}")
            return {}
    
    def _save_data(self, file_path: str, data: dict):
        """保存数据到文件
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        import json
        try:
            # 确保数据目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 保存数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            log_info(f"数据保存成功: {file_path}")
        except Exception as e:
            log_error(f"保存数据文件失败: {file_path}, 错误: {str(e)}")
    
    # 词库管理相关方法
    def get_all_word_sets(self):
        """获取所有词库"""
        return self.db_manager.get_all_word_sets()
    
    def get_word_set_by_id(self, set_id):
        """根据ID获取词库信息"""
        return self.db_manager.get_word_set_by_id(set_id)
    
    def get_active_word_set(self):
        """获取当前激活的词库"""
        if not self.active_word_set_id:
            self._set_default_word_set()
        return self.db_manager.get_word_set_by_id(self.active_word_set_id)
    
    def set_active_word_set(self, set_id):
        """设置当前激活的词库"""
        try:
            # 验证词库是否存在
            word_set = self.db_manager.get_word_set_by_id(set_id)
            if not word_set:
                return False, "词库不存在"
            
            # 更新激活词库
            self.active_word_set_id = set_id
            
            # 保存到设置
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ('active_word_set', str(set_id))
            )
            conn.commit()
            conn.close()
            
            log_info(f"切换激活词库成功: {word_set['name']}")
            return True, f"切换到词库 '{word_set['name']}' 成功"
        except Exception as e:
            log_error(f"设置激活词库失败: {str(e)}")
            return False, str(e)
    
    def create_word_set(self, name, description=''):
        """创建新词库"""
        return self.db_manager.create_word_set(name, description)
    
    def delete_word_set(self, set_id):
        """删除词库"""
        # 检查是否是当前激活的词库
        if set_id == self.active_word_set_id:
            return False, "不能删除当前激活的词库"
        
        # 检查是否是默认词库
        word_set = self.db_manager.get_word_set_by_id(set_id)
        if word_set and word_set['name'] == '默认词库':
            return False, "不能删除默认词库"
        
        return self.db_manager.delete_word_set(set_id)
    
    def import_word_set_from_json(self, json_file_path):
        """从JSON文件导入词库"""
        try:
            import json
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证JSON结构
            if 'name' not in data:
                # 如果没有name字段，使用文件名
                import os
                data['name'] = os.path.splitext(os.path.basename(json_file_path))[0]
            
            if 'words' not in data or not isinstance(data['words'], list):
                return False, "词库文件格式错误：缺少words数组"
            
            if len(data['words']) == 0:
                return False, "词库文件为空"
            
            # 检查词库名是否已存在
            existing_set = self.db_manager.get_word_set_by_name(data['name'])
            if existing_set:
                # 返回特殊消息，表示需要确认覆盖
                return None, "overwrite"
            
            # 创建词库
            set_id, msg = self.db_manager.create_word_set(
                name=data['name'],
                description=data.get('description', ''),
                source='user_upload'
            )
            
            if not set_id:
                return False, msg
            
            # 添加单词
            success_count = 0
            for word_data in data['words']:
                # 验证单词数据格式
                if 'word' not in word_data or 'translation' not in word_data:
                    continue
                
                success, _ = self.db_manager.add_word_to_set(
                    set_id=set_id,
                    word=word_data['word'],
                    translation=word_data['translation'],
                    phonetic=word_data.get('phonetic', ''),
                    example=word_data.get('example', ''),
                    meaning_en=word_data.get('meaning_en', ''),
                    tag=word_data.get('tag', '')
                )
                if success:
                    success_count += 1
            
            log_info(f"词库导入成功: {data['name']}, {success_count}个单词")
            return True, f"导入成功！共添加{success_count}个单词"
            
        except json.JSONDecodeError:
            return False, "JSON文件格式错误"
        except Exception as e:
            log_error(f"导入词库失败: {str(e)}")
            return False, str(e)
    
    def export_word_set_to_json(self, set_id, output_file_path):
        """导出词库到JSON文件"""
        try:
            # 获取词库信息
            word_set = self.db_manager.get_word_set_by_id(set_id)
            if not word_set:
                return False, "词库不存在"
            
            # 获取词库中的单词
            words = self.db_manager.get_words_by_set_id(set_id)
            
            # 构建导出数据
            export_data = {
                'name': word_set['name'],
                'description': word_set.get('description', ''),
                'source': word_set.get('source', 'user_upload'),
                'words': []
            }
            
            for word in words:
                word_data = {
                    'word': word['word'],
                    'translation': word['translation'],
                    'phonetic': word.get('phonetic', ''),
                    'example': word.get('example', ''),
                    'meaning_en': word.get('meaning_en', ''),
                    'tag': word.get('tag', '')
                }
                export_data['words'].append(word_data)
            
            # 写入JSON文件
            import json
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            log_info(f"词库导出成功: {word_set['name']}")
            return True, "导出成功"
        except Exception as e:
            log_error(f"导出词库失败: {str(e)}")
            return False, str(e)
    
    # 单词管理相关方法
    def get_words_from_active_set(self, keyword=None, limit=None, offset=None):
        """从当前激活的词库获取单词"""
        if not self.active_word_set_id:
            self._set_default_word_set()
        return self.db_manager.get_words_by_set_id(
            self.active_word_set_id, keyword, limit, offset
        )
    
    def get_words_by_set_id(self, set_id, keyword=None, limit=None, offset=None):
        """从指定词库获取单词"""
        return self.db_manager.get_words_by_set_id(
            set_id, keyword, limit, offset
        )
    
    def add_word_to_active_set(self, word, translation, phonetic='', example='', meaning_en='', tag='', example_translation=''):
        """向当前激活的词库添加单词"""
        if not self.active_word_set_id:
            self._set_default_word_set()
        return self.db_manager.add_word_to_set(
            self.active_word_set_id, word, translation, phonetic, example, meaning_en, tag, example_translation
        )
    
    def update_word(self, word_id, **kwargs):
        """更新单词信息"""
        return self.db_manager.update_word(word_id, **kwargs)
    
    def delete_word(self, word_id):
        """删除单词"""
        return self.db_manager.delete_word(word_id)
    
    def get_words_missing_details(self, limit=10):
        """获取词库中缺失详细属性的单词
        
        Args:
            limit: 返回的最大单词数量
            
        Returns:
            缺失详细属性的单词列表
        """
        if not self.active_word_set_id:
            self._set_default_word_set()
            
        # 查询当前词库中缺少例句、例句翻译、音标、词性或英语释义的单词
        # 同时检查NULL值和空字符串
        sql = """
        SELECT * FROM words 
        WHERE set_id = ? 
        AND (example IS NULL OR example = '' OR example_translation IS NULL OR example_translation = '' OR phonetic IS NULL OR phonetic = '' OR tag IS NULL OR tag = '' OR meaning_en IS NULL OR meaning_en = '')
        ORDER BY word
        LIMIT ?
        """
        
        try:
            return self.db_manager.execute_read(sql, (self.active_word_set_id, limit))
        except Exception as e:
            log_error(f"获取缺失属性单词失败: {str(e)}")
            return []
    
    def ai_complete_word_details(self, callback=None):
        """使用AI补全单词的详细属性
        
        Args:
            callback: 进度回调函数，接收参数：(current: int, total: int, word: str)
            
        Returns:
            补全成功的单词数量
        """
        if not self.ai_available or not self.ai_manager:
            log_warning("AI不可用，无法补全单词属性")
            return 0
            
        # 获取需要补全的单词
        words_to_complete = self.get_words_missing_details(10)
        if not words_to_complete:
            log_info("没有需要补全属性的单词")
            return 0
            
        completed_count = 0
        total = len(words_to_complete)
        
        for i, word_data in enumerate(words_to_complete):
            word = word_data['word']
            word_id = word_data['id']
            
            try:
                # 调用AI获取单词详细属性
                ai_response = self.ai_manager.get_word_details_sync(word)
                
                # 解析AI响应
                import json
                import re
                
                # 提取JSON部分，处理可能包含的Markdown代码块或额外内容
                json_str = ai_response
                
                # 尝试提取JSON部分（处理可能的代码块）
                json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 尝试直接提取JSON对象
                    json_match = re.search(r'\{.*?\}', ai_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                
                # 清理JSON字符串，确保有效的JSON格式
                json_str = json_str.replace('\\_', '_')  # 处理转义的下划线
                
                details = json.loads(json_str)
                
                # 准备更新数据
                update_data = {}
                
                # 只更新缺失的属性
                if (word_data['phonetic'] is None or word_data['phonetic'] == '') and 'phonetic' in details and details['phonetic']:
                    update_data['phonetic'] = details['phonetic']
                
                if (word_data['tag'] is None or word_data['tag'] == '') and 'tag' in details and details['tag']:
                    update_data['tag'] = details['tag']
                
                if (word_data['meaning_en'] is None or word_data['meaning_en'] == '') and 'meaning_en' in details and details['meaning_en']:
                    update_data['meaning_en'] = details['meaning_en']
                
                if (word_data['example'] is None or word_data['example'] == '') and 'example' in details and details['example']:
                    update_data['example'] = details['example']
                
                # 只更新缺失的例句翻译
                if (word_data['example_translation'] is None or word_data['example_translation'] == '') and 'example_translation' in details and details['example_translation']:
                    update_data['example_translation'] = details['example_translation']
                
                # 处理中文释义，更新为新的多词性多义项结构
                if 'meaning_zh' in details and details['meaning_zh']:
                    # 创建新的翻译结构
                    translation_struct = []
                    
                    # 处理meaning_zh（可能是字符串或列表）
                    meanings = details['meaning_zh']
                    if isinstance(meanings, str):
                        meanings = [meanings]
                    elif not isinstance(meanings, list):
                        meanings = [str(meanings)]
                    
                    # 创建词性条目
                    # 使用pos字段作为权威词性来源，保留与旧模块的兼容性
                    pos = details.get('tag', '')
                    translation_struct.append({
                        'pos': pos,
                        'meaning_zh': meanings
                    })
                    
                    # 转换为JSON字符串存储
                    import json
                    update_data['translation'] = json.dumps(translation_struct, ensure_ascii=False)
                
                # 更新数据库
                if update_data:
                    success, msg = self.update_word(word_id, **update_data)
                    if success:
                        completed_count += 1
                        log_info(f"AI补全单词 '{word}' 成功: {update_data}")
                    else:
                        log_error(f"AI补全单词 '{word}' 失败: {msg}")
                
                # 调用进度回调
                if callback:
                    callback(i + 1, total, word)
                    
            except json.JSONDecodeError:
                log_error(f"解析AI响应失败 (单词: {word}): {ai_response}")
            except Exception as e:
                log_error(f"AI补全单词 '{word}' 失败: {str(e)}")
                
        log_info(f"AI补全单词完成，成功补全 {completed_count}/{total} 个单词")
        return completed_count
    
    def get_translation(self, word: str, format_output: bool = True) -> Optional[Union[str, List[Dict[str, Any]]]]:
        """获取单词翻译（带缓存）
        
        Args:
            word: 单词
            format_output: 是否格式化输出（当为True时，将多词性多义项格式转为字符串；为False时返回原始格式）
            
        Returns:
            翻译结果：格式化输出时返回字符串，否则返回原始格式
        """
        import json
        
        # 先查内存缓存
        with self._cache_lock:
            if word in self._word_cache:
                translation = self._word_cache[word]
                if not format_output:
                    return translation
                return self._format_translation(translation)
        
        # 查数据库
        translation = self.db_manager.get_word_translation(word)
        
        if not translation:
            return None
        
        # 更新缓存
        with self._cache_lock:
            self._word_cache[word] = translation
        
        if not format_output:
            return translation
            
        return self._format_translation(translation)
    
    def _format_translation(self, translation: Union[str, List[Dict[str, Any]]]) -> str:
        """格式化翻译结果为字符串
        
        Args:
            translation: 翻译结果，可以是字符串或多词性多义项结构
            
        Returns:
            格式化后的字符串
        """
        import json
        
        # 处理可能的JSON字符串
        try:
            if isinstance(translation, str) and (translation.startswith('[') or translation.startswith('{')):
                parsed = json.loads(translation)
                return self._format_translation(parsed)
        except json.JSONDecodeError:
            pass
        
        # 如果已经是字符串，直接返回
        if isinstance(translation, str):
            return translation
            
        # 如果是列表结构（新格式）
        if isinstance(translation, list):
            formatted_parts = []
            for item in translation:
                # 同时支持'pos'和'tag'字段，pos优先，确保与旧模块兼容
                tag = item.get('pos', item.get('tag', ''))
                # 同时支持'meanings'和'meaning_zh'键，确保兼容性
                meanings = item.get('meanings', item.get('meaning_zh', []))
                if meanings:
                    # 不显示词性，只显示含义
                    formatted_parts.append('；'.join(meanings))
            return '\n'.join(formatted_parts)
            
        # 其他情况，返回原始字符串
        return str(translation)
    
    def add_word(self, word: str, translation: str) -> bool:
        """添加单词
        
        Args:
            word: 单词
            translation: 翻译
            
        Returns:
            是否添加成功
        """
        try:
            # 添加到数据库
            self.db_manager.add_word(word, translation)
            
            # 更新缓存
            with self._cache_lock:
                self._word_cache[word] = translation
            
            log_info(f"添加单词成功: {word} -> {translation}")
            return True
        except Exception as e:
            log_error(f"添加单词失败: {str(e)}")
            return False
    
    def get_all_words(self) -> List[str]:
        """获取所有单词
        
        Returns:
            单词列表
        """
        return self.db_manager.get_all_words()
        
    def get_words_for_review(self, filter_type='all', limit=100) -> List[Dict]:
        """获取用于复习的单词列表
        
        Args:
            filter_type: 过滤类型，可选值: 'all'全部单词, 'familiar'熟词, 'difficult'难词
            limit: 返回的最大单词数
            
        Returns:
            单词字典列表，包含word、translation、proficiency等信息
        """
        try:
            if not self.active_word_set_id:
                self._set_default_word_set()
                
            # 根据过滤类型构建查询
            if filter_type == 'familiar':
                # 熟词：熟练度高于0.8的单词
                query = """
                    SELECT * FROM words 
                    WHERE set_id = ? AND proficiency > 0.8 
                    ORDER BY last_review DESC NULLS LAST, RANDOM() 
                    LIMIT ?
                """
            elif filter_type == 'difficult':
                # 难词：熟练度低于0.5的单词
                query = """
                    SELECT * FROM words 
                    WHERE set_id = ? AND proficiency < 0.5 
                    ORDER BY last_review ASC NULLS FIRST, proficiency ASC 
                    LIMIT ?
                """
            else:
                # 所有单词：优先选择最近复习过的和熟练度中等的单词
                query = """
                    SELECT * FROM words 
                    WHERE set_id = ? 
                    ORDER BY 
                        CASE 
                            WHEN last_review IS NULL THEN 0 
                            ELSE 1 
                        END, 
                        last_review ASC, 
                        ABS(proficiency - 0.5) DESC, 
                        RANDOM() 
                    LIMIT ?
                """
                
            results = self.db_manager.execute_read(
                query, 
                (self.active_word_set_id, limit)
            )
            
            return results
            
        except Exception as e:
            log_error(f"获取复习单词列表失败: {str(e)}")
            # 失败时返回空列表
            return []
            
    def update_word_familiarity(self, word: str, familiarity: float):
        """更新单词熟悉度（兼容旧接口，实际使用proficiency字段）
        
        Args:
            word: 单词
            familiarity: 熟悉度值（0.0-1.0）
        """
        try:
            # 查找单词ID
            result = self.db_manager.execute_read(
                "SELECT id FROM words WHERE word = ? AND set_id = ?",
                (word, self.active_word_set_id)
            )
            
            if result:
                word_id = result[0]['id']
                # 更新熟悉度（使用proficiency字段）
                update_result = self.db_manager.update_word(
                    word_id, 
                    proficiency=float(familiarity),
                    last_review=datetime.now().isoformat()
                )
                
                # 更新内存缓存
                with self._cache_lock:
                    if word in self.word_familiarity:
                        self.word_familiarity[word] = float(familiarity)
                
                if update_result[0]:
                    log_info(f"更新单词熟悉度成功: {word} -> {familiarity}")
                else:
                    log_error(f"更新单词熟悉度失败: {update_result[1]}")
            else:
                log_warning(f"单词不存在于当前词库: {word}")
                
        except Exception as e:
            log_error(f"更新单词熟悉度异常: {str(e)}")
            
    def get_word_familiarity(self) -> Dict[str, float]:
        """获取单词熟悉度字典（兼容旧接口，实际返回proficiency值）
        
        Returns:
            单词熟悉度字典
        """
        try:
            # 如果缓存为空，从数据库重新加载
            if not self.word_familiarity:
                self._load_word_familiarity()
            return self.word_familiarity
        except Exception as e:
            log_error(f"获取单词熟悉度失败: {str(e)}")
            return {}
    
    # get_word_by_weight 已在文件后部提供更完整实现，早期占位实现已移除
    
    def update_word_proficiency(self, word: str, is_correct: bool):
        """更新单词熟练度
        
        Args:
            word: 单词
            is_correct: 是否正确
        """
        try:
            # 获取当前熟练度
            results = self.db_manager.execute_read(
                "SELECT proficiency FROM words WHERE word = ?",
                (word,)
            )
            
            current_proficiency = results[0]['proficiency'] if results else 0.0
            
            # 更新熟练度
            # 正确增加0.1，错误减少0.15
            proficiency_change = 0.1 if is_correct else -0.15
            new_proficiency = max(0.0, min(1.0, current_proficiency + proficiency_change))
            
            # 更新数据库
            self.db_manager.update_proficiency(word, new_proficiency)
            self.db_manager.add_progress_record(word, is_correct, proficiency_change)
            
            # 清除相关缓存
            with self._cache_lock:
                if word in self._weight_cache:
                    del self._weight_cache[word]
            
            log_info(f"更新单词熟练度: {word} -> {new_proficiency}")
            
        except Exception as e:
            log_error(f"更新单词熟练度失败: {str(e)}")
    
    def get_familiar_words(self) -> List[str]:
        """获取熟悉的单词（熟练度>0.8）
        
        Returns:
            熟悉单词列表
        """
        try:
            results = self.db_manager.execute_read(
                "SELECT word FROM words WHERE proficiency > 0.8"
            )
            return [row['word'] for row in results]
        except Exception as e:
            log_error(f"获取熟悉单词失败: {str(e)}")
            return []
    
    # 早期的 get_difficult_words 实现已移除，使用文件后部更通用的 get_difficult_words
    
    def get_learning_stats(self) -> Dict:
        """获取学习统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 使用统计管理器获取综合统计信息
            summary_stats = self.statistics_manager.get_summary_stats()
            
            # 获取今日统计
            today_stats = self.statistics_manager.get_daily_stats()
            
            return {
                "total_words": summary_stats['total_words'],
                "today_practices": today_stats['practices'],
                "today_correct": today_stats['correct'],
                "today_accuracy": today_stats['accuracy'],
                "avg_proficiency": summary_stats['overall_accuracy']
            }
            
        except Exception as e:
            log_error(f"获取学习统计失败: {str(e)}")
            return {
                "total_words": 0,
                "today_practices": 0,
                "today_correct": 0,
                "today_accuracy": 0.0,
                "avg_proficiency": 0.0
            }
    
    def clear_cache(self):
        """清除内存缓存"""
        with self._cache_lock:
            self._word_cache.clear()
            self._weight_cache.clear()
        self.get_translation.cache_clear()  # 清除lru_cache
        log_info("内存缓存已清除")

    def _load_word_familiarity(self):
        """从数据库加载所有单词的熟练度到内存缓存"""
        try:
            rows = self.db_manager.execute_read("SELECT word, proficiency FROM words")
            with self._cache_lock:
                self.word_familiarity = {row['word']: row.get('proficiency', 0.0) for row in rows}
            log_info(f"加载单词熟悉度: {len(self.word_familiarity)} 条")
        except Exception as e:
            log_error(f"加载单词熟悉度失败: {str(e)}")
    
    def _load_active_word_set(self):
        """加载当前激活的词库"""
        try:
            # 从设置中读取当前激活的词库
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'active_word_set'")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                try:
                    self.active_word_set_id = int(result[0])
                except ValueError:
                    # 如果设置值无效，设置为默认词库
                    self._set_default_word_set()
            else:
                # 如果没有设置，设置为默认词库
                self._set_default_word_set()
        except Exception as e:
            log_error(f"加载激活词库失败: {str(e)}")
            # 失败时设置默认词库
            self._set_default_word_set()
    
    def _set_default_word_set(self):
        """设置默认词库为激活状态"""
        try:
            # 获取默认词库
            default_set = self.db_manager.get_word_set_by_name('默认词库')
            if default_set:
                self.active_word_set_id = default_set['id']
                # 保存到设置
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ('active_word_set', str(self.active_word_set_id))
                )
                conn.commit()
                conn.close()
        except Exception as e:
            log_error(f"设置默认词库失败: {str(e)}")

    def check_spelling(self, correct_word: str, user_input: str) -> bool:
        """检查拼写是否正确
        
        Args:
            correct_word: 正确的单词
            user_input: 用户输入的单词
            
        Returns:
            bool: 拼写是否正确（不区分大小写）
        """
        try:
            # 不区分大小写的比较
            return correct_word.lower() == user_input.lower().strip()
        except Exception as e:
            log_error(f"检查拼写时出错: {str(e)}")
            return False
            
    def remove_word(self, word: str) -> bool:
        """删除单词

        Args:
            word: 单词
            
        Returns:
            是否删除成功
        """
        try:
            # 从数据库删除
            result = self.db_manager.remove_word(word)
            
            # 从缓存删除
            with self._cache_lock:
                if word in self._word_cache:
                    del self._word_cache[word]
                if word in self._weight_cache:
                    del self._weight_cache[word]
            
            if result:
                log_info(f"删除单词成功: {word}")
            return result
        except Exception as e:
            log_error(f"删除单词失败: {str(e)}")
            return False

    def update_word_translation(self, word: str, translation: str) -> bool:
        """更新单词翻译

        Args:
            word: 单词
            translation: 新的翻译
            
        Returns:
            是否更新成功
        """
        try:
            # 更新数据库
            result = self.db_manager.update_word_translation(word, translation)
            
            # 更新缓存
            if result:
                with self._cache_lock:
                    self._word_cache[word] = translation
                log_info(f"更新单词成功: {word} -> {translation}")
            return result
        except Exception as e:
            log_error(f"更新单词失败: {str(e)}")
            return False
    
    def batch_import_words(self, json_file_path: str, set_id: int = None) -> Dict:
        """批量导入单词
        
        Args:
            json_file_path: JSON文件路径，文件格式应为 {"word1": "translation1", "word2": "translation2", ...}
            set_id: 词库ID，默认为默认词库
            
        Returns:
            Dict: 导入结果统计信息，包含success, total, imported, skipped, errors等字段
        """
        try:
            # 动态导入单词导入器以避免循环依赖
            from modules.word_importer import import_words_from_json
            
            # 调用导入功能
            result = import_words_from_json(json_file_path, set_id)
            
            # 如果导入成功，更新缓存
            if result.get("success", False) and result.get("imported", 0) > 0:
                # 重新预热缓存以包含新导入的单词
                self._warmup_cache()
            
            return result
        except ImportError:
            log_error("无法导入单词导入模块")
            return {
                "success": False,
                "total": 0,
                "imported": 0,
                "skipped": 0,
                "errors": ["单词导入模块未找到"]
            }
        except Exception as e:
            log_error(f"批量导入单词时发生错误: {str(e)}")
            return {
                "success": False,
                "total": 0,
                "imported": 0,
                "skipped": 0,
                "errors": [str(e)]
            }

    def get_word_translation(self, word: str) -> Optional[str]:
        """获取单词翻译

        Args:
            word: 单词

        Returns:
            str: 单词的翻译，如果不存在返回None
        """
        return self.get_translation(word)

    def get_word_count(self) -> int:
        """获取单词数量

        Returns:
            int: 单词数量
        """
        try:
            # 使用统计管理器获取总单词数
            return self.statistics_manager.get_total_word_count()
        except Exception as e:
            log_error(f"获取单词数量失败: {str(e)}")
            return 0

    def get_random_word(
        self, exclude_words: List[str] = None
    ) -> Optional[str]:
        """获取随机单词

        Args:
            exclude_words: 排除的单词列表

        Returns:
            str: 随机单词，如果没有可用单词返回None
        """
        try:
            # 检查是否有激活的词库，如果没有则设置默认词库
            if not self.active_word_set_id:
                self._set_default_word_set()
                
            # 获取当前激活词库中的所有单词
            words = self.db_manager.execute_read(
                "SELECT word FROM words WHERE set_id = ? ORDER BY word",
                (self.active_word_set_id,)
            )
            
            all_words = [word['word'] for word in words]
            
            if exclude_words:
                available_words = [word for word in all_words if word not in exclude_words]
            else:
                available_words = all_words
            
            if available_words:
                return random.choice(available_words)
            return None
        except Exception as e:
            log_error(f"获取随机单词失败: {str(e)}")
            return None

    def get_weighted_random_word(
        self, exclude_words: List[str] = None
    ) -> Optional[str]:
        """根据权重获取随机单词

        Args:
            exclude_words: 排除的单词列表

        Returns:
            str: 随机单词，如果没有可用单词返回None
        """
        try:
            # 检查是否有激活的词库，如果没有则设置默认词库
            if not self.active_word_set_id:
                self._set_default_word_set()
                
            # 使用数据库中的熟练度作为权重，仅从当前激活词库获取
            words = self.db_manager.execute_read(
                "SELECT word, proficiency FROM words WHERE set_id = ? ORDER BY proficiency ASC",
                (self.active_word_set_id,)
            )
            
            # 过滤排除的单词
            if exclude_words:
                words = [word for word in words if word['word'] not in exclude_words]
            
            if not words:
                return None
            
            # 使用权重选择（熟练度越低，权重越高）
            total_weight = sum((1.0 - word['proficiency']) for word in words)
            if total_weight == 0:
                return random.choice(words)['word']
            
            # 加权随机选择
            r = random.uniform(0, total_weight)
            cumulative = 0
            
            for word in words:
                cumulative += (1.0 - word['proficiency'])
                if r <= cumulative:
                    return word['word']
            
            return words[0]['word']
        except Exception as e:
            log_error(f"获取加权随机单词失败: {str(e)}")
            return self.get_random_word(exclude_words)

    def update_word_weight(self, word: str, is_correct: bool, time_spent: float = 0):
        """更新单词权重，考虑正确与否和响应时间

        Args:
            word: 单词
            is_correct: 是否拼写正确
            time_spent: 拼写所用时间（秒）
        """
        try:
            # 调用数据库更新方法，考虑时间因素调整熟练度变化量
            proficiency_change = 0.1
            
            if is_correct:
                # 正确拼写时增加熟练度
                if time_spent > 10:
                    proficiency_change = 0.05  # 响应很慢，增加较少
                elif time_spent > 5:
                    proficiency_change = 0.08  # 响应较慢，增加中等
                elif time_spent < 2:
                    proficiency_change = 0.15  # 响应很快，增加较多
            else:
                # 错误拼写时减少熟练度
                proficiency_change = -0.15
                if time_spent < 3:
                    proficiency_change = -0.2  # 快速错误，减少更多
                elif time_spent > 8:
                    proficiency_change = -0.1  # 思考后错误，减少较少
            
            # 获取当前熟练度
            results = self.db_manager.execute_read(
                "SELECT proficiency FROM words WHERE word = ?",
                (word,)
            )
            
            current_proficiency = results[0]['proficiency'] if results else 0.0
            new_proficiency = max(0.0, min(1.0, current_proficiency + proficiency_change))
            
            # 更新数据库
            self.db_manager.update_proficiency(word, new_proficiency)
            
            log_info(f"更新单词权重: {word}, 熟练度从 {current_proficiency} 调整为 {new_proficiency}")
            
        except Exception as e:
            log_error(f"更新单词权重失败: {str(e)}")

    def get_progress(self) -> dict:
        """获取学习进度信息

        Returns:
            包含学习进度信息的字典，包括:
            - total_learned: 总学习单词数
            - correct_rate: 正确率
            - last_session: 最后学习时间
        """
        try:
            # 使用统计管理器获取综合统计信息
            summary_stats = self.statistics_manager.get_summary_stats()
            
            return {
                'total_learned': summary_stats['learned_words'],
                'correct_rate': summary_stats['overall_accuracy'],
                'last_session': summary_stats['last_session']
            }
        except Exception as e:
            log_info(f"获取学习进度失败: {str(e)}")
            # 返回默认值
            return {
                'total_learned': 0,
                'correct_rate': 0.0,
                'last_session': "未开始"
            }
    
    def start_exercise(self, exercise_type: str) -> None:
        """开始练习，记录练习开始信息

        Args:
            exercise_type: 练习类型，如"听写"
        """
        try:
            from datetime import datetime
            
            # 记录练习开始日志
            log_info(f"开始{exercise_type}练习")
            
            # 在数据库中记录练习会话
            timestamp = datetime.now().isoformat()
            try:
                self.db_manager.execute_write(
                    "INSERT INTO exercise_sessions (exercise_type, start_time) VALUES (?, ?)",
                    (exercise_type, timestamp)
                )
            except Exception as db_error:
                log_info(f"记录练习会话失败: {str(db_error)}")
        except Exception as e:
            log_info(f"开始练习失败: {str(e)}")
    
    def get_word_by_weight(self) -> Optional[str]:
        """根据单词权重获取单词（错误次数多的单词优先）

        Returns:
            选中的单词，如果没有单词则返回None
        """
        try:
            # 检查是否有激活的词库，如果没有则设置默认词库
            if not self.active_word_set_id:
                self._set_default_word_set()
                
            # 查询当前激活词库中熟练度较低的单词
            words = self.db_manager.execute_read(
                "SELECT word, proficiency FROM words WHERE set_id = ? ORDER BY proficiency ASC LIMIT 20",
                (self.active_word_set_id,)
            )
            
            if not words:
                return None
            
            # 使用权重选择
            # 熟练度越低，权重越高
            total_weight = sum((1.0 - word['proficiency']) for word in words)
            if total_weight == 0:
                # 如果所有单词熟练度都很高，随机选择
                return random.choice(words)['word']
            
            # 加权随机选择
            r = random.uniform(0, total_weight)
            cumulative = 0
            
            for word in words:
                cumulative += (1.0 - word['proficiency'])
                if r <= cumulative:
                    return word['word']
            
            return words[0]['word']
            
        except Exception as e:
            log_error(f"根据权重获取单词失败: {str(e)}")
            return self.get_random_word()
    
    def add_wrong_word(self, word: str):
        """添加错误单词

        Args:
            word: 单词
        """
        try:
            word_lower = word.lower()
            # 错误拼写，更新权重，没有时间统计使用默认值
            self.update_word_weight(word_lower, False, 0)
            # 降低熟悉度（通过更新熟练度实现）
            self.update_word_proficiency(word_lower, False)
            log_info(f"添加错误单词: {word}")
        except Exception as e:
            log_error(f"添加错误单词失败: {str(e)}")

    def get_wrong_words(self) -> Dict[str, int]:
        """获取所有错误单词及其错误次数

        Returns:
            Dict[str, int]: 错误单词字典，键为单词，值为错误次数
        """
        return self.wrong_words

    def get_difficult_words(self, threshold: int = 3, limit: int = None) -> List[str]:
        """获取困难单词（错误次数超过阈值的单词）

        Args:
            threshold: 错误次数阈值
            limit: 返回单词数量限制，如果为None则返回所有符合条件的单词

        Returns:
            List[str]: 困难单词列表
        """
        difficult_words = [
            word for word, count in self.wrong_words.items()
            if count >= threshold
        ]
        # 如果指定了limit，限制返回数量
        if limit is not None:
            difficult_words = difficult_words[:limit]
        return difficult_words

    def update_word_familiarity(self, word: str, delta: float):
        """更新单词熟悉度（已废弃，使用update_word_proficiency替代）

        Args:
            word: 单词
            delta: 熟悉度变化量
        """
        try:
            # 调用新的update_word_proficiency方法，使用参数转换
            is_correct = delta > 0  # 正增量表示正确，负增量表示错误
            self.update_word_proficiency(word, is_correct)
        except Exception as e:
            log_error(f"更新单词熟悉度失败: {str(e)}")

    def get_today_learned_words(self) -> List[str]:
        """获取今日学习的单词列表
        
        Returns:
            List[str]: 今日学习的单词列表
        """
        try:
            # 从数据库查询今日学习记录
            today = datetime.now().strftime("%Y-%m-%d")
            results = self.db_manager.execute_read(
                """
                SELECT DISTINCT word 
                FROM progress 
                WHERE practice_date >= ?
                """,
                (today + " 00:00:00",)
            )
            
            today_words = [row['word'] for row in results]
            log_info(f"get_today_learned_words 返回 {len(today_words)} 个单词")
            return today_words
        except Exception as e:
            log_error(f"获取今日学习单词失败: {str(e)}")
            return []
    
    def get_word_familiarity(self, word: str = None) -> Union[float, Dict[str, float]]:
        """获取单词熟悉度
        
        Args:
            word: 单词，不提供则返回所有单词的熟悉度
            
        Returns:
            单个单词返回熟悉度值(0-1)，所有单词返回字典{word: familiarity}
        """
        if word is not None:
            return self.word_familiarity.get(word.lower(), 0.0)
        else:
            # 返回所有单词的熟悉度
            # 使用数据库获取所有单词并返回熟悉度映射
            try:
                all_words = self.db_manager.get_all_words()
                return {word: self.word_familiarity.get(word.lower(), 0.0) for word in all_words}
            except Exception as e:
                log_error(f"获取单词熟悉度映射失败: {str(e)}")
                return {}

    def _get_default_example(self, word: str) -> str:
        """获取单词的默认例句（用于AI调用失败时的备用）

        Args:
            word: 要获取例句的单词

        Returns:
            str: 包含例句和翻译的文本
        """
        # 硬编码的基本例句
        basic_examples = {
            "apple": (
                "I eat an apple every day. "
                "(我每天吃一个苹果。)"
            ),
            "book": (
                "This is a good book. "
                "(这是一本好书。)"
            ),
            "run": (
                "I like to run in the morning. "
                "(我喜欢在早上跑步。)"
            ),
            "beautiful": (
                "She is very beautiful. "
                "(她非常美丽。)"
            ),
            "computer": (
                "I use the computer to work. "
                "(我用电脑工作。)"
            ),
            "learn": (
                "We need to learn English every day. "
                "(我们需要每天学习英语。)"
            ),
            "friend": (
                "He is my best friend. "
                "(我最好的朋友。)"
            ),
            "happy": (
                "I feel very happy today. "
                "(我今天感到很开心。)"
            ),
            "work": (
                "I go to work at 9 o'clock. "
                "(我9点钟去上班。)"
            ),
            "time": (
                "Time flies. "
                "(时光飞逝。)"
            )
        }

        # 如果有基本例句，返回它
        if word.lower() in basic_examples:
            return basic_examples[word.lower()]

        # 获取单词翻译
        translation = self.get_word_translation(word)
        if translation:
            # 返回带翻译的默认例句
            return f"This is an example sentence with the word '{word}'. " \
                   f"(这是一个包含 '{word}' 的例句，意思是：{translation}。)"
        else:
            # 返回带占位翻译的默认例句
            return f"This is an example sentence with the word '{word}'. " \
                   f"(这是一个包含 '{word}' 的例句，暂无翻译。)"

    def get_unfamiliar_words(self, threshold: float = 0.3) -> List[str]:
        """获取不熟悉的单词

        Args:
            threshold: 熟悉度阈值

        Returns:
            List[str]: 不熟悉的单词列表
        """
        return [
            word for word, familiarity in self.word_familiarity.items()
            if familiarity < threshold
        ]

    def get_and_save_word_attributes(self, word: str, attributes: List[str] = None, async_mode=False, callback=None) -> Dict[str, str]:
        """获取并保存单词的属性（节流模式）
        
        只在数据库中对应字段为空时从AI获取数据并存储，已有内容的字段不调用AI
        
        Args:
            word: 单词
            attributes: 需要获取的属性列表，可选值：['phonetic', 'example', 'meaning_en', 'tag']
            async_mode: 是否异步获取
            callback: 异步模式下的回调函数，接收参数：(attributes_dict: Dict[str, str])
            
        Returns:
            Dict[str, str]: 同步模式返回属性字典，异步模式返回None
        """
        if attributes is None:
            attributes = ['phonetic', 'example', 'meaning_en', 'tag']
        
        try:
            # 验证属性值
            valid_attributes = ['phonetic', 'example', 'example_translation', 'meaning_en', 'tag']
            attributes = [attr for attr in attributes if attr in valid_attributes]
            
            if not attributes:
                log_error("无效的属性列表")
                return {}
            
            # 从数据库获取单词信息
            db_attributes = {}
            missing_attributes = []
            
            words = self.get_words_from_active_set(keyword=word)
            word_obj = None
            
            for w in words:
                if w['word'].lower() == word.lower():
                    word_obj = w
                    break
            
            if not word_obj:
                log_error(f"单词不存在于当前词库: {word}")
                return {}
            
            # 检查哪些属性缺失
            for attr in attributes:
                if attr in word_obj and word_obj[attr]:
                    db_attributes[attr] = word_obj[attr]
                else:
                    missing_attributes.append(attr)
            
            # 如果所有属性都已存在，直接返回
            if not missing_attributes:
                log_info(f"所有请求的属性都已存在于数据库: {word}")
                if async_mode and callback:
                    callback(db_attributes)
                return db_attributes
            
            # 如果有缺失的属性，从AI获取
            # 无论是同步还是异步模式，都从AI获取缺失的属性
            def fetch_missing_attributes():
                try:
                    # 检查AI功能是否可用（每次都重新验证）
                    if not self.is_ai_available() or not self.ai_manager:
                        log_warning("AI功能不可用，无法获取缺失的属性")
                        if callback:
                            callback(db_attributes)
                        return db_attributes

                    # 检查节流限制
                    if not self._check_throttle_limit():
                        log_info(f"AI调用受节流限制，稍后重试: {word}")
                        if callback:
                            callback(db_attributes)
                        return db_attributes

                    # 请求AI获取缺失的属性
                    # 构建提示词请求所有缺失的属性
                    prompt = f"请为单词 '{word}' 提供以下信息：{', '.join(missing_attributes)}"
                    if 'example' in missing_attributes:
                        prompt += "，例句需要包含英文句子和中文翻译"

                    response = self.ai_manager._ask_sync(prompt)

                    # 解析AI返回的数据
                    # 这里简化处理，实际项目中可能需要更复杂的解析逻辑
                    # 根据不同属性使用不同的AI方法或更精确的解析
                    ai_attributes = {}

                    if 'phonetic' in missing_attributes:
                        # 获取音标
                        try:
                            phonetic_response = self.ai_manager._ask_sync(f"请提供单词 '{word}' 的标准音标，仅返回音标部分")
                            if phonetic_response and "AI功能暂不可用" not in phonetic_response:
                                ai_attributes['phonetic'] = phonetic_response
                        except Exception as e:
                            log_error(f"获取音标时发生异常: {str(e)}")

                    if 'example' in missing_attributes:
                        # 获取例句
                        try:
                            example = self.ai_manager.example_sync(word)
                            # 注意：example_sync返回的不是JSON格式，而是"英文例句|中文翻译"格式
                            if example and "AI功能暂不可用" not in example and "生成例句失败" not in example:
                                # 正确拆分例句和翻译
                                if "|" in example:
                                    example_en, example_zh = example.split("|", 1)
                                    ai_attributes['example'] = example_en.strip()
                                    ai_attributes['example_translation'] = example_zh.strip()
                                else:
                                    # 如果格式不符合预期，仍然保存到example字段
                                    ai_attributes['example'] = example.strip()
                            else:
                                log_warning(f"获取例句失败或AI不可用: {example}")
                        except Exception as e:
                            log_error(f"获取例句时发生异常: {str(e)}")

                    if 'meaning_en' in missing_attributes:
                        # 获取英文释义
                        try:
                            meaning_en_response = self.ai_manager._ask_sync(f"请提供单词 '{word}' 的英文释义，仅返回英文")
                            if meaning_en_response and "AI功能暂不可用" not in meaning_en_response:
                                ai_attributes['meaning_en'] = meaning_en_response
                        except Exception as e:
                            log_error(f"获取英文释义时发生异常: {str(e)}")

                    if 'tag' in missing_attributes:
                        # 获取标签
                        try:
                            tag_response = self.ai_manager._ask_sync(f"请为单词 '{word}' 提供合适的标签，用逗号分隔，如：名词,动词")
                            if tag_response and "AI功能暂不可用" not in tag_response:
                                ai_attributes['tag'] = tag_response
                        except Exception as e:
                            log_error(f"获取标签时发生异常: {str(e)}")

                    # 合并数据库已有属性和AI获取的属性
                    result_attributes = {**db_attributes, **ai_attributes}

                    # 先返回数据给用户展示
                    if callback:
                        callback(result_attributes)

                    # 然后在后台异步保存到数据库
                    def save_attributes_to_database():
                        try:
                            update_data = {}
                            for attr, value in ai_attributes.items():
                                if value and "AI功能暂不可用" not in value:
                                    update_data[attr] = value

                            if update_data:
                                success, msg = self.update_word(word_obj['id'], **update_data)
                                if success:
                                    log_info(f"已保存单词属性到数据库: {word}, 属性: {', '.join(update_data.keys())}")
                                else:
                                    log_error(f"保存单词属性失败: {msg}")
                        except Exception as e:
                            log_error(f"异步保存单词属性时发生异常: {str(e)}")

                    # 启动保存数据的后台线程
                    save_thread = threading.Thread(target=save_attributes_to_database, daemon=True)
                    save_thread.start()
                    
                    return result_attributes

                except Exception as e:
                    log_error(f"获取缺失属性时发生异常: {str(e)}")
                    if callback:
                        callback(db_attributes)  # 返回已有数据
                    return db_attributes

            # 异步模式：在单独的线程中执行
            if async_mode:
                thread = threading.Thread(target=fetch_missing_attributes, daemon=True)
                thread.start()
                return None
            else:
                # 同步模式：直接执行并返回结果
                return fetch_missing_attributes()
                
        except Exception as e:
            log_error(f"处理单词属性时发生异常: {str(e)}")
            if async_mode and callback:
                callback({})
            return {}
    
    def _format_example(self, example_text):
        """格式化例句文本
        
        Args:
            example_text: 原始例句文本（可能是"英文例句|中文翻译"格式）
            
        Returns:
            格式化后的例句文本
        """
        if not example_text:
            return ""
            
        # 检查是否包含分隔符
        if '|' in example_text:
            parts = example_text.split('|', 1)
            if len(parts) == 2:
                return f"🌍 {parts[0].strip()}\n📝 {parts[1].strip()}"
        
        # 如果不是预期格式，直接返回
        return example_text
            
    def get_word_example(self, word: str, async_mode=False, callback=None) -> str:
        """
        获取单词的例句（优先从数据库获取，没有则通过AI补全）

        Args:
            word: 要获取例句的单词
            async_mode: 是否以异步方式获取（不阻塞UI线程）
            callback: 异步模式下的回调函数，接收参数：(example: str)

        Returns:
            str: 同步模式下返回包含例句和翻译的文本，如果获取失败返回默认例句
                 异步模式下返回None，结果通过callback返回
        """
        log_info(f"获取单词例句: {word}, 异步模式: {async_mode}")
        
        # 首先从数据库获取单词信息
        words = self.get_words_from_active_set(keyword=word)
        word_obj = None
        
        for w in words:
            if w['word'].lower() == word.lower():
                word_obj = w
                break
        
        if not word_obj:
            log_error(f"单词不存在于当前词库: {word}")
            if async_mode:
                if callback:
                    callback(self._get_default_example(word))
                return None
            else:
                return self._get_default_example(word)
        
        # 检查数据库中是否已有例句
        example = word_obj.get('example', '')
        example_translation = word_obj.get('example_translation', '')
        
        # 如果已有例句，直接使用（无论是否有翻译）
        if example:
            formatted_example = ""
            if example and example_translation:
                formatted_example = f"🌍 {example}\n📝 {example_translation}"
            elif example:
                # 如果有例句但没有翻译，或者需要兼容旧格式
                old_format_example = self._format_example(example)
                if '|' in example:
                    # 如果是旧格式（包含|分隔符），使用格式化结果
                    formatted_example = old_format_example
                else:
                    # 否则只显示例句（没有翻译）
                    formatted_example = f"🌍 {example}"
            
            if async_mode:
                if callback:
                    callback(formatted_example)
                return None
            else:
                return formatted_example
        
        # 如果没有例句，才通过AI获取
        # 使用通用的属性获取方法（自动处理数据库检查和AI补全）
        def example_callback(attributes):
            if callback:
                try:
                    example = attributes.get('example', '')
                    example_translation = attributes.get('example_translation', '')
                    if example and example_translation:
                        formatted_example = f"🌍 {example}\n📝 {example_translation}"
                    elif example:
                        # 如果有例句但没有翻译，或者需要兼容旧格式
                        old_format_example = self._format_example(example)
                        if '|' in example:
                            # 如果是旧格式（包含|分隔符），使用格式化结果
                            formatted_example = old_format_example
                        else:
                            # 否则只显示例句（没有翻译）
                            formatted_example = f"🌍 {example}"
                    else:
                        formatted_example = self._get_default_example(word)
                    callback(formatted_example)
                except Exception as e:
                    log_error(f"执行例句回调时发生错误: {str(e)}")
        
        attributes = self.get_and_save_word_attributes(word, ['example', 'example_translation'], async_mode, 
                                                     callback=example_callback if async_mode else None)
        
        if async_mode:
            return None
        else:
            example = attributes.get('example', '')
            example_translation = attributes.get('example_translation', '')
            if example and example_translation:
                return f"🌍 {example}\n📝 {example_translation}"
            elif example:
                # 如果有例句但没有翻译，或者需要兼容旧格式
                old_format_example = self._format_example(example)
                if '|' in example:
                    # 如果是旧格式（包含|分隔符），使用格式化结果
                    return old_format_example
                else:
                    # 否则只显示例句（没有翻译）
                    return f"🌍 {example}"
            else:
                return self._get_default_example(word)
    
    def _save_example_to_database(self, word: str, example: str):
        """将例句保存到数据库
        
        Args:
            word: 单词
            example: 例句
        """
        try:
            # 获取当前激活词库中的单词
            words = self.get_words_from_active_set(keyword=word)
            for w in words:
                if w['word'].lower() == word.lower():
                    # 更新单词的例句
                    success, msg = self.update_word(w['id'], example=example)
                    if success:
                        log_info(f"例句已保存到数据库: {word}")
                    else:
                        log_error(f"保存例句到数据库失败: {msg}")
                    return
        except Exception as e:
            log_error(f"保存例句到数据库异常: {str(e)}")
            
    def get_example_sentence(self, word: str) -> str:
        """获取单词的例句（兼容性方法，调用get_word_example）
        
        Args:
            word: 单词
            
        Returns:
            str: 包含例句和翻译的文本，如果获取失败返回默认例句
        """
        return self.get_word_example(word)

    def is_ai_available(self) -> bool:
        """检查AI功能是否可用

        Returns:
            bool: AI功能是否可用
        """
        # 初始化AI管理器（如果尚未初始化）
        if not self.ai_manager:
            self._init_ai_manager()

        # 每次都重新检查连接状态
        try:
            import requests

            # 尝试连接Ollama API进行可用性检查
            try:
                response = requests.get("http://localhost:11434", timeout=2)
                if response.status_code == 200:
                    # 更新AI可用状态
                    self.ai_available = True
                    return True
                else:
                    log_warning(f"Ollama服务返回非200状态码: {response.status_code}")
                    self.ai_available = False
                    return False
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as conn_err:
                # 连接失败，可能是Ollama未启动或不可用
                log_warning(f"无法连接到Ollama服务，AI功能不可用: {str(conn_err)}")
                self.ai_available = False
                return False
        except ImportError:
            log_warning("requests模块未安装，AI功能不可用")
            self.ai_available = False
            return False
        except Exception as e:
            log_error(f"检查AI可用性时发生异常: {str(e)}")
            self.ai_available = False
            return False

    def get_words_by_criteria(self, criteria: Dict) -> List[str]:
        """根据条件获取单词

        Args:
            criteria: 条件字典，支持以下键：
                - 'unfamiliar': 布尔值，表示是否只获取不熟悉的单词
                - 'difficult': 布尔值，表示是否只获取困难单词
                - 'min_length': 整数，表示单词的最小长度
                - 'max_length': 整数，表示单词的最大长度

        Returns:
            List[str]: 符合条件的单词列表
        """
        words = self.get_all_words()

        # 按条件过滤单词
        if criteria.get('unfamiliar', False):
            unfamiliar_words = self.get_unfamiliar_words()
            words = [word for word in words if word in unfamiliar_words]

        if criteria.get('difficult', False):
            difficult_words = self.get_difficult_words()
            words = [word for word in words if word in difficult_words]

        min_length = criteria.get('min_length')
        if min_length is not None:
            words = [word for word in words if len(word) >= min_length]

        max_length = criteria.get('max_length')
        if max_length is not None:
            words = [word for word in words if len(word) <= max_length]

        return words
    
    def check_today_progress_completed(self) -> bool:
        """
        检查单词学习模块是否标记为完成状态
        
        Returns:
            True/False: 今日学习是否已完成
        """
        try:
            # 从数据库查询今日是否完成学习
            today = datetime.now().strftime("%Y-%m-%d")
            result = self.db_manager.execute_read(
                """
                SELECT COUNT(*) as count 
                FROM exercise_sessions 
                WHERE exercise_type = 'completed' AND start_time LIKE ?
                """,
                (f"{today}%",)
            )
            
            if result and result[0]['count'] > 0:
                log_info("今日学习进度已完成")
                return True
            
            log_info("今日学习进度未完成")
            return False
        except Exception as e:
            log_error(f"检查今日学习进度失败: {str(e)}")
            return False
    
    def migrate_old_translations(self):
        """迁移旧格式的翻译数据到新的多词性多义项结构
        
        Returns:
            int: 成功迁移的单词数量
        """
        try:
            import json
            
            # 获取所有单词
            all_words = self.db_manager.execute_read("SELECT id, word, translation FROM words")
            
            if not all_words:
                log_info("没有需要迁移的单词")
                return 0
            
            migrated_count = 0
            
            for word_data in all_words:
                word_id = word_data['id']
                word = word_data['word']
                translation = word_data['translation']
                
                # 跳过已经是新格式的翻译
                if isinstance(translation, str) and translation.startswith('['):
                    try:
                        parsed = json.loads(translation)
                        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
                            continue
                    except json.JSONDecodeError:
                        pass
                
                # 为旧格式翻译创建新结构
                new_translation = []
                
                # 如果是字符串，拆分为多个含义
                if isinstance(translation, str):
                    import re
                    meanings = re.split(r"[;,；、/|]", translation)
                    meanings = [m.strip() for m in meanings if m.strip()]
                    
                    if meanings:
                        # 如果有词性信息，使用现有词性，否则为空
                        tag = word_data.get('tag', '')
                        new_translation.append({
                            'tag': tag,
                            'meaning_zh': meanings
                        })
                
                if new_translation:
                    # 更新数据库
                    new_translation_json = json.dumps(new_translation, ensure_ascii=False)
                    success, msg = self.update_word(word_id, translation=new_translation_json)
                    if success:
                        migrated_count += 1
                        log_info(f"迁移单词 '{word}' 的翻译格式成功")
                    else:
                        log_error(f"迁移单词 '{word}' 的翻译格式失败: {msg}")
                
            log_info(f"翻译格式迁移完成，共迁移 {migrated_count} 个单词")
            return migrated_count
            
        except Exception as e:
            log_error(f"迁移旧翻译格式失败: {str(e)}")
            return 0
    
    def check_translation(self, word: str, user_translation: str, update_stats: bool = True, translation_mode: str = 'ai_first') -> bool:
        """检查用户翻译是否正确
        
        Args:
            word: 单词
            user_translation: 用户输入的翻译
            update_stats: 是否更新统计信息
            
        Returns:
            bool: 翻译是否正确
        """
        try:
            import re

            def normalize(s: str) -> str:
                if s is None:
                    return ""
                s = s.strip().lower()
                # 移除括号内说明
                s = re.sub(r"\([^)]*\)", "", s)
                s = re.sub(r"（[^）]*）", "", s)
                # 替换常见分隔符为统一分隔符
                for sep in [";", "；", ",", "、", "/", "|"]:
                    s = s.replace(sep, ";")
                # 去掉标点符号（中英文）和多余空格
                import string as _string
                punct = re.escape(_string.punctuation) + "，。！？；：“”‘’、（）【】—…·、、·"
                s = re.sub(f"[{punct}]", "", s)
                s = re.sub(r"\s+", " ", s).strip()
                return s

            word_lower = word.lower()
            correct_translation = self.get_word_translation(word_lower)

            if not correct_translation:
                log_warning(f"无法检查翻译: 单词 '{word}' 没有对应的翻译")
                return False
            
            # 提取所有可能的候选翻译
            candidates = []
            
            # 处理新格式（多词性多义项结构）
            if isinstance(correct_translation, list):
                for item in correct_translation:
                    if isinstance(item, dict) and 'meaning_zh' in item:
                        meanings = item['meaning_zh']
                        if isinstance(meanings, list):
                            candidates.extend([normalize(m) for m in meanings if m and m.strip()])
                        elif isinstance(meanings, str):
                            candidates.append(normalize(meanings))
            # 处理旧格式（字符串）
            elif isinstance(correct_translation, str):
                # 先尝试作为JSON解析（处理可能存储为字符串的新格式）
                try:
                    import json
                    if correct_translation.startswith('['):
                        parsed = json.loads(correct_translation)
                        if isinstance(parsed, list):
                            for item in parsed:
                                if isinstance(item, dict) and 'meaning_zh' in item:
                                    meanings = item['meaning_zh']
                                    if isinstance(meanings, list):
                                        candidates.extend([normalize(m) for m in meanings if m and m.strip()])
                                    elif isinstance(meanings, str):
                                        candidates.append(normalize(meanings))
                            # 如果成功解析为新格式，不再处理为字符串
                            if candidates:
                                pass
                            else:
                                # 如果解析为列表但没有提取到候选，继续按字符串处理
                                raise json.JSONDecodeError("Invalid format", correct_translation, 0)
                        else:
                            # 解析结果不是列表，继续按字符串处理
                            raise json.JSONDecodeError("Not a list", correct_translation, 0)
                    else:
                        # 不是JSON格式，按字符串处理
                        raise json.JSONDecodeError("Not JSON", correct_translation, 0)
                except json.JSONDecodeError:
                    # 按旧格式字符串处理
                    candidates_raw = re.split(r"[;,；、/|]", correct_translation)
                    candidates = [normalize(c) for c in candidates_raw if c and c.strip()]

            # 如果没有分拆出候选，则把整个翻译作为单候选
            if not candidates:
                candidates = [normalize(str(correct_translation))]

            user_normalized = normalize(user_translation)
            is_correct = False

            # 根据翻译判定模式选择不同的判断策略
            if translation_mode == 'local_first' or translation_mode == 'local_only':
                # 本地优先或仅本地：先尝试本地判断
                # 精确匹配或包含匹配（用户输入可能是简短形式）
                for cand in candidates:
                    if not cand:
                        continue
                    if user_normalized == cand:
                        is_correct = True
                        break
                    # 容错：用户输入包含候选或候选包含用户输入（如只输入关键词）
                    if user_normalized and (user_normalized in cand or cand in user_normalized):
                        is_correct = True
                        break
                
                # 如果是本地优先且本地判断失败，尝试AI判断
                if not is_correct and translation_mode == 'local_first' and self.ai_available and self.ai_manager:
                    try:
                        # 使用格式化后的翻译进行AI评估
                        formatted_translation = self._format_translation(correct_translation)
                        eval_result = self.ai_manager.evaluate_sync(formatted_translation, user_translation)
                        if isinstance(eval_result, dict):
                            ai_is_correct = bool(eval_result.get('is_correct'))
                            similarity = float(eval_result.get('similarity', 0)) if eval_result.get('similarity') is not None else 0.0
                            # Accept when AI says correct, or similarity is high (>=0.8)
                            if ai_is_correct or similarity >= 0.8:
                                is_correct = True
                    except Exception as ai_e:
                        log_warning(f"调用AI评估翻译失败: {str(ai_e)}")
            elif translation_mode == 'ai_first':
                # AI优先：先尝试AI判断
                try:
                    if self.ai_available and self.ai_manager:
                        try:
                            # 使用格式化后的翻译进行AI评估
                            formatted_translation = self._format_translation(correct_translation)
                            eval_result = self.ai_manager.evaluate_sync(formatted_translation, user_translation)
                            if isinstance(eval_result, dict):
                                ai_is_correct = bool(eval_result.get('is_correct'))
                                similarity = float(eval_result.get('similarity', 0)) if eval_result.get('similarity') is not None else 0.0
                                # Accept when AI says correct, or similarity is high (>=0.8)
                                if ai_is_correct or similarity >= 0.8:
                                    is_correct = True
                                else:
                                    is_correct = False
                        except Exception as ai_e:
                            log_warning(f"调用AI评估翻译失败，回退本地判断: {str(ai_e)}")
                            # AI失败，回退到本地判断
                            is_correct = False
                    else:
                        # AI不可用，使用本地判断
                        is_correct = False
                except Exception:
                    # 保守处理：若任何AI交互错误，回退到本地判断
                    is_correct = False
                
                # 如果AI判断失败或不可用，使用本地判断
                if not is_correct:
                    for cand in candidates:
                        if not cand:
                            continue
                        if user_normalized == cand:
                            is_correct = True
                            break
                        # 容错：用户输入包含候选或候选包含用户输入（如只输入关键词）
                        if user_normalized and (user_normalized in cand or cand in user_normalized):
                            is_correct = True
                            break

            if update_stats:
                if is_correct:
                    # 翻译正确，更新熟练度
                    self.update_word_proficiency(word_lower, True)
                    self.update_word_weight(word_lower, True, 0)
                    log_info(f"翻译正确: {word} -> {user_translation}, mode={translation_mode}")
                else:
                    # 翻译错误，更新熟练度
                    self.update_word_proficiency(word_lower, False)
                    self.update_word_weight(word_lower, False, 0)
                    log_info(f"翻译错误: {word} -> 用户输入: {user_translation}, 正确翻译: {correct_translation}, mode={translation_mode}")

            return is_correct
        except Exception as e:
            log_error(f"检查翻译失败: {str(e)}")
            return False