import json
import time
import os
import requests
from typing import Dict, Optional, Tuple
import threading

from logger import log_info, log_error, log_warning
from core.ai_interface import AIManager
from .database import ComprehensionDatabase
from .utils import extract_json_from_text


class AIService:
    """AI服务类，负责生成题目和判题"""
    
    def __init__(self):
        """初始化AI服务"""
        self.ai_manager = AIManager()
        self.db_manager = ComprehensionDatabase()
        self._lock = threading.RLock()
        
        # 测试AI连接状态
        self.ai_available = self._test_ai_connection()
        
    def _get_available_models(self) -> list:
        """获取可用的Ollama模型列表
        
        Returns:
            可用模型名称列表
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            log_warning(f"获取可用模型列表失败: {str(e)}")
        return []

    def _save_raw_response(self, tag: str, content: str):
        """将原始 AI 返回保存到 cache 目录，便于排查"""
        try:
            cache_dir = getattr(self.ai_manager, 'cache_dir', None) or os.path.join('cache', 'ai_text')
            os.makedirs(cache_dir, exist_ok=True)
            filename = f"{tag}_{int(time.time())}.txt"
            path = os.path.join(cache_dir, filename)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content if content is not None else '')
            log_info(f"已保存原始AI响应到: {path}")
        except Exception as e:
            log_warning(f"保存原始AI响应失败: {str(e)}")
    
    def _test_ai_connection(self) -> bool:
        """测试AI连接是否可用
        
        Returns:
            bool: AI连接是否可用
        """
        try:
            # 首先检查服务是否运行
            try:
                # 使用 /api/tags 作为健康检查端点
                health_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if health_response.status_code != 200:
                    log_warning(f"Ollama服务运行异常，状态码: {health_response.status_code}")
                    return False
            except requests.RequestException as e:
                log_warning(f"Ollama服务连接失败: {str(e)}")
                return False
            
            # 然后测试模型响应
            test_prompt = "请回复'OK'"
            response = self.ai_manager._ask_sync(test_prompt)
            log_info(f"AI连接测试响应: {response[:50]}...")
            return "OK" in response
        except Exception as e:
            log_warning(f"AI连接测试失败: {str(e)}")
            return False
    
    def is_ai_available(self) -> bool:
        """检查AI服务是否可用，每次调用都重新测试连接状态
        
        Returns:
            bool: AI服务是否可用
        """
        # 每次调用都重新测试，以便检测连接恢复
        self.ai_available = self._test_ai_connection()
        return self.ai_available
    
    def generate_cloze_test(self, level: str = "中级", topic: str = "通用") -> Optional[Dict]:
        """生成完形填空题目
        
        Args:
            level: 难度级别（初级/中级/高级）
            topic: 主题
            
        Returns:
            Dict: 包含题目信息的字典
        """
        try:
            if not self.is_ai_available():
                log_error("AI服务不可用，无法生成完形填空题目")
                return None
            
            prompt = f"""
请生成一篇{level}难度的英语完形填空文章，主题为{topic}。

要求：
1. 文章长度适中，包含约200-300个单词
2. 文章内容连贯，适合{level}英语水平的学习者
3. 请在文章中选择10个合适的单词替换为空格
4. 为每个空格提供4个选项，其中只有一个是正确答案
5. 请按照以下JSON格式输出，不要包含其他任何无关内容：

{{
  "title": "文章标题",
  "content": "包含[BLANK_1], [BLANK_2], ..., [BLANK_10]的文章内容",
  "options": [
    {{"blank": 1, "text": "空格1的四个选项，用分号分隔，例如：word1;word2;word3;word4"}},
    {{"blank": 2, "text": "空格2的四个选项"}},
    // 其他空格的选项
  ],
  "answers": "答案序列，例如：1,3,2,4,...",
  "explanation": "题目解析，包括每个空格的正确答案说明，使用中文回答，引用部分可以使用英语"
}}
            """
            
            response = self.ai_manager._ask_sync(prompt)
            
            # 解析AI返回的JSON
            try:
                # 去除可能的代码块标记
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                # 使用工具函数提取JSON
                result = extract_json_from_text(clean_response)
                if result is None:
                    log_error("无法从AI返回中提取有效的JSON")
                    return None
                
                # 处理可能的字段名拼写错误
                if 'answeers' in result:
                    result['answers'] = result.pop('answeers')
                    log_info("已修复字段名拼写错误: answeers -> answers")
                
                # 验证必要字段
                required_fields = ['title', 'content', 'options', 'answers', 'explanation']
                for field in required_fields:
                    if field not in result:
                        log_error(f"AI返回的完形填空数据缺少{field}字段")
                        return None
                
                # 处理选项格式
                processed_options = []
                for opt in result['options']:
                    try:
                        options_list = opt['text'].split(';')
                        processed_options.append({
                            'blank': opt['blank'],
                            'options': options_list
                        })
                    except Exception as e:
                        log_error(f"处理选项失败: {str(e)}")
                        return None
                
                # 保存到数据库
                test_id = self.db_manager.add_cloze_test(
                    title=result['title'],
                    content=result['content'],
                    options=processed_options,
                    answer=result['answers'],
                    explanation=result['explanation']
                )
                
                if test_id > 0:
                    result['id'] = test_id
                    # 兼容字段：数据库中使用 answer 字段，AI 返回可能使用 answers
                    result['answer'] = result.get('answers', result.get('answer'))
                    result['options'] = processed_options
                    log_info(f"成功生成并保存完形填空题目，ID: {test_id}")
                    return result
                else:
                    return None
                    
            except json.JSONDecodeError as e:
                log_error(f"解析AI返回的JSON失败: {str(e)}")
                log_error(f"AI返回内容: {response}")
                # 保存原始响应便于排查
                try:
                    self._save_raw_response('cloze_parse_fail', response)
                except Exception:
                    pass
                return None
                
        except Exception as e:
            log_error(f"生成完形填空题目失败: {str(e)}")
            return None
    
    def generate_reading_comprehension(self, level: str = "中级", 
                                     length: str = "短篇", 
                                     question_count: int = 5) -> Optional[Dict]:
        """生成阅读理解题目
        
        Args:
            level: 难度级别（初级/中级/高级）
            length: 文章长度（短篇/长篇）
            question_count: 题目数量
            
        Returns:
            Dict: 包含题目信息的字典
        """
        try:
            if not self.ai_available:
                log_error("AI服务不可用，无法生成阅读理解题目")
                return None
            
            # 设置文章长度对应的单词数
            word_count = "300-500" if length == "短篇" else "600-800"
            
            prompt = f"""
请生成一篇{length}（约{word_count}个单词）的{level}难度英语阅读理解文章，并附带{question_count}个问题。

要求：
1. 文章内容连贯，主题明确，适合{level}英语水平的学习者
2. 问题类型混合使用选择题和主观题
3. 选择题请提供4个选项，其中只有一个正确答案
4. 所有问题（包括选择题和简答题）必须包含具体的问题内容，**绝对不可以**使用'Question X'或类似的占位符
5. 选择题格式：具体问题内容 A.Option1 B.Option2 C.Option3 D.Option4（选项内容必须使用英文，不可以使用中文）
6. 简答题格式：具体问题内容（例如：请解释文章中提到的主要观点）
7. 答案部分：选择题使用A/B/C/D，主观题提供中文标准参考答案
8. 解析部分：使用中文回答，引用部分可以使用英语
9. 请严格按照以下JSON格式输出，不要包含任何额外的内容、解释或说明：

{{
  "article": "完整的阅读文章内容",
  "questions": [
    "具体问题1（选择题：A.First option B.Second option C.Third option D.Fourth option）",
    "具体问题2（简答题：请解释文章中的关键概念）",
    // 其他问题
  ],
  "answers": [
    "答案1（选择题使用A/B/C/D，主观题提供标准参考答案）",
    "答案2",
    // 其他答案
  ],
  "explanations": [
    "解析1",
    "解析2",
    // 其他解析
  ]
}}
            """
            
            response = self.ai_manager._ask_sync(prompt)
            
            # 保存原始响应用于调试
            self._save_raw_response('reading_generation', response)
            
            # 解析AI返回的JSON
            try:
                # 去除可能的代码块标记
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                # 使用工具函数提取JSON
                result = extract_json_from_text(clean_response)
                if result is None:
                    log_error("无法从AI返回中提取有效的JSON")
                    # 保存原始响应以便排查
                    log_error(f"AI返回原始内容: {response}")
                    try:
                        self._save_raw_response('reading_parse_fail', response)
                    except Exception:
                        pass
                    return None
                
                # 处理可能的字段名拼写错误
                if 'answeers' in result:
                    result['answers'] = result.pop('answeers')
                    log_info("已修复字段名拼写错误: answeers -> answers")
                
                if 'explanaations' in result:
                    result['explanations'] = result.pop('explanaations')
                    log_info("已修复字段名拼写错误: explanaations -> explanations")
                
                # 验证必要字段
                required_fields = ['article', 'questions', 'answers', 'explanations']
                for field in required_fields:
                    if field not in result:
                        log_error(f"AI返回的阅读理解数据缺少{field}字段")
                        return None
                
                # 检查问题内容是否有效
                if not result['questions']:
                    log_error("AI返回的题目为空")
                    self._save_raw_response('reading_invalid_questions', response)
                    return None
                
                # 检查是否有选择题只包含'question'文本
                has_invalid_questions = False
                invalid_question_indices = []
                
                for i, question in enumerate(result['questions']):
                    # 检查是否是选择题
                    is_multiple_choice = any(opt in question.upper() for opt in ["A.", "B.", "C.", "D.", "MULTIPLE CHOICE"])
                    
                    # 检查题目是否只包含'question'文本（特别是选择题）
                    if question.lower().strip() == 'question' or (is_multiple_choice and len(question.strip()) < 10):
                        has_invalid_questions = True
                        invalid_question_indices.append(i+1)  # 题目编号从1开始
                
                if has_invalid_questions:
                    log_error(f"AI返回的选择题内容无效，问题编号: {invalid_question_indices}")
                    log_error(f"无效题目内容示例: {result['questions'][invalid_question_indices[0]-1]}")
                    self._save_raw_response('reading_invalid_questions', response)
                    return None
                
                # 检查问题数量是否匹配
                if len(result['questions']) != len(result['answers']) or \
                   len(result['questions']) != len(result['explanations']):
                    log_error("问题、答案和解析数量不匹配")
                    log_error(f"问题数: {len(result['questions'])}, 答案数: {len(result['answers'])}, 解析数: {len(result['explanations'])}")
                    return None
                
                # 保存到数据库
                test_id = self.db_manager.add_reading_comprehension(
                    article=result['article'],
                    questions=result['questions'],
                    answers=result['answers'],
                    explanations=result['explanations']
                )
                
                if test_id > 0:
                    result['id'] = test_id
                    log_info(f"成功生成并保存阅读理解题目，ID: {test_id}")
                    return result
                else:
                    log_error("保存阅读理解题目到数据库失败")
                    return None
                    
            except Exception as e:
                log_error(f"处理AI返回的阅读理解数据失败: {str(e)}")
                log_error(f"AI返回内容: {response}")
                try:
                    self._save_raw_response('reading_parse_fail', response)
                except Exception:
                    pass
                return None
        except Exception as e:
            log_error(f"生成阅读理解题目失败: {str(e)}")
            return None
    
    def evaluate_cloze_answer(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """评估完形填空答案
        
        Args:
            user_answer: 用户答案
            correct_answer: 正确答案
            
        Returns:
            Tuple[bool, str]: (是否正确, 评估结果)
        """
        try:
            # 简单对比答案
            user_answers = [a.strip() for a in user_answer.split(',')]
            correct_answers = [a.strip() for a in correct_answer.split(',')]
            
            if len(user_answers) != len(correct_answers):
                return False, f"答案数量不匹配，需要{len(correct_answers)}个答案"
            
            correct_count = 0
            for i, (user, correct) in enumerate(zip(user_answers, correct_answers)):
                if user.lower() == correct.lower():
                    correct_count += 1
            
            accuracy = correct_count / len(correct_answers)
            result = f"正确率: {correct_count}/{len(correct_answers)} ({accuracy*100:.1f}%)"
            
            return correct_count == len(correct_answers), result
            
        except Exception as e:
            log_error(f"评估完形填空答案失败: {str(e)}")
            return False, "评估失败"
    
    def evaluate_reading_answer(self, user_answer: str, correct_answer: str, 
                              question_type: str = "选择题") -> Tuple[bool, str]:
        """评估阅读理解答案
        
        Args:
            user_answer: 用户答案
            correct_answer: 正确答案
            question_type: 题目类型（选择题/主观题）
            
        Returns:
            Tuple[bool, str]: (是否正确, 评估结果)
        """
        try:
            if question_type == "选择题":
                # 选择题直接对比
                is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
                result = "答案正确" if is_correct else f"答案错误，正确答案是: {correct_answer}"
                return is_correct, result
            else:
                # 主观题使用AI评估
                if not self.ai_available:
                    return False, "AI服务不可用，无法评估主观题"
                
                prompt = f"""
请评估以下英语阅读理解主观题的答案：

问题：请根据文章内容回答
标准参考答案：{correct_answer}
学生答案：{user_answer}

请从以下几个方面进行评估：
1. 答案是否准确反映了文章内容
2. 语言表达是否清晰准确
3. 是否包含了所有关键信息

请使用中文回答，引用部分可以使用英语。评估结果请以JSON格式输出：
{{
  "is_acceptable": true/false,
  "score": 0-100,
  "feedback": "具体的评估反馈（使用中文）"
}}
                """
                
                response = self.ai_manager._ask_sync(prompt)

                # 尝试解析AI返回的JSON，若失败则尝试提取JSON或重试一次要求AI仅返回JSON
                # 使用公共工具解析 AI 返回的 JSON（支持提取文本中的 JSON 对象）
                eval_result = extract_json_from_text(response)
                if eval_result is None:
                    # 记录原始响应以便排查
                    log_error(f"解析AI评估结果失败，原始返回：{response}")
                    try:
                        self._save_raw_response('eval_first_fail', response)
                    except Exception:
                        pass
                    # 重试：请求AI仅返回JSON格式
                    retry_prompt = prompt + "\n\n请仅返回符合上面JSON格式的JSON对象，不要包含任何解释或额外文本。"
                    retry_response = self.ai_manager._ask_sync(retry_prompt)
                    eval_result = extract_json_from_text(retry_response)

                    if eval_result is None:
                        log_error("二次解析仍失败，返回评估失败")
                        try:
                            self._save_raw_response('eval_second_fail', retry_response)
                        except Exception:
                            pass
                        return False, "评估失败"

                try:
                    is_correct = eval_result.get('is_acceptable', False)
                    score = eval_result.get('score', 0)
                    feedback = eval_result.get('feedback', '')

                    result = f"得分: {score}/100\n反馈: {feedback}"
                    return is_correct, result
                except Exception as e:
                    log_error(f"处理AI评估结果字段失败: {str(e)}")
                    return False, "评估失败"
                    
        except Exception as e:
            log_error(f"评估阅读理解答案失败: {str(e)}")
            return False, "评估失败"