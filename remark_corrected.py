# -*- coding: utf-8 -*-
# Filename: remark.py

__author__ = 'Piratf'

import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import sqlite3
import datetime

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

defEncoding = sys.getfilesystemencoding()

def sys_encode(content):
    return content.encode(defEncoding).decode(defEncoding)

def run_command(command):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.call(command, startupinfo=startupinfo, shell=True)

def get_setting_file_path(fpath):
    return fpath + os.sep + 'desktop.ini'

def update_folder_comment(fpath, comment, image_path=""):
    """更新文件夹备注（desktop.ini）"""
    setting_file_path = get_setting_file_path(fpath)
    if os.path.exists(setting_file_path):
        run_command('attrib "' + setting_file_path + '" -s -h')
    with open(setting_file_path, 'w', encoding='utf-16') as f:
        f.write('[.ShellClassInfo]\n')
        f.write('InfoTip=' + comment + '\n')
        if image_path:
            f.write('IconResource=' + image_path + ',0\n')
    run_command('attrib "' + setting_file_path + '" +s +h')
    run_command('attrib "' + fpath + '" +s ')
    return True

def read_folder_comment(fpath):
    """读取文件夹备注"""
    setting_file_path = get_setting_file_path(fpath)
    if not os.path.exists(setting_file_path):
        return None, None
    run_command('attrib "' + setting_file_path + '" -s -h')
    try:
        with open(setting_file_path, 'r', encoding='utf-16') as f:
            content = f.read()
            comment = None
            image_path = None
            for line in content.splitlines():
                if line.startswith('InfoTip='):
                    comment = line[8:].strip()
                elif line.startswith('IconResource='):
                    icon_line = line[12:].strip()
                    if ',' in icon_line:
                        image_path = icon_line.split(',')[0].strip()
            return comment, image_path
    except Exception:
        return None, None
    finally:
        run_command('attrib "' + setting_file_path + '" +s +h')

def delete_folder_comment(fpath):
    """删除文件夹备注（删除 desktop.ini 或清空 InfoTip）"""
    setting_file_path = get_setting_file_path(fpath)
    if os.path.exists(setting_file_path):
        run_command('attrib "' + setting_file_path + '" -s -h')
        try:
            # 尝试只删除 InfoTip 行，保留其他可能配置
            with open(setting_file_path, 'r', encoding='utf-16') as f:
                lines = f.readlines()
            with open(setting_file_path, 'w', encoding='utf-16') as f:
                for line in lines:
                    if not line.startswith('InfoTip='):
                        f.write(line)
            # 如果文件变空或只剩 [.ShellClassInfo]，删除该文件
            with open(setting_file_path, 'r', encoding='utf-16') as f:
                if f.read().strip() in ('', '[.ShellClassInfo]'):
                    os.remove(setting_file_path)
        except:
            os.remove(setting_file_path)
        run_command('attrib "' + fpath + '"-s')  # 可选取消系统属性
        return True
    return False

# ---------- 文件备注数据库操作 ----------
DB_PATH = os.path.join(os.path.expanduser("~"), ".folder_remark_manager.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS file_remarks
                 (path TEXT PRIMARY KEY,
                  comment TEXT,
                  image_path TEXT,
                  modify_time TEXT)''')
    conn.commit()
    conn.close()

def add_file_remark(file_path, comment, image_path=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO file_remarks (path, comment, image_path, modify_time) VALUES (?,?,?,?)",
              (file_path, comment, image_path, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_file_remark(file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT comment, image_path FROM file_remarks WHERE path=?", (file_path,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None

def delete_file_remark(file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM file_remarks WHERE path=?", (file_path,))
    conn.commit()
    conn.close()

def get_all_file_remarks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT path, comment, image_path FROM file_remarks")
    rows = c.fetchall()
    conn.close()
    return rows

# ---------- GUI 程序 ----------
class RemarkApp:
    def __init__(self, master):
        self.master = master
        master.title("文件夹/文件备注管理器")
        master.geometry("950x750")
        
        init_db()  # 初始化数据库
        
        self.search_thread = None
        self.stop_search = False
        self.pre_scan_enabled = False
        
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_add = ttk.Frame(self.notebook)
        self.tab_search = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_add, text="添加备注")
        self.notebook.add(self.tab_search, text="搜索/管理备注")
        
        self.create_add_tab()
        self.create_search_tab()
    
    def create_add_tab(self):
        frame = self.tab_add
        frame.grid_columnconfigure(1, weight=1)
        
        # 类型选择：文件夹或文件
        ttk.Label(frame, text="类型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar(value="folder")
        ttk.Radiobutton(frame, text="文件夹", variable=self.type_var, value="folder",
                        command=self.on_type_change).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(frame, text="文件", variable=self.type_var, value="file",
                        command=self.on_type_change).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(frame, text="路径:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.path_entry = ttk.Entry(frame, width=60)
        self.path_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_btn = ttk.Button(frame, text="浏览", command=self.browse_path)
        self.browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(frame, text="备注内容:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.comment_text = scrolledtext.ScrolledText(frame, width=60, height=6)
        self.comment_text.grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(frame, text="图片路径:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.image_path_entry = ttk.Entry(frame, width=50)
        self.image_path_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(frame, text="选择图片", command=self.browse_image).grid(row=3, column=2, padx=5, pady=5)
        
        self.image_preview_canvas = tk.Canvas(frame, bg='white', width=200, height=150)
        self.image_preview_canvas.grid(row=4, column=1, padx=5, pady=5)
        self.image_preview_canvas.create_text(100, 75, text="图片预览", fill='gray')
        
        ttk.Button(frame, text="添加备注", command=self.add_remark).grid(row=5, column=1, pady=10)
        self.status_label = ttk.Label(frame, text="")
        self.status_label.grid(row=6, column=1, pady=5)
    
    def on_type_change(self):
        """切换类型时修改浏览按钮行为"""
        if self.type_var.get() == "folder":
            self.browse_btn.config(text="浏览文件夹")
        else:
            self.browse_btn.config(text="浏览文件")
    
    def browse_path(self):
        if self.type_var.get() == "folder":
            folder = filedialog.askdirectory()
            if folder:
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, folder)
        else:
            file_path = filedialog.askopenfilename(
                filetypes=[("所有文件", "*.*"), ("文本文件", "*.txt"), ("Word文档", "*.doc;*.docx")])
            if file_path:
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, file_path)
    
    def browse_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            self.image_path_entry.delete(0, tk.END)
            self.image_path_entry.insert(0, file_path)
            self.update_image_preview(file_path)
    
    def update_image_preview(self, file_path, canvas=None, max_width=200, max_height=150):
        target_canvas = canvas if canvas else self.image_preview_canvas
        target_canvas.delete("all")
        if not PIL_AVAILABLE:
            target_canvas.create_text(max_width/2, max_height/2, 
                                    text="需要安装PIL库\n(pip install pillow)", fill='red')
            return
        try:
            image = Image.open(file_path)
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            target_canvas.image = photo
            target_canvas.create_image(max_width/2, max_height/2, image=photo)
        except Exception as e:
            target_canvas.create_text(max_width/2, max_height/2, 
                                    text="无法加载图片\n" + str(e), fill='red')
    
    def add_remark(self):
        path = self.path_entry.get().strip()
        comment = self.comment_text.get("1.0", tk.END).strip()
        image_path = self.image_path_entry.get().strip()
        if not path:
            messagebox.showwarning("警告", "请输入路径")
            return
        if not comment:
            messagebox.showwarning("警告", "备注内容不能为空")
            return
        if image_path and not os.path.isfile(image_path):
            messagebox.showwarning("警告", "图片路径无效")
            return
        
        if self.type_var.get() == "folder":
            if not os.path.isdir(path):
                messagebox.showwarning("警告", "文件夹路径无效")
                return
            if update_folder_comment(path, comment, image_path):
                messagebox.showinfo("成功", "文件夹备注添加成功！\n可能需要刷新资源管理器才能看到")
                self.clear_add_form()
        else:  # file
            if not os.path.isfile(path):
                messagebox.showwarning("警告", "文件路径无效")
                return
            add_file_remark(path, comment, image_path)
            messagebox.showinfo("成功", "文件备注已保存到数据库")
            self.clear_add_form()
    
    def clear_add_form(self):
        self.path_entry.delete(0, tk.END)
        self.comment_text.delete("1.0", tk.END)
        self.image_path_entry.delete(0, tk.END)
        self.image_preview_canvas.delete("all")
        self.image_preview_canvas.create_text(100, 75, text="图片预览", fill='gray')
    
    # ---------- 搜索/管理选项卡 ----------
    def create_search_tab(self):
        frame = self.tab_search
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        
        ttk.Label(frame, text="搜索目录:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_path_entry = ttk.Entry(frame, width=60)
        self.search_path_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.search_path_entry.insert(0, os.path.expanduser("~"))
        self.search_path_entry.bind('<FocusOut>', self.on_path_lost_focus)
        ttk.Button(frame, text="浏览", command=self.browse_search_folder).grid(row=0, column=2, padx=5, pady=5)
        
        self.pre_scan_var = tk.BooleanVar()
        self.pre_scan_check = ttk.Checkbutton(frame, text="开启预扫描", variable=self.pre_scan_var,
                                              command=self.toggle_pre_scan)
        self.pre_scan_check.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(frame, text="搜索关键词:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.keyword_entry = ttk.Entry(frame, width=40)
        self.keyword_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.search_btn = ttk.Button(frame, text="搜索", command=self.perform_search)
        self.search_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # 结果表格 Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=2, column=0, columnspan=4, sticky=tk.NSEW, padx=5, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        columns = ("type", "path", "comment", "image")
        self.result_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.result_tree.heading("type", text="类型")
        self.result_tree.heading("path", text="路径")
        self.result_tree.heading("comment", text="备注")
        self.result_tree.heading("image", text="图片路径")
        self.result_tree.column("type", width=60)
        self.result_tree.column("path", width=400)
        self.result_tree.column("comment", width=300)
        self.result_tree.column("image", width=150)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=vsb.set)
        self.result_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        
        # 图片预览区
        self.image_canvas = tk.Canvas(frame, bg='white', width=300, height=200)
        self.image_canvas.grid(row=3, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
        self.image_canvas.create_text(150, 100, text="图片预览区域\n点击结果项查看图片", fill='gray')
        
        # 管理按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="删除备注", command=self.delete_selected_remark).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑备注", command=self.edit_selected_remark).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存结果列表", command=self.save_results).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_frame = ttk.Frame(frame)
        self.progress_frame.grid(row=5, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=5)
        self.progress_label = ttk.Label(self.progress_frame, text="就绪")
        self.progress_label.pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        
        # 绑定选择事件显示图片
        self.result_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
    
    def browse_search_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.search_path_entry.delete(0, tk.END)
            self.search_path_entry.insert(0, folder)
            if self.pre_scan_enabled:
                self.perform_search()
    
    def toggle_pre_scan(self):
        self.pre_scan_enabled = self.pre_scan_var.get()
        if self.pre_scan_enabled:
            path = self.search_path_entry.get().strip()
            if path and os.path.isdir(path):
                self.perform_search()
    
    def on_path_lost_focus(self, event):
        if self.pre_scan_enabled:
            path = self.search_path_entry.get().strip()
            if path and os.path.isdir(path):
                self.perform_search()
    
    def perform_search(self):
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            self.search_btn.config(text="搜索")
            self.progress_bar.stop()
            self.progress_label.config(text="已停止")
            return
        
        root_path = self.search_path_entry.get().strip()
        keyword = self.keyword_entry.get().strip()
        if not root_path or not os.path.isdir(root_path):
            messagebox.showwarning("警告", "请输入有效的搜索目录")
            return
        
        # 清空表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.stop_search = False
        self.search_btn.config(text="停止")
        self.progress_bar.start()
        self.progress_label.config(text="正在搜索...")
        
        self.search_thread = threading.Thread(
            target=self.search_worker,
            args=(root_path, keyword),
            daemon=True
        )
        self.search_thread.start()
    
    def search_worker(self, root_path, keyword):
        results = []  # (type, path, comment, image_path)
        folder_count = 0
        found_count = 0
        
        # 1. 扫描文件夹（通过 desktop.ini）
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                if self.stop_search:
                    break
                for dirname in dirnames:
                    if self.stop_search:
                        break
                    folder_path = os.path.join(dirpath, dirname)
                    folder_count += 1
                    if folder_count % 100 == 0:
                        self.master.after(0, self.update_progress,
                            f"已扫描 {folder_count} 个文件夹，找到 {found_count} 条备注...")
                    comment, img = read_folder_comment(folder_path)
                    if comment:
                        found_count += 1
                        if not keyword or (keyword.lower() in folder_path.lower() or keyword.lower() in comment.lower()):
                            results.append(("文件夹", folder_path, comment, img if img else ""))
        except Exception as e:
            self.master.after(0, self.show_error, str(e))
        
        # 2. 从数据库读取文件备注（不依赖目录树，直接查询所有）
        if not self.stop_search:
            file_remarks = get_all_file_remarks()
            for file_path, comment, img in file_remarks:
                if self.stop_search:
                    break
                if os.path.exists(file_path) and file_path.startswith(root_path):
                    if not keyword or (keyword.lower() in file_path.lower() or keyword.lower() in comment.lower()):
                        results.append(("文件", file_path, comment, img if img else ""))
                        found_count += 1
        
        self.master.after(0, self.search_complete, results, folder_count, found_count)
    
    def update_progress(self, message):
        self.progress_label.config(text=message)
    
    def show_error(self, message):
        messagebox.showerror("错误", message)
    
    def search_complete(self, results, folder_count, found_count):
        self.progress_bar.stop()
        self.search_btn.config(text="搜索")
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        for typ, path, comment, img in results:
            self.result_tree.insert("", tk.END, values=(typ, path, comment, img))
        self.progress_label.config(text=f"搜索完成：扫描 {folder_count} 个文件夹，数据库匹配 {len(results)} 条")
    
    def on_tree_select(self, event):
        """选中结果时预览图片"""
        selection = self.result_tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self.result_tree.item(item, "values")
        if len(values) >= 4:
            img_path = values[3]
            if img_path and os.path.isfile(img_path):
                self.update_image_preview(img_path, self.image_canvas, 300, 200)
            else:
                self.image_canvas.delete("all")
                self.image_canvas.create_text(150, 100, text="无图片或图片文件已丢失", fill='gray')
    
    def delete_selected_remark(self):
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选中一条记录")
            return
        item = selection[0]
        typ, path, comment, img = self.result_tree.item(item, "values")
        if not messagebox.askyesno("确认删除", f"确定要删除 {typ} 的备注吗？\n{path}"):
            return
        if typ == "文件夹":
            if delete_folder_comment(path):
                messagebox.showinfo("成功", "文件夹备注已删除")
            else:
                messagebox.showerror("错误", "删除失败，请检查权限")
        else:  # 文件
            delete_file_remark(path)
            messagebox.showinfo("成功", "文件备注已删除")
        # 刷新当前搜索结果（重新搜索）
        self.perform_search()
    
    def edit_selected_remark(self):
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选中一条记录")
            return
        item = selection[0]
        typ, path, old_comment, old_img = self.result_tree.item(item, "values")
        # 弹出编辑对话框
        dialog = tk.Toplevel(self.master)
        dialog.title("编辑备注")
        dialog.geometry("500x400")
        dialog.transient(self.master)
        dialog.grab_set()
        
        ttk.Label(dialog, text="路径:").pack(pady=5)
        ttk.Label(dialog, text=path, wraplength=450).pack()
        ttk.Label(dialog, text="备注内容:").pack(pady=5)
        text_edit = scrolledtext.ScrolledText(dialog, width=60, height=6)
        text_edit.insert("1.0", old_comment)
        text_edit.pack(pady=5)
        ttk.Label(dialog, text="图片路径:").pack(pady=5)
        img_entry = ttk.Entry(dialog, width=50)
        img_entry.insert(0, old_img if old_img else "")
        img_entry.pack(pady=5)
        
        def browse_edit_image():
            f = filedialog.askopenfilename(filetypes=[("图片", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
            if f:
                img_entry.delete(0, tk.END)
                img_entry.insert(0, f)
        
        ttk.Button(dialog, text="选择图片", command=browse_edit_image).pack(pady=5)
        
        def save_edit():
            new_comment = text_edit.get("1.0", tk.END).strip()
            new_img = img_entry.get().strip()
            if not new_comment:
                messagebox.showwarning("警告", "备注内容不能为空")
                return
            if typ == "文件夹":
                if update_folder_comment(path, new_comment, new_img):
                    messagebox.showinfo("成功", "文件夹备注已更新")
                    dialog.destroy()
                    self.perform_search()
                else:
                    messagebox.showerror("错误", "更新失败")
            else:
                add_file_remark(path, new_comment, new_img)
                messagebox.showinfo("成功", "文件备注已更新")
                dialog.destroy()
                self.perform_search()
        
        ttk.Button(dialog, text="保存", command=save_edit).pack(pady=10)
    
    def save_results(self):
        """保存当前表格内容到文本文件"""
        if not self.result_tree.get_children():
            messagebox.showwarning("警告", "没有可保存的结果")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in self.result_tree.get_children():
                    values = self.result_tree.item(item, "values")
                    f.write(f"类型: {values[0]}\n路径: {values[1]}\n备注: {values[2]}\n图片: {values[3]}\n{'-'*50}\n")
            messagebox.showinfo("成功", "搜索结果已保存")

if __name__ == '__main__':
    root = tk.Tk()
    app = RemarkApp(root)
    root.mainloop()