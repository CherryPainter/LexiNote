import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os

from logger import log_info, log_error


class WordSetPage(tk.Frame):
    """词库管理页面"""
    
    def __init__(self, parent, word_manager, font_config):
        """初始化词库管理页面"""
        super().__init__(parent)
        self.parent = parent
        self.word_manager = word_manager
        self.font_config = font_config
        
        # 当前选中的词库ID
        self.current_set_id = None
        
        # 分页相关
        self.current_page = 1
        self.items_per_page = 20
        
        # 创建UI
        self._create_ui()
        
        # 加载数据
        self._load_word_sets()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部操作栏
        top_bar = tk.Frame(main_frame, bg='white')
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        # 导入词库按钮
        import_btn = tk.Button(
            top_bar,
            text="📂 导入词库",
            font=self.font_config['button'],
            command=self._import_word_set,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建词库按钮
        create_btn = tk.Button(
            top_bar,
            text="➕ 创建词库",
            font=self.font_config['button'],
            command=self._create_word_set,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        create_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除词库按钮
        delete_set_btn = tk.Button(
            top_bar,
            text="🗑️ 删除词库",
            font=self.font_config['button'],
            command=self._delete_word_set,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        delete_set_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出词库按钮
        export_btn = tk.Button(
            top_bar,
            text="📤 导出词库",
            font=self.font_config['button'],
            command=self._export_word_set,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_btn = tk.Button(
            top_bar,
            text="🔄 刷新",
            font=self.font_config['button'],
            command=self._refresh,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # 分割线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        # 左侧词库列表
        left_frame = tk.Frame(main_frame, bg='white', width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 词库列表标题
        set_list_label = tk.Label(
            left_frame,
            text="词库列表",
            font=self.font_config['header'],
            bg='white'
        )
        set_list_label.pack(pady=(0, 10))
        
        # 词库列表
        self.set_listbox = tk.Listbox(
            left_frame,
            font=self.font_config['normal'],
            width=25,
            height=20,
            selectmode=tk.SINGLE
        )
        self.set_listbox.pack(fill=tk.BOTH, expand=True)
        self.set_listbox.bind('<<ListboxSelect>>', self._on_word_set_select)
        
        # 滚动条
        set_scrollbar = tk.Scrollbar(self.set_listbox, orient=tk.VERTICAL, command=self.set_listbox.yview)
        set_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.set_listbox.config(yscrollcommand=set_scrollbar.set)
        
        # 右侧单词列表
        right_frame = tk.Frame(main_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 词库信息和搜索栏
        info_search_frame = tk.Frame(right_frame, bg='white')
        info_search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 词库信息标签
        self.set_info_label = tk.Label(
            info_search_frame,
            text="请选择一个词库",
            font=self.font_config['normal'],
            bg='white'
        )
        self.set_info_label.pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = tk.Frame(info_search_frame, bg='white')
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        search_label = tk.Label(search_frame, text="搜索:", font=self.font_config['normal'], bg='white')
        search_label.pack(side=tk.LEFT)
        
        self.search_entry = tk.Entry(search_frame, font=self.font_config['normal'], width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', self._search_words)
        
        search_btn = tk.Button(
            search_frame,
            text="🔍",
            font=self.font_config['normal'],
            command=self._search_words,
            width=3
        )
        search_btn.pack(side=tk.LEFT)
        
        # 单词操作按钮
        word_actions_frame = tk.Frame(right_frame, bg='white')
        word_actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        add_word_btn = tk.Button(
            word_actions_frame,
            text="➕ 添加单词",
            font=self.font_config['button'],
            command=self._add_word,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        add_word_btn.pack(side=tk.LEFT, padx=5)
        
        edit_word_btn = tk.Button(
            word_actions_frame,
            text="✏️ 编辑单词",
            font=self.font_config['button'],
            command=self._edit_word,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        edit_word_btn.pack(side=tk.LEFT, padx=5)
        
        delete_word_btn = tk.Button(
            word_actions_frame,
            text="🗑️ 删除单词",
            font=self.font_config['button'],
            command=self._delete_word,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        delete_word_btn.pack(side=tk.LEFT, padx=5)
        
        # AI补全按钮
        ai_complete_btn = tk.Button(
            word_actions_frame,
            text="🤖 AI补全",
            font=self.font_config['button'],
            command=self._ai_complete_words,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        ai_complete_btn.pack(side=tk.LEFT, padx=5)
        
        # 单词列表表格
        columns = ("id", "word", "translation", "phonetic", "tag")
        self.word_tree = ttk.Treeview(right_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.word_tree.heading("id", text="ID")
        self.word_tree.heading("word", text="单词")
        self.word_tree.heading("translation", text="翻译")
        self.word_tree.heading("phonetic", text="音标")
        self.word_tree.heading("tag", text="词性")
        
        # 设置列宽
        self.word_tree.column("id", width=50, anchor=tk.CENTER)
        self.word_tree.column("word", width=100, anchor=tk.W)
        self.word_tree.column("translation", width=150, anchor=tk.W)
        self.word_tree.column("phonetic", width=100, anchor=tk.W)
        self.word_tree.column("tag", width=80, anchor=tk.CENTER)
        
        # 绑定双击事件显示例句
        self.word_tree.bind('<Double-1>', self._show_word_details)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.word_tree.yview)
        self.word_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.word_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 分页控制
        pagination_frame = tk.Frame(right_frame, bg='white')
        pagination_frame.pack(fill=tk.X, pady=10)
        
        self.prev_btn = tk.Button(
            pagination_frame,
            text="上一页",
            font=self.font_config['button'],
            command=self._prev_page,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.page_label = tk.Label(
            pagination_frame,
            text="第 1 页",
            font=self.font_config['normal'],
            bg='white'
        )
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(
            pagination_frame,
            text="下一页",
            font=self.font_config['button'],
            command=self._next_page,
            bg='#e0e0e0',
            relief=tk.RAISED
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
    
    def _load_word_sets(self):
        """加载词库列表"""
        try:
            self.set_listbox.delete(0, tk.END)
            word_sets = self.word_manager.get_all_word_sets()
            
            # 存储词库ID到索引的映射
            self.word_set_map = {}
            
            # 获取当前激活的词库
            active_set = self.word_manager.get_active_word_set()
            active_set_id = active_set['id'] if active_set else None
            
            # 添加词库到列表
            for i, word_set in enumerate(word_sets):
                prefix = "✅ " if word_set['id'] == active_set_id else "   "
                display_text = f"{prefix}{word_set['name']} ({word_set['word_count']}个单词)"
                self.set_listbox.insert(tk.END, display_text)
                self.word_set_map[i] = word_set['id']
                
                # 自动选中当前激活的词库
                if word_set['id'] == active_set_id:
                    self.set_listbox.selection_set(i)
                    self.current_set_id = word_set['id']
                    self._update_set_info(word_set)
                    self._load_words()
        except Exception as e:
            log_error(f"加载词库列表失败: {str(e)}")
            messagebox.showerror("错误", f"加载词库列表失败: {str(e)}")
    
    def _on_word_set_select(self, event):
        """选择词库时的处理"""
        selection = self.set_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        set_id = self.word_set_map.get(index)
        
        if set_id:
            self.current_set_id = set_id
            # 更新词库信息
            word_set = self.word_manager.get_word_set_by_id(set_id)
            if word_set:
                self._update_set_info(word_set)
                self._load_words()
                
                # 询问是否切换到该词库
                if messagebox.askyesno(
                    "切换词库", 
                    f"是否将 '{word_set['name']}' 设为当前学习词库？"
                ):
                    success, msg = self.word_manager.set_active_word_set(set_id)
                    if success:
                        messagebox.showinfo("成功", msg)
                        self._load_word_sets()  # 重新加载以显示选中状态
                    else:
                        messagebox.showerror("错误", msg)
    
    def _update_set_info(self, word_set):
        """更新词库信息显示"""
        info_text = f"{word_set['name']} - {word_set.get('description', '无描述')}"
        if word_set.get('create_time'):
            info_text += f" (创建于: {word_set['create_time']})"
        self.set_info_label.config(text=info_text)
    
    def _load_words(self, keyword=None):
        """加载单词列表"""
        if not self.current_set_id:
            return
        
        try:
            # 清空现有数据
            for item in self.word_tree.get_children():
                self.word_tree.delete(item)
            
            # 计算偏移量
            offset = (self.current_page - 1) * self.items_per_page
            
            # 加载单词
            words = self.word_manager.get_words_by_set_id(
                self.current_set_id, 
                keyword=keyword,
                limit=self.items_per_page + 1,  # 多加载一个用于判断是否有下一页
                offset=offset
            )
            
            # 判断是否有下一页
            has_next = len(words) > self.items_per_page
            if has_next:
                words = words[:self.items_per_page]
            
            # 更新分页按钮状态
            self.prev_btn.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if has_next else tk.DISABLED)
            
            # 更新页码标签
            word_set = self.word_manager.get_word_set_by_id(self.current_set_id)
            total_words = word_set.get('word_count', 0) if word_set else 0
            total_pages = (total_words + self.items_per_page - 1) // self.items_per_page
            self.page_label.config(text=f"第 {self.current_page} / {total_pages} 页")
            
            # 添加单词到表格
            for word in words:
                self.word_tree.insert("", tk.END, values=(
                    word['id'],
                    word['word'],
                    word['translation'],
                    word.get('phonetic', ''),
                    word.get('tag', '')
                ))
        except Exception as e:
            log_error(f"加载单词列表失败: {str(e)}")
            messagebox.showerror("错误", f"加载单词列表失败: {str(e)}")
    
    def _search_words(self, event=None):
        """搜索单词"""
        keyword = self.search_entry.get().strip()
        self.current_page = 1  # 搜索时重置到第一页
        self._load_words(keyword=keyword)
    
    def _prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            keyword = self.search_entry.get().strip() or None
            self._load_words(keyword=keyword)
    
    def _next_page(self):
        """下一页"""
        self.current_page += 1
        keyword = self.search_entry.get().strip() or None
        self._load_words(keyword=keyword)
    
    def _import_word_set(self):
        """导入词库"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择词库文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                return
            
            # 导入词库
            success, msg = self.word_manager.import_word_set_from_json(file_path)
            
            if success:
                messagebox.showinfo("成功", msg)
                self._load_word_sets()
            elif msg == "overwrite":
                # 询问是否覆盖
                if messagebox.askyesno(
                    "确认覆盖", 
                    "同名词库已存在，是否覆盖？"
                ):
                    # 先删除旧词库
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    set_name = data.get('name', os.path.splitext(os.path.basename(file_path))[0])
                    
                    # 获取旧词库ID
                    old_set = self.word_manager.db_manager.get_word_set_by_name(set_name)
                    if old_set:
                        # 确保不是当前激活的词库或默认词库
                        if old_set['id'] == self.word_manager.active_word_set_id:
                            messagebox.showerror("错误", "不能覆盖当前激活的词库")
                            return
                        if old_set['name'] == '默认词库':
                            messagebox.showerror("错误", "不能覆盖默认词库")
                            return
                        
                        # 删除旧词库
                        self.word_manager.db_manager.delete_word_set(old_set['id'])
                        
                        # 重新导入
                        success, msg = self.word_manager.import_word_set_from_json(file_path)
                        if success:
                            messagebox.showinfo("成功", msg)
                            self._load_word_sets()
                        else:
                            messagebox.showerror("错误", msg)
            else:
                messagebox.showerror("错误", msg)
        except Exception as e:
            log_error(f"导入词库失败: {str(e)}")
            messagebox.showerror("错误", f"导入词库失败: {str(e)}")
    
    def _export_word_set(self):
        """导出词库"""
        if not self.current_set_id:
            messagebox.showwarning("提示", "请先选择一个词库")
            return
        
        try:
            # 获取词库信息
            word_set = self.word_manager.get_word_set_by_id(self.current_set_id)
            if not word_set:
                messagebox.showerror("错误", "词库不存在")
                return
            
            # 选择导出路径
            default_filename = f"{word_set['name']}.json"
            file_path = filedialog.asksaveasfilename(
                title="导出词库",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json")],
                initialfile=default_filename
            )
            
            if not file_path:
                return
            
            # 导出词库
            success, msg = self.word_manager.export_word_set_to_json(self.current_set_id, file_path)
            if success:
                messagebox.showinfo("成功", msg)
            else:
                messagebox.showerror("错误", msg)
        except Exception as e:
            log_error(f"导出词库失败: {str(e)}")
            messagebox.showerror("错误", f"导出词库失败: {str(e)}")
    
    def _create_word_set(self):
        """创建新词库"""
        from tkinter import simpledialog
        
        try:
            name = simpledialog.askstring("创建词库", "请输入词库名称:")
            if not name or not name.strip():
                return
            
            description = simpledialog.askstring("创建词库", "请输入词库描述:", initialvalue="")
            
            success, msg = self.word_manager.create_word_set(name.strip(), description or "")
            if success:
                messagebox.showinfo("成功", msg)
                self._load_word_sets()
            else:
                messagebox.showerror("错误", msg)
        except Exception as e:
            log_error(f"创建词库失败: {str(e)}")
            messagebox.showerror("错误", f"创建词库失败: {str(e)}")
    
    def _delete_word_set(self):
        """删除词库"""
        if not self.current_set_id:
            messagebox.showwarning("提示", "请先选择一个词库")
            return
        
        try:
            word_set = self.word_manager.get_word_set_by_id(self.current_set_id)
            if not word_set:
                return
            
            # 二次确认
            if messagebox.askyesno(
                "确认删除", 
                f"确定要删除词库 '{word_set['name']}' 吗？此操作不可恢复！"
            ):
                success, msg = self.word_manager.delete_word_set(self.current_set_id)
                if success:
                    messagebox.showinfo("成功", msg)
                    self.current_set_id = None
                    self.set_info_label.config(text="请选择一个词库")
                    # 清空单词列表
                    for item in self.word_tree.get_children():
                        self.word_tree.delete(item)
                    self._load_word_sets()
                else:
                    messagebox.showerror("错误", msg)
        except Exception as e:
            log_error(f"删除词库失败: {str(e)}")
            messagebox.showerror("错误", f"删除词库失败: {str(e)}")
    
    def _add_word(self):
        """添加单词"""
        if not self.current_set_id:
            messagebox.showwarning("提示", "请先选择一个词库")
            return
        
        # 创建单词编辑对话框
        self._show_word_edit_dialog()
    
    def _edit_word(self):
        """编辑单词"""
        selection = self.word_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个单词")
            return
        
        # 获取单词ID
        item = selection[0]
        word_id = self.word_tree.item(item, "values")[0]
        
        # 创建单词编辑对话框
        self._show_word_edit_dialog(word_id)
    
    def _delete_word(self):
        """删除单词"""
        selection = self.word_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个单词")
            return
        
        # 获取单词信息
        item = selection[0]
        values = self.word_tree.item(item, "values")
        word_id = values[0]
        word_name = values[1]
        
        # 二次确认
        if messagebox.askyesno(
            "确认删除", 
            f"确定要删除单词 '{word_name}' 吗？"
        ):
            success, msg = self.word_manager.delete_word(word_id)
            if success:
                messagebox.showinfo("成功", msg)
                # 重新加载单词列表
                keyword = self.search_entry.get().strip() or None
                self._load_words(keyword=keyword)
                # 重新加载词库列表以更新单词计数
                self._load_word_sets()
            else:
                messagebox.showerror("错误", msg)
    
    def _ai_complete_words(self):
        """使用AI补全单词的详细属性"""
        if not self.current_set_id:
            messagebox.showwarning("警告", "请先选择一个词库")
            return
            
        # 创建进度对话框
        progress_window = tk.Toplevel(self)
        progress_window.title("AI补全进度")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self)
        progress_window.grab_set()
        
        # 设置居中位置
        x = self.winfo_x() + self.winfo_width() // 2 - 200
        y = self.winfo_y() + self.winfo_height() // 2 - 75
        progress_window.geometry(f"400x150+{x}+{y}")
        
        # 进度标签
        progress_label = tk.Label(
            progress_window,
            text="正在准备AI补全...",
            font=self.font_config['normal']
        )
        progress_label.pack(pady=20)
        
        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window,
            variable=progress_var,
            length=300,
            mode='determinate'
        )
        progress_bar.pack(pady=10)
        
        # 关闭按钮（初始禁用）
        close_btn = tk.Button(
            progress_window,
            text="关闭",
            command=progress_window.destroy,
            state=tk.DISABLED
        )
        close_btn.pack(pady=10)
        
        # 定义进度回调函数
        def update_progress(current, total, word):
            progress = (current / total) * 100
            progress_var.set(progress)
            progress_label.config(text=f"正在补全单词 {current}/{total}: {word}")
            progress_window.update_idletasks()
        
        # 定义补全完成后的回调函数
        def on_completion(completed_count, total_count):
            if completed_count > 0:
                progress_label.config(text=f"AI补全完成！成功补全 {completed_count}/{total_count} 个单词")
            else:
                progress_label.config(text="没有需要补全的单词或补全失败")
            
            progress_var.set(100)
            close_btn.config(state=tk.NORMAL)
            
            # 重新加载单词列表以显示更新后的信息
            keyword = self.search_entry.get().strip() or None
            self._load_words(keyword=keyword)
        
        # 在后台线程中执行AI补全操作
        def ai_complete_task():
            try:
                completed_count = self.word_manager.ai_complete_word_details(callback=update_progress)
                self.after(0, lambda: on_completion(completed_count, len(self.word_manager.get_words_missing_details(10))))
            except Exception as e:
                log_error(f"AI补全单词失败: {str(e)}")
                self.after(0, lambda: messagebox.showerror("错误", f"AI补全单词失败: {str(e)}"))
                self.after(0, progress_window.destroy)
        
        # 启动后台线程
        import threading
        thread = threading.Thread(target=ai_complete_task)
        thread.daemon = True
        thread.start()
    
    def _show_word_edit_dialog(self, word_id=None):
        """显示单词编辑对话框"""
        # 创建对话框
        dialog = tk.Toplevel(self)
        dialog.title("编辑单词" if word_id else "添加单词")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # 获取单词信息（如果是编辑）
        word_data = {}
        if word_id:
            word = self.word_manager.db_manager.get_word_by_id(word_id)
            if word:
                word_data = word
        
        # 创建表单
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 单词
        tk.Label(form_frame, text="单词:", font=self.font_config['normal']).grid(row=0, column=0, sticky=tk.W, pady=5)
        word_var = tk.StringVar(value=word_data.get('word', ''))
        word_entry = tk.Entry(form_frame, textvariable=word_var, font=self.font_config['normal'], width=30)
        word_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 翻译
        tk.Label(form_frame, text="翻译:", font=self.font_config['normal']).grid(row=1, column=0, sticky=tk.W, pady=5)
        translation_var = tk.StringVar(value=word_data.get('translation', ''))
        translation_entry = tk.Entry(form_frame, textvariable=translation_var, font=self.font_config['normal'], width=30)
        translation_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 音标
        tk.Label(form_frame, text="音标:", font=self.font_config['normal']).grid(row=2, column=0, sticky=tk.W, pady=5)
        phonetic_var = tk.StringVar(value=word_data.get('phonetic', ''))
        phonetic_entry = tk.Entry(form_frame, textvariable=phonetic_var, font=self.font_config['normal'], width=30)
        phonetic_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 词性
        tk.Label(form_frame, text="词性:", font=self.font_config['normal']).grid(row=3, column=0, sticky=tk.W, pady=5)
        tag_var = tk.StringVar(value=word_data.get('tag', ''))
        tag_entry = tk.Entry(form_frame, textvariable=tag_var, font=self.font_config['normal'], width=30)
        tag_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 英文释义
        tk.Label(form_frame, text="英文释义:", font=self.font_config['normal']).grid(row=4, column=0, sticky=tk.NW, pady=5)
        meaning_en_var = tk.Text(form_frame, font=self.font_config['normal'], width=30, height=3)
        meaning_en_var.grid(row=4, column=1, sticky=tk.W, pady=5)
        if word_data.get('meaning_en'):
            meaning_en_var.insert(tk.END, word_data['meaning_en'])
        
        # 例句
        tk.Label(form_frame, text="例句:", font=self.font_config['normal']).grid(row=5, column=0, sticky=tk.NW, pady=5)
        example_var = tk.Text(form_frame, font=self.font_config['normal'], width=30, height=3)
        example_var.grid(row=5, column=1, sticky=tk.W, pady=5)
        if word_data.get('example'):
            example_var.insert(tk.END, word_data['example'])
        
        # 例句翻译
        tk.Label(form_frame, text="例句翻译:", font=self.font_config['normal']).grid(row=6, column=0, sticky=tk.NW, pady=5)
        example_translation_var = tk.Text(form_frame, font=self.font_config['normal'], width=30, height=3)
        example_translation_var.grid(row=6, column=1, sticky=tk.W, pady=5)
        if word_data.get('example_translation'):
            example_translation_var.insert(tk.END, word_data['example_translation'])
        
        # 按钮框架
        btn_frame = tk.Frame(dialog, pady=10)
        btn_frame.pack(fill=tk.X)
        
        def save_word():
            word = word_var.get().strip()
            translation = translation_var.get().strip()
            
            if not word or not translation:
                messagebox.showwarning("提示", "单词和翻译不能为空")
                return
            
            try:
                if word_id:
                    # 更新单词
                    success, msg = self.word_manager.update_word(
                        word_id,
                        word=word,
                        translation=translation,
                        phonetic=phonetic_var.get().strip(),
                        tag=tag_var.get().strip(),
                        meaning_en=meaning_en_var.get(1.0, tk.END).strip(),
                        example=example_var.get(1.0, tk.END).strip(),
                        example_translation=example_translation_var.get(1.0, tk.END).strip()
                    )
                else:
                    # 添加单词
                    success, msg = self.word_manager.db_manager.add_word_to_set(
                        self.current_set_id,
                        word=word,
                        translation=translation,
                        phonetic=phonetic_var.get().strip(),
                        meaning_en=meaning_en_var.get(1.0, tk.END).strip(),
                        example=example_var.get(1.0, tk.END).strip(),
                        example_translation=example_translation_var.get(1.0, tk.END).strip(),
                        tag=tag_var.get().strip()
                    )
                
                if success:
                    dialog.destroy()
                    # 重新加载单词列表
                    keyword = self.search_entry.get().strip() or None
                    self._load_words(keyword=keyword)
                    # 重新加载词库列表以更新单词计数
                    self._load_word_sets()
                else:
                    messagebox.showerror("错误", msg)
            except Exception as e:
                messagebox.showerror("错误", f"保存单词失败: {str(e)}")
        
        save_btn = tk.Button(
            btn_frame,
            text="保存",
            font=self.font_config['button'],
            command=save_word,
            width=10
        )
        save_btn.pack(side=tk.LEFT, padx=20)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="取消",
            font=self.font_config['button'],
            command=dialog.destroy,
            width=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def _show_word_details(self, event):
        """显示单词详细信息（双击事件）"""
        selection = self.word_tree.selection()
        if not selection:
            return
        
        # 获取单词ID
        item = selection[0]
        word_id = self.word_tree.item(item, "values")[0]
        
        # 获取单词详情
        word = self.word_manager.db_manager.get_word_by_id(word_id)
        if not word:
            return
        
        # 创建详情对话框
        dialog = tk.Toplevel(self)
        dialog.title(f"单词详情: {word['word']}")
        dialog.geometry("500x400")
        dialog.transient(self)
        
        # 详情内容
        detail_frame = tk.Frame(dialog, padx=20, pady=20)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        
        # 单词和音标
        word_frame = tk.Frame(detail_frame)
        word_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(word_frame, text=word['word'], font=(self.font_config['header'][0], 20, 'bold')).pack(side=tk.LEFT)
        if word.get('phonetic'):
            tk.Label(word_frame, text=word['phonetic'], font=self.font_config['normal'], fg='#666').pack(side=tk.LEFT, padx=10)
        if word.get('tag'):
            tk.Label(word_frame, text=word['tag'], font=self.font_config['normal'], fg='#999').pack(side=tk.LEFT, padx=10)
        
        # 翻译
        tk.Label(detail_frame, text="中文释义:", font=self.font_config['normal'], fg='#333').pack(anchor=tk.W, pady=5)
        tk.Label(detail_frame, text=word['translation'], font=self.font_config['normal']).pack(anchor=tk.W, pady=5)
        
        # 英文释义
        if word.get('meaning_en'):
            tk.Label(detail_frame, text="英文释义:", font=self.font_config['normal'], fg='#333').pack(anchor=tk.W, pady=5)
            tk.Label(detail_frame, text=word['meaning_en'], font=self.font_config['normal']).pack(anchor=tk.W, pady=5)
        
        # 例句
        if word.get('example'):
            tk.Label(detail_frame, text="例句:", font=self.font_config['normal'], fg='#333').pack(anchor=tk.W, pady=5)
            example_text = tk.Text(detail_frame, font=self.font_config['normal'], wrap=tk.WORD, height=3, width=50)
            example_text.pack(fill=tk.X, pady=5)
            example_text.insert(tk.END, word['example'])
            example_text.config(state=tk.DISABLED)
        
        # 熟悉度
        familiarity = word.get('familiarity', 0)
        tk.Label(detail_frame, text=f"熟悉度: {familiarity}/5", font=self.font_config['normal'], fg='#333').pack(anchor=tk.W, pady=10)
        
        # 关闭按钮
        tk.Button(
            detail_frame,
            text="关闭",
            font=self.font_config['button'],
            command=dialog.destroy,
            width=10
        ).pack(side=tk.BOTTOM, pady=20)
    
    def _refresh(self):
        """刷新数据"""
        self._load_word_sets()
        # 如果有选中的词库，重新加载单词
        if self.current_set_id:
            keyword = self.search_entry.get().strip() or None
            self._load_words(keyword=keyword)