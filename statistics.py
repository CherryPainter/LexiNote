from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.database_manager import DatabaseManager
from logger import log_info, log_error


class StatisticsManager:
    """统计管理器类，用于处理所有学习统计相关功能
    
    该类提供了全面的学习统计功能，包括：
    - 单词学习统计
    - 练习进度统计
    - 每日学习情况统计
    - 学习趋势分析
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化统计管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def get_total_word_count(self) -> int:
        """获取总单词数
        
        Returns:
            int: 总单词数
        """
        try:
            result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM words"
            )[0]
            return result['count']
        except Exception as e:
            log_error(f"获取总单词数失败: {str(e)}")
            return 0
    
    def get_learned_word_count(self) -> int:
        """获取已学习单词数
        
        Returns:
            int: 已学习单词数（熟练度大于0的单词）
        """
        try:
            result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM words WHERE proficiency > 0"
            )[0]
            return result['count']
        except Exception as e:
            log_error(f"获取已学习单词数失败: {str(e)}")
            return 0
    
    def get_total_practice_count(self) -> int:
        """获取总练习次数
        
        Returns:
            int: 总练习次数
        """
        try:
            result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM progress"
            )[0]
            return result['count']
        except Exception as e:
            log_error(f"获取总练习次数失败: {str(e)}")
            return 0
    
    def get_total_correct_count(self) -> int:
        """获取总正确次数
        
        Returns:
            int: 总正确次数
        """
        try:
            result = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM progress WHERE is_correct = 1"
            )[0]
            return result['count']
        except Exception as e:
            log_error(f"获取总正确次数失败: {str(e)}")
            return 0
    
    def get_overall_accuracy(self) -> float:
        """获取总体正确率
        
        Returns:
            float: 总体正确率（0.0-1.0）
        """
        try:
            result = self.db_manager.execute_read(
                """SELECT 
                    COUNT(*) as total, 
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct 
                FROM progress"""
            )[0]
            
            if result['total'] > 0:
                return result['correct'] / result['total']
            return 0.0
        except Exception as e:
            log_error(f"获取总体正确率失败: {str(e)}")
            return 0.0
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """获取每日学习统计
        
        Args:
            date: 指定日期（格式：YYYY-MM-DD），默认获取今日统计
            
        Returns:
            Dict: 每日统计信息
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # 每日练习次数
            daily_practices = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM progress WHERE practice_date LIKE ?",
                (f"{date}%",)
            )[0]['count']
            
            # 每日正确次数
            daily_correct = self.db_manager.execute_read(
                "SELECT COUNT(*) as count FROM progress WHERE practice_date LIKE ? AND is_correct = 1",
                (f"{date}%",)
            )[0]['count']
            
            # 每日学习单词数
            daily_words = self.db_manager.execute_read(
                "SELECT COUNT(DISTINCT word) as count FROM progress WHERE practice_date LIKE ?",
                (f"{date}%",)
            )[0]['count']
            
            return {
                "date": date,
                "practices": daily_practices,
                "correct": daily_correct,
                "words": daily_words,
                "accuracy": daily_correct / daily_practices if daily_practices > 0 else 0.0
            }
        except Exception as e:
            log_error(f"获取每日学习统计失败: {str(e)}")
            return {
                "date": date or datetime.now().strftime('%Y-%m-%d'),
                "practices": 0,
                "correct": 0,
                "words": 0,
                "accuracy": 0.0
            }
    
    def get_weekly_stats(self) -> List[Dict]:
        """获取最近7天的学习统计
        
        Returns:
            List[Dict]: 包含最近7天统计信息的列表
        """
        try:
            weekly_stats = []
            today = datetime.now()
            
            for i in range(7):
                date = today - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                daily_stat = self.get_daily_stats(date_str)
                weekly_stats.append(daily_stat)
            
            # 按日期升序排序
            weekly_stats.sort(key=lambda x: x['date'])
            return weekly_stats
        except Exception as e:
            log_error(f"获取每周学习统计失败: {str(e)}")
            return []
    
    def get_proficiency_stats(self) -> Dict[str, int]:
        """获取熟练度分布统计
        
        Returns:
            Dict: 各熟练度区间的单词数量
        """
        try:
            # 定义熟练度区间
            intervals = [
                (0, 0, "未学习"),
                (0.01, 0.3, "不熟悉"),
                (0.31, 0.7, "一般"),
                (0.71, 1.0, "熟练")
            ]
            
            stats = {}
            for min_prof, max_prof, label in intervals:
                if min_prof == max_prof:
                    # 未学习（熟练度为0）
                    result = self.db_manager.execute_read(
                        "SELECT COUNT(*) as count FROM words WHERE proficiency = ?",
                        (min_prof,)
                    )[0]
                else:
                    # 其他区间
                    result = self.db_manager.execute_read(
                        "SELECT COUNT(*) as count FROM words WHERE proficiency > ? AND proficiency <= ?",
                        (min_prof, max_prof)
                    )[0]
                stats[label] = result['count']
            
            return stats
        except Exception as e:
            log_error(f"获取熟练度分布统计失败: {str(e)}")
            return {
                "未学习": 0,
                "不熟悉": 0,
                "一般": 0,
                "熟练": 0
            }
    
    def get_word_set_stats(self, set_id: Optional[int] = None) -> Dict:
        """获取词库统计信息
        
        Args:
            set_id: 词库ID，默认获取所有词库统计
            
        Returns:
            Dict: 词库统计信息
        """
        try:
            if set_id is None:
                # 获取所有词库统计
                word_sets = self.db_manager.execute_read("SELECT id, name FROM word_sets")
                stats = {}
                
                for word_set in word_sets:
                    set_id = word_set['id']
                    set_name = word_set['name']
                    
                    # 词库单词数
                    word_count = self.db_manager.execute_read(
                        "SELECT COUNT(*) as count FROM words WHERE set_id = ?",
                        (set_id,)
                    )[0]['count']
                    
                    # 已学习单词数
                    learned_count = self.db_manager.execute_read(
                        "SELECT COUNT(*) as count FROM words WHERE set_id = ? AND proficiency > 0",
                        (set_id,)
                    )[0]['count']
                    
                    stats[set_name] = {
                        "word_count": word_count,
                        "learned_count": learned_count,
                        "progress": learned_count / word_count if word_count > 0 else 0.0
                    }
                
                return stats
            else:
                # 获取指定词库统计
                word_set = self.db_manager.execute_read(
                    "SELECT name FROM word_sets WHERE id = ?",
                    (set_id,)
                )[0]
                
                if not word_set:
                    return {}
                
                set_name = word_set['name']
                
                # 词库单词数
                word_count = self.db_manager.execute_read(
                    "SELECT COUNT(*) as count FROM words WHERE set_id = ?",
                    (set_id,)
                )[0]['count']
                
                # 已学习单词数
                learned_count = self.db_manager.execute_read(
                    "SELECT COUNT(*) as count FROM words WHERE set_id = ? AND proficiency > 0",
                    (set_id,)
                )[0]['count']
                
                return {
                    set_name: {
                        "word_count": word_count,
                        "learned_count": learned_count,
                        "progress": learned_count / word_count if word_count > 0 else 0.0
                    }
                }
        except Exception as e:
            log_error(f"获取词库统计信息失败: {str(e)}")
            return {}
    
    def get_recent_progress(self, limit: int = 10) -> List[Dict]:
        """获取最近的学习进度记录
        
        Args:
            limit: 返回记录数限制，默认10条
            
        Returns:
            List[Dict]: 最近的学习进度记录
        """
        try:
            results = self.db_manager.execute_read(
                "SELECT word, is_correct, practice_date FROM progress ORDER BY practice_date DESC LIMIT ?",
                (limit,)
            )
            
            return [
                {
                    "word": result['word'],
                    "is_correct": bool(result['is_correct']),
                    "practice_date": result['practice_date']
                }
                for result in results
            ]
        except Exception as e:
            log_error(f"获取最近学习进度记录失败: {str(e)}")
            return []
    
    def get_summary_stats(self) -> Dict:
        """获取综合统计信息
        
        Returns:
            Dict: 综合统计信息
        """
        try:
            # 总单词数
            total_words = self.get_total_word_count()
            
            # 已学习单词数
            learned_words = self.get_learned_word_count()
            
            # 总练习次数
            total_practices = self.get_total_practice_count()
            
            # 总正确次数
            total_correct = self.get_total_correct_count()
            
            # 总体正确率
            overall_accuracy = self.get_overall_accuracy()
            
            # 今日统计
            today_stats = self.get_daily_stats()
            
            # 熟练度分布
            proficiency_stats = self.get_proficiency_stats()
            
            # 最后学习时间
            last_session = "未开始"
            try:
                result = self.db_manager.execute_read(
                    "SELECT MAX(practice_date) as last_date FROM progress"
                )[0]
                if result['last_date']:
                    last_session = result['last_date']
            except Exception as e:
                log_error(f"获取最后学习时间失败: {str(e)}")
            
            return {
                "total_words": total_words,
                "learned_words": learned_words,
                "total_practices": total_practices,
                "total_correct": total_correct,
                "overall_accuracy": overall_accuracy,
                "today_practices": today_stats['practices'],
                "today_correct": today_stats['correct'],
                "today_accuracy": today_stats['accuracy'],
                "proficiency_distribution": proficiency_stats,
                "last_session": last_session
            }
        except Exception as e:
            log_error(f"获取综合统计信息失败: {str(e)}")
            return {
                "total_words": 0,
                "learned_words": 0,
                "total_practices": 0,
                "total_correct": 0,
                "overall_accuracy": 0.0,
                "today_practices": 0,
                "today_correct": 0,
                "today_accuracy": 0.0,
                "proficiency_distribution": {
                    "未学习": 0,
                    "不熟悉": 0,
                    "一般": 0,
                    "熟练": 0
                },
                "last_session": "未开始"
            }