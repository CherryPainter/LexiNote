import json
import re
from typing import Optional, Any

from logger import log_error


def extract_json_from_text(text: str) -> Optional[Any]:
    """尝试从任意文本中提取并解析第一个 JSON 对象。

    返回解析后的 Python 对象；若无法解析则返回 None。
    """
    if not text:
        return None

    # 预处理文本，清理常见的干扰内容
    cleaned_text = text.strip()

    # 移除可能的JSON代码块标记
    if cleaned_text.startswith('```json'):
        cleaned_text = cleaned_text[7:]
    if cleaned_text.endswith('```'):
        cleaned_text = cleaned_text[:-3]

    # 移除可能的开场白或结束语
    cleaned_text = re.sub(r'^[^{]*', '', cleaned_text)  # 移除开头直到第一个 { 之前的内容
    cleaned_text = re.sub(r'[^}]*$', '', cleaned_text)  # 移除最后一个 } 之后的内容

    cleaned_text = cleaned_text.strip()

    # 1. 直接尝试解析整个文本
    try:
        return json.loads(cleaned_text)
    except Exception:
        pass

    # 2. 尝试清理文本后再次解析
    try:
        # 替换常见的问题字符
        cleaned_text = cleaned_text.replace('\n', ' ').replace('\t', ' ')
        # 确保引号正确转义
        cleaned_text = re.sub(r'(?<!\\)'"'", '"', cleaned_text)  # 将单引号替换为双引号
        # 移除多余的空格
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        return json.loads(cleaned_text)
    except Exception:
        pass

    # 3. 使用正则寻找所有可能的JSON对象（非贪婪）
    try:
        # 查找所有可能的JSON对象（更复杂的模式）
        candidates = re.findall(r"\{[^}]*\}", cleaned_text, re.DOTALL)
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except Exception:
                # 尝试修复这个候选对象
                try:
                    # 修复缺失的逗号
                    fixed_candidate = re.sub(r'"\}\s*"', '","', candidate)
                    # 修复缺失的引号
                    fixed_candidate = re.sub(r'(\w+):', '"\1":', fixed_candidate)
                    return json.loads(fixed_candidate)
                except Exception:
                    continue
    except Exception:
        pass

    # 4. 寻找最外层的花括号匹配（贪婪）
    try:
        # 找到第一个 { 和最后一个 }
        first_brace = cleaned_text.find('{')
        last_brace = cleaned_text.rfind('}')
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            candidate = cleaned_text[first_brace:last_brace + 1]
            try:
                return json.loads(candidate)
            except Exception:
                # 尝试清理这个候选对象
                try:
                    candidate = candidate.replace('\n', '').replace('\t', '')
                    return json.loads(candidate)
                except Exception:
                    pass
    except Exception:
        pass

    # 5. 尝试更激进的预处理
    try:
        # 移除所有非JSON字符，只保留基本的JSON结构字符
        cleaned_text = re.sub(r'[^\{\}\[\]"\:,\.\s\w\-\+\*/\\]', '', cleaned_text)
        # 再次尝试解析
        return json.loads(cleaned_text)
    except Exception as e:
        log_error(f"extract_json_from_text错误: {e}")

    return None
