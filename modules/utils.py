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

    # 直接尝试解析整个文本
    try:
        return json.loads(text)
    except Exception:
        pass

    # 使用正则寻找第一个花括号包裹的 JSON 对象（非贪婪）
    try:
        m = re.search(r"\{.*?\}", text, re.DOTALL)
        if m:
            candidate = m.group(0)
            try:
                return json.loads(candidate)
            except Exception:
                # 再尝试贪婪匹配，覆盖多行复杂情况
                m2 = re.search(r"\{.*\}", text, re.DOTALL)
                if m2:
                    try:
                        return json.loads(m2.group(0))
                    except Exception:
                        return None
    except Exception as e:
        log_error(f"extract_json_from_text错误: {e}")

    return None
