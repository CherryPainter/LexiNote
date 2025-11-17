import tkinter as tk
from tkinter import ttk, messagebox
import json

class TranslationEditor(tk.Frame):
    """
    多词性多义项翻译编辑器组件
    提供友好的界面让用户添加/删除词性和含义，自动生成JSON格式
    """

    def __init__(self, parent, font_config=None, height=200):
        """
        初始化翻译编辑器组件

        Args:
            parent: 父容器
            font_config: 字体配置
            height: 编辑器高度，默认200像素
        """
        super().__init__(parent)

        self.font_config = font_config or {"normal": ("SimHei", 10)}
        self.height = height

        # 设置主框架大小策略
        self.pack_propagate(False)  # 防止框架被内容撑开
        self.config(height=height)

        # 创建主框架
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.pack_propagate(False)
        self.main_frame.config(height=height)

        # 创建滚动条
        self.scrollbar = ttk.Scrollbar(self.main_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建画布并配置滚动
        self.canvas = tk.Canvas(self.main_frame, yscrollcommand=self.scrollbar.set, height=height-10)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        # 创建内部框架用于放置所有内容
        self.inner_frame = tk.Frame(self.canvas)
        self.inner_frame_id = self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW, width=self.canvas.winfo_width())

        # 跟踪内部框架大小变化以更新滚动区域
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # 跟踪画布宽度变化以调整内部框架宽度
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.inner_frame_id, width=e.width))

        # 词性列表
        self.tag_frames = []

        # 添加词性按钮
        self.add_tag_btn = tk.Button(
            self.inner_frame,
            text="+ 添加词性",
            command=self._add_tag,
            font=self.font_config["normal"],
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED
        )
        self.add_tag_btn.pack(fill=tk.X, pady=5)

        # 添加一个默认词性框架
        self._add_tag()

    def _add_tag(self, tag="", meanings=None):
        """
        添加一个词性框架

        Args:
            tag: 词性（如"n", "v"等）
            meanings: 含义列表
        """
        tag_frame = tk.Frame(self.inner_frame, relief=tk.RAISED, bd=1, padx=10, pady=10)

        # 词性输入
        tag_row = tk.Frame(tag_frame)
        tag_row.pack(fill=tk.X, pady=5)

        tk.Label(tag_row, text="词性:", font=self.font_config["normal"]).pack(side=tk.LEFT, padx=5)
        tag_var = tk.StringVar(value=tag)
        tag_entry = tk.Entry(tag_row, textvariable=tag_var, font=self.font_config["normal"], width=10)
        tag_entry.pack(side=tk.LEFT, padx=5)

        # 删除词性按钮
        delete_tag_btn = tk.Button(
            tag_row,
            text="×",
            command=lambda: self._delete_tag(tag_frame),
            font=self.font_config["normal"],
            bg="#f44336",
            fg="white",
            width=2,
            relief=tk.RAISED
        )
        delete_tag_btn.pack(side=tk.RIGHT, padx=5)

        # 含义列表
        meaning_entries = []
        meanings = meanings or []

        # 含义框架
        meanings_frame = tk.Frame(tag_frame)
        meanings_frame.pack(fill=tk.X, pady=5)

        # 添加含义按钮
        add_meaning_btn = tk.Button(
            meanings_frame,
            text="+ 添加含义",
            command=lambda: self._add_meaning(meanings_frame, meaning_entries),
            font=self.font_config["normal"],
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED
        )
        add_meaning_btn.pack(fill=tk.X, pady=5)

        # 添加现有含义
        for meaning in meanings:
            self._add_meaning(meanings_frame, meaning_entries, meaning)

        # 如果没有含义，添加一个默认的
        if not meanings:
            self._add_meaning(meanings_frame, meaning_entries)

        # 保存框架信息
        tag_frame_info = {
            "frame": tag_frame,
            "tag_var": tag_var,
            "meaning_entries": meaning_entries
        }
        self.tag_frames.append(tag_frame_info)

        # 重新排列框架
        self._rearrange_frames()

    def _add_meaning(self, parent, meaning_entries, meaning=""):
        """
        添加一个含义输入框

        Args:
            parent: 父容器
            meaning_entries: 含义输入框列表
            meaning: 初始含义
        """
        meaning_row = tk.Frame(parent)
        meaning_row.pack(fill=tk.X, pady=2)

        meaning_var = tk.StringVar(value=meaning)
        meaning_entry = tk.Entry(meaning_row, textvariable=meaning_var, font=self.font_config["normal"])
        meaning_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 删除含义按钮
        delete_meaning_btn = tk.Button(
            meaning_row,
            text="×",
            command=lambda: self._delete_meaning(meaning_row, meaning_entries),
            font=self.font_config["normal"],
            bg="#ff9800",
            fg="white",
            width=2,
            relief=tk.RAISED
        )
        delete_meaning_btn.pack(side=tk.RIGHT, padx=5)

        meaning_entries.append(meaning_var)

    def _delete_tag(self, tag_frame):
        """
        删除词性框架

        Args:
            tag_frame: 要删除的词性框架
        """
        # 确保至少保留一个词性框架
        if len(self.tag_frames) <= 1:
            messagebox.showwarning("提示", "至少需要保留一个词性")
            return

        # 找到并删除框架
        for i, info in enumerate(self.tag_frames):
            if info["frame"] == tag_frame:
                info["frame"].destroy()
                del self.tag_frames[i]
                break

        # 重新排列框架
        self._rearrange_frames()

    def _delete_meaning(self, meaning_row, meaning_entries):
        """
        删除含义输入框

        Args:
            meaning_row: 要删除的含义行框架
            meaning_entries: 含义输入框列表
        """
        # 确保每个词性至少有一个含义
        if len(meaning_entries) <= 1:
            messagebox.showwarning("提示", "每个词性至少需要保留一个含义")
            return

        # 找到并删除含义
        for entry in meaning_entries:
            if entry.get() == meaning_row.children["!entry"].get():
                meaning_entries.remove(entry)
                break

        meaning_row.destroy()

    def _rearrange_frames(self):
        """
        重新排列所有词性框架
        """
        # 先将所有框架隐藏
        for info in self.tag_frames:
            info["frame"].pack_forget()

        # 重新显示所有框架
        for info in self.tag_frames:
            info["frame"].pack(fill=tk.X, pady=5)

        # 确保添加按钮在最后
        self.add_tag_btn.pack(fill=tk.X, pady=5)

    def get_translation(self):
        """
        获取翻译数据，返回JSON格式字符串

        Returns:
            str: JSON格式的翻译数据
        """
        translations = []

        for info in self.tag_frames:
            tag = info["tag_var"].get().strip()
            if not tag:
                tag = ""

            meanings = []
            for entry in info["meaning_entries"]:
                meaning = entry.get().strip()
                if meaning:
                    meanings.append(meaning)

            # 只添加有含义的词性
            if meanings:
                # 使用pos字段作为权威词性来源，保留与旧模块的兼容性
                translations.append({"pos": tag, "meanings": meanings})

        # 如果只有一个词性且没有设置词性，可以返回简单字符串格式
        if len(translations) == 1 and not translations[0]["pos"] and len(translations[0]["meanings"]) == 1:
            return translations[0]["meanings"][0]

        # 否则返回JSON格式
        return json.dumps(translations, ensure_ascii=False, indent=2)

    def set_translation(self, translation):
        """
        设置翻译数据

        Args:
            translation: 翻译数据，可以是字符串或JSON格式
        """
        # 清空现有内容
        for info in self.tag_frames[:]:
            info["frame"].destroy()
        self.tag_frames.clear()

        # 解析翻译数据
        try:
            # 尝试解析为JSON
            if isinstance(translation, str) and translation.startswith('['):
                data = json.loads(translation)

                # 验证数据格式
                if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    for item in data:
                        # 同时支持'pos'和'tag'字段，pos优先，确保与旧模块兼容
                        tag = item.get("pos", item.get("tag", ""))
                        # 同时支持'meanings'和'meaning_zh'键，确保兼容性
                        meanings = item.get("meanings", item.get("meaning_zh", []))
                        self._add_tag(tag, meanings)
                    return
        except json.JSONDecodeError:
            pass

        # 如果解析失败或不是JSON格式，当作简单字符串处理
        if translation and isinstance(translation, str):
            self._add_tag("", [translation])
        else:
            self._add_tag()
