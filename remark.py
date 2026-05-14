# -*- coding: utf-8 -*-
# Filename: remark.py

__author__ = 'Piratf'

import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

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
    content = sys_encode(u'[.ShellClassInfo]' + os.linesep + 'InfoTip=')
    setting_file_path = get_setting_file_path(fpath)
    with open(setting_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        f.write(sys_encode(comment + os.linesep))
        if image_path:
            f.write('IconResource=' + image_path + ',0' + os.linesep)
    
    run_command('attrib "' + setting_file_path + '" +s +h')
    run_command('attrib "' + fpath + '" +s ')
    return True

def read_folder_comment(fpath):
    setting_file_path = get_setting_file_path(fpath)
    if not os.path.exists(setting_file_path):
        return None, None
    
    run_command('attrib "' + setting_file_path + '" -s -h')
    try:
        with open(setting_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            comment = None
            image_path = None
            if 'InfoTip=' in content:
                comment = content.split('InfoTip=')[1].split('\n')[0].strip()
            if 'IconResource=' in content:
                icon_line = content.split('IconResource=')[1].split('\n')[0].strip()
                if ',' in icon_line:
                    image_path = icon_line.split(',')[0].strip()
            return comment, image_path
    except:
        return None, None

class RemarkApp:
    def __init__(self, master):
        self.master = master
        master.title("文件夹备注管理器")
        master.geometry("900x700")
        
        self.search_thread = None
        self.stop_search = False
        self.pre_scan_enabled = False
        
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_add = ttk.Frame(self.notebook)
        self.tab_search = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_add, text="添加备注")
        self.notebook.add(self.tab_search, text="搜索备注")
        
        self.create_add_tab()
        self.create_search_tab()
    
    def create_add_tab(self):
        frame = self.tab_add
        frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frame, text="文件夹路径:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.path_entry = ttk.Entry(frame, width=60)
        self.path_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Button(frame, text="浏览", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(frame, text="备注内容:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.comment_text = scrolledtext.ScrolledText(frame, width=60, height=6)
        self.comment_text.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(frame, text="图片路径:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.image_path_entry = ttk.Entry(frame, width=50)
        self.image_path_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Button(frame, text="选择图片", command=self.browse_image).grid(row=2, column=2, padx=5, pady=5)
        
        self.image_preview_canvas = tk.Canvas(frame, bg='white', width=200, height=150)
        self.image_preview_canvas.grid(row=3, column=1, padx=5, pady=5)
        self.image_preview_canvas.create_text(100, 75, text="图片预览", fill='gray')
        
        ttk.Button(frame, text="添加备注", command=self.add_comment).grid(row=4, column=1, pady=10)
        
        self.status_label = ttk.Label(frame, text="")
        self.status_label.grid(row=5, column=1, pady=5)
    
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
        
        self.result_text = scrolledtext.ScrolledText(frame, width=80, height=15)
        self.result_text.grid(row=2, column=0, columnspan=3, sticky=tk.NSEW, padx=5, pady=5)
        
        self.image_frame = ttk.Frame(frame, borderwidth=1, relief=tk.SUNKEN)
        self.image_frame.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW, padx=5, pady=5)
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)
        
        self.image_canvas = tk.Canvas(self.image_frame, bg='white', width=300, height=200)
        self.image_canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        self.image_canvas.create_text(150, 100, text="图片预览区域\n备注不支持图片格式", fill='gray')
        
        ttk.Button(frame, text="保存结果", command=self.save_results).grid(row=4, column=1, pady=10)
        
        self.progress_frame = ttk.Frame(frame)
        self.progress_frame.grid(row=5, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="就绪")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
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
    
    def add_comment(self):
        fpath = self.path_entry.get().strip()
        comment = self.comment_text.get("1.0", tk.END).strip()
        image_path = self.image_path_entry.get().strip() if hasattr(self, 'image_path_entry') else ""
        
        if not fpath:
            messagebox.showwarning("警告", "请输入文件夹路径")
            return
        
        if not os.path.isdir(fpath):
            messagebox.showwarning("警告", "输入的不是有效的文件夹路径")
            return
        
        if not comment:
            messagebox.showwarning("警告", "备注内容不能为空")
            return
        
        if image_path and not os.path.isfile(image_path):
            messagebox.showwarning("警告", "图片路径无效")
            return
        
        setting_file_path = get_setting_file_path(fpath)
        if os.path.exists(setting_file_path):
            run_command('attrib "' + setting_file_path + '" -s -h')
        
        if update_folder_comment(fpath, comment, image_path):
            messagebox.showinfo("成功", "备注添加成功！\n备注可能需要过一会儿才会显示")
            self.path_entry.delete(0, tk.END)
            self.comment_text.delete("1.0", tk.END)
            if hasattr(self, 'image_path_entry'):
                self.image_path_entry.delete(0, tk.END)
                self.image_preview_canvas.delete("all")
                self.image_preview_canvas.create_text(100, 75, text="图片预览", fill='gray')
    
    def perform_search(self):
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            self.search_btn.config(text="搜索")
            self.progress_bar.stop()
            self.progress_label.config(text="已停止")
            return
        
        root_path = self.search_path_entry.get().strip()
        keyword = self.keyword_entry.get().strip()
        
        if not root_path:
            messagebox.showwarning("警告", "请输入搜索目录")
            return
        
        if not os.path.isdir(root_path):
            messagebox.showwarning("警告", "输入的不是有效的文件夹路径")
            return
        
        self.result_text.delete("1.0", tk.END)
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
        results = []
        folder_count = 0
        found_count = 0
        
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
                    
                    comment, image_path = read_folder_comment(folder_path)
                    if comment:
                        found_count += 1
                        if not keyword or (keyword.lower() in folder_path.lower() or keyword.lower() in comment.lower()):
                            results.append((folder_path, comment, image_path))
        except Exception as e:
            self.master.after(0, self.show_error, str(e))
        
        self.master.after(0, self.search_complete, results, folder_count, found_count)
    
    def update_progress(self, message):
        self.progress_label.config(text=message)
    
    def show_error(self, message):
        messagebox.showerror("错误", message)
    
    def search_complete(self, results, folder_count, found_count):
        self.progress_bar.stop()
        self.search_btn.config(text="搜索")
        self.current_image_path = ""
        
        if not results:
            self.result_text.insert(tk.END, "未找到匹配的备注")
            self.progress_label.config(text=f"搜索完成：扫描 {folder_count} 个文件夹，未找到匹配结果")
            self.current_results = ""
            self.image_canvas.delete("all")
            self.image_canvas.create_text(150, 100, text="图片预览区域\n暂无图片", fill='gray')
            return
        
        result_str = f"搜索完成：扫描 {folder_count} 个文件夹，找到 {found_count} 条备注，匹配 {len(results)} 条\n\n"
        for i, (path, comment, image_path) in enumerate(results, 1):
            result_str += "【{}】\n".format(i)
            result_str += "文件夹路径: {}\n".format(path)
            result_str += "备注内容: {}\n".format(comment)
            if image_path:
                result_str += "图片路径: {}\n".format(image_path)
            result_str += "------------------------\n"
        
        self.result_text.insert(tk.END, result_str)
        self.current_results = result_str
        
        first_image_path = None
        for _, _, image_path in results:
            if image_path and os.path.isfile(image_path):
                first_image_path = image_path
                break
        
        if first_image_path:
            self.update_image_preview(first_image_path, self.image_canvas, 300, 200)
            self.current_image_path = first_image_path
        else:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(150, 100, text="图片预览区域\n暂无图片", fill='gray')
        
        self.progress_label.config(text=f"搜索完成：扫描 {folder_count} 个文件夹，找到 {found_count} 条备注，匹配 {len(results)} 条")
    
    def save_results(self):
        if hasattr(self, 'current_results') and self.current_results:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存搜索结果"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_results)
                messagebox.showinfo("成功", "结果已保存！")
        else:
            messagebox.showwarning("警告", "没有可保存的搜索结果")

if __name__ == '__main__':
    root = tk.Tk()
    app = RemarkApp(root)
    root.mainloop()
