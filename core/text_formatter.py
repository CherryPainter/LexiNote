import re
from typing import Optional


class TextFormatter:
    """文本格式化工具，用于将Markdown等富文本格式转换为适合tkinter纯文本显示的格式"""
    
    def __init__(self):
        """初始化文本格式化器"""
        # 定义Markdown格式的正则表达式
        self.bold_pattern = re.compile(r'\*\*(.*?)\*\*')  # **粗体**
        self.italic_pattern = re.compile(r'\*(.*?)\*|_(.*?)_')  # *斜体* 或 _斜体_
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE)  # # 标题
        self.unordered_list_pattern = re.compile(r'(^|\n)(\s*)([-*+])\s+', re.MULTILINE)  # 无序列表项
        self.ordered_list_pattern = re.compile(r'(^|\n)(\s*)(\d+\.)\s+', re.MULTILINE)  # 有序列表项
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)  # 代码块
        self.inline_code_pattern = re.compile(r'`([^`]+)`')  # `行内代码`
        self.link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')  # [链接文本](链接地址)
    
    def format_for_tkinter(self, text: Optional[str]) -> str:
        """将富文本格式转换为适合tkinter显示的纯文本格式
        
        Args:
            text: 原始富文本内容
            
        Returns:
            格式化后的纯文本
        """
        if not text:
            return ""
        
        formatted_text = text
        
        # 移除可能导致垂直堆叠的特殊字符和格式
        formatted_text = self._remove_vertical_stack_chars(formatted_text)
        
        # 首先处理所有的列表格式（无序列表和有序列表）
        formatted_text = self._format_all_lists(formatted_text)
        
        # 处理行内格式（粗体、斜体、行内代码）
        formatted_text = self._format_inline_elements(formatted_text)
        
        # 处理链接
        formatted_text = self._format_links(formatted_text)
        
        # 清理残留的星号
        formatted_text = self._cleanup_asterisks(formatted_text)
        
        # 调整整体排版
        formatted_text = self._adjust_formatting(formatted_text)
        
        return formatted_text
    
    def _remove_vertical_stack_chars(self, text: str) -> str:
        """移除可能导致垂直堆叠的特殊字符和格式
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 移除可能导致显示问题的特殊字符
        text = re.sub(r'\x00-\x08\x0B\x0C\x0E-\x1F', '', text)  # 控制字符
        text = re.sub(r'\r', '', text)  # 回车符
        
        # 确保没有连续的换行符
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _format_inline_elements(self, text: str) -> str:
        """处理行内元素（粗体、斜体、行内代码）
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 处理行内代码
        text = self.inline_code_pattern.sub(r'"\1"', text)
        
        # 处理粗体（**内容**）
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # 处理斜体（*内容* 或 _内容_）
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        return text
    
    def _cleanup_asterisks(self, text: str) -> str:
        """清理残留的星号
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 移除单独的星号（不在单词内部的）
        text = re.sub(r'(?<!\w)\*(?!\w)', ' ', text)
        
        # 移除连续的星号
        text = re.sub(r'\*{2,}', ' ', text)
        
        return text
    
    def _format_all_lists(self, text: str) -> str:
        """处理所有列表格式，包括嵌套列表
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 处理无序列表项，匹配以*、-、+开头的行
        # 考虑各种可能的缩进情况
        text = re.sub(r'(^|\n)(\s*)\*\s+', r'\1\2• ', text)
        text = re.sub(r'(^|\n)(\s*)-\s+', r'\1\2• ', text)
        text = re.sub(r'(^|\n)(\s*)\+\s+', r'\1\2• ', text)
        
        # 处理有序列表项，保持数字格式
        text = re.sub(r'(^|\n)(\s*)(\d+)\.\s+', r'\1\2\3. ', text)
        
        return text
    
    def _adjust_formatting(self, text: str) -> str:
        """调整整体排版格式
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 确保段落之间有适当的空行
        text = re.sub(r'\n\s*\n', r'\n\n', text)
        
        # 确保每行开头没有多余的空格
        text = re.sub(r'\n\s+', r'\n', text)
        
        # 移除多余的空行
        text = re.sub(r'\n{3,}', r'\n\n', text)
        
        return text
    
    def _format_code_blocks(self, text: str) -> str:
        """处理代码块
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        def replace_code_block(match):
            lang = match.group(1) or ""
            code = match.group(2)
            # 用特殊符号包围代码块，增加可读性
            return f"\n=== 代码块{(' (' + lang + ')') if lang else ''} ===\n{code}\n================\n"
        
        return self.code_block_pattern.sub(replace_code_block, text)
    
    def _format_inline_code(self, text: str) -> str:
        """处理行内代码
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 将行内代码用双引号包围，保持区分
        return self.inline_code_pattern.sub(r'"\1"', text)
    
    def _format_headings(self, text: str) -> str:
        """处理标题
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        def replace_heading(match):
            hashes = match.group(1)
            heading_text = match.group(2)
            level = len(hashes)
            
            # 根据标题级别使用不同的强调方式
            if level == 1:
                return f"\n{'='*50}\n{heading_text}\n{'='*50}\n"
            elif level == 2:
                return f"\n{heading_text}\n{'='*len(heading_text)}\n"
            else:
                return f"\n{'>'*level} {heading_text}\n"
        
        return self.heading_pattern.sub(replace_heading, text)
    

    
    def _format_links(self, text: str) -> str:
        """处理链接
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 将链接转换为 "链接文本 (链接地址)" 格式
        return self.link_pattern.sub(r'\1 (\2)', text)
    
    def _format_bold_italic(self, text: str) -> str:
        """处理粗体和斜体
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 用全角空格包围强调内容，模拟粗体效果
        def replace_bold(match):
            content = match.group(1) or match.group(2)
            return f"　{content}　"  # 使用全角空格包围
        
        # 先处理粗体
        text = self.bold_pattern.sub(replace_bold, text)
        
        # 再处理斜体
        text = self.italic_pattern.sub(replace_bold, text)
        
        return text
    
    def _adjust_empty_lines(self, text: str) -> str:
        """调整空行，确保适当的间距
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 将多个空行合并为一个
        text = re.sub(r'\n\s*\n', r'\n\n', text)
        # 确保文本开头没有多余的空行
        text = text.lstrip('\n')
        # 确保文本结尾有一个空行
        if not text.endswith('\n'):
            text += '\n'
        
        return text
    
    def strip_markdown(self, text: Optional[str]) -> str:
        """简单地移除所有Markdown标记
        
        Args:
            text: 原始文本
            
        Returns:
            移除标记后的纯文本
        """
        if not text:
            return ""
        
        # 移除所有Markdown标记
        text = self.code_block_pattern.sub(r'\2', text)
        text = self.inline_code_pattern.sub(r'\1', text)
        text = self.heading_pattern.sub(r'\2', text)
        text = self.list_pattern.sub(r'\3', text)
        text = self.link_pattern.sub(r'\1', text)
        text = self.bold_pattern.sub(r'\1\2', text)
        text = self.italic_pattern.sub(r'\1', text)
        
        return text