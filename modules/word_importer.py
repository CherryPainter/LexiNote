"""单词批量导入模块，负责从JSON文件批量导入单词到数据库"""
import os
import json
from typing import Dict, Tuple

from logger import log_info, log_error, log_warning
from core.database_manager import DatabaseManager


class WordImporter:
    """单词导入器类，提供从JSON文件批量导入单词的功能"""
    
    def __init__(self):
        """初始化单词导入器"""
        self.db_manager = DatabaseManager()
    
    def import_from_json_file(self, json_file_path: str) -> Tuple[bool, Dict]:
        """从JSON文件导入单词到数据库
        
        Args:
            json_file_path: JSON文件路径，文件格式应与data/word_dict.json相同
            {"word1": "translation1", "word2": "translation2", ...}
        
        Returns:
            Tuple[bool, Dict]: 导入是否成功和统计信息
            统计信息包含: total(总单词数), imported(成功导入), skipped(跳过的单词)
        """
        result = {
            "total": 0,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        try:
            # 检查文件是否存在
            if not os.path.exists(json_file_path):
                error_msg = f"文件不存在: {json_file_path}"
                log_error(error_msg)
                result["errors"].append(error_msg)
                return False, result
            
            # 读取JSON文件
            log_info(f"开始读取单词文件: {json_file_path}")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                word_dict = json.load(f)
            
            # 验证数据格式
            if not isinstance(word_dict, dict):
                error_msg = f"文件格式错误，需要JSON对象: {json_file_path}"
                log_error(error_msg)
                result["errors"].append(error_msg)
                return False, result
            
            result["total"] = len(word_dict)
            log_info(f"读取到 {result['total']} 个单词")
            
            # 准备批量插入数据
            words_to_import = []
            for word, translation in word_dict.items():
                # 验证单词和翻译格式
                if not isinstance(word, str) or not word.strip():
                    log_warning(f"跳过无效单词: {word}")
                    result["skipped"] += 1
                    continue
                
                if not isinstance(translation, str) or not translation.strip():
                    log_warning(f"跳过无效翻译的单词: {word}")
                    result["skipped"] += 1
                    continue
                
                words_to_import.append((word.strip(), translation.strip()))
            
            # 批量导入到数据库
            if words_to_import:
                log_info(f"准备导入 {len(words_to_import)} 个单词到数据库")
                success = self.db_manager.execute_write_many(
                    "INSERT OR IGNORE INTO words (word, translation) VALUES (?, ?)",
                    words_to_import
                )
                
                if success:
                    # 获取实际导入的单词数（过滤掉重复的单词）
                    # 先获取导入前的单词数量
                    before_count = len(self.db_manager.get_all_words())
                    
                    # 因为使用了INSERT OR IGNORE，我们需要查询数据库来确定实际导入的数量
                    # 或者我们可以查询每个单词是否存在
                    # 这里采用更高效的方法，重新获取所有单词并计算差异
                    after_count = len(self.db_manager.get_all_words())
                    result["imported"] = after_count - before_count
                    result["skipped"] = result["total"] - result["imported"]
                    
                    log_info(f"单词导入完成: 成功导入 {result['imported']} 个，跳过 {result['skipped']} 个")
                    return True, result
                else:
                    error_msg = "批量导入数据库失败"
                    log_error(error_msg)
                    result["errors"].append(error_msg)
                    return False, result
            else:
                log_info("没有有效的单词需要导入")
                return True, result
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析错误: {str(e)}"
            log_error(error_msg)
            result["errors"].append(error_msg)
            return False, result
        except Exception as e:
            error_msg = f"导入单词时发生错误: {str(e)}"
            log_error(error_msg)
            result["errors"].append(error_msg)
            return False, result


def import_words_from_json(json_file_path: str) -> Dict:
    """便捷函数：从JSON文件批量导入单词
    
    Args:
        json_file_path: JSON文件路径
    
    Returns:
        Dict: 导入结果统计信息
    """
    importer = WordImporter()
    success, stats = importer.import_from_json_file(json_file_path)
    stats["success"] = success
    return stats


if __name__ == "__main__":
    # 命令行使用示例
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        result = import_words_from_json(json_file)
        
        print(f"\n导入结果:")
        print(f"  状态: {'成功' if result['success'] else '失败'}")
        print(f"  总计单词: {result['total']}")
        print(f"  成功导入: {result['imported']}")
        print(f"  跳过单词: {result['skipped']}")
        
        if result['errors']:
            print(f"  错误信息:")
            for error in result['errors']:
                print(f"    - {error}")
    else:
        print("使用方法: python -m modules.word_importer <json文件路径>")