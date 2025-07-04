# Uchat/client/forms/post_moment_form.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import os

from common.global_vars import client_memory
from common.message import MessageType
from common.util.socket_listener import add_listener, remove_listener

class PostMomentForm(tk.Frame):
    def __init__(self, master=None, on_post_callback=None):
        super().__init__(master)
        self.master = master
        self.master.title("发布新动态")
        self.master.geometry("450x400") # 窗口加大
        self.master.resizable(False, False)
        self.on_post_callback = on_post_callback
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # 【新增】用于存储待上传的图片数据
        self.image_data = None
        self.photo_image = None # 用于在UI上预览

        self.is_listener_active = True
        add_listener(self.socket_listener)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()

    def create_widgets(self):
        self.text_editor = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=('Arial', 11), height=10)
        self.text_editor.pack(fill="both", expand=True)
        self.text_editor.focus_set()

        # 【新增】图片预览和操作区
        self.image_preview_frame = tk.Frame(self)
        self.image_preview_frame.pack(fill='x', pady=5)
        self.image_preview_label = tk.Label(self.image_preview_frame)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', pady=10)
        
        self.add_img_button = tk.Button(btn_frame, text="添加图片", command=self.select_image)
        self.add_img_button.pack(side='left')
        
        self.post_button = tk.Button(btn_frame, text="发布", font=('Arial', 10, 'bold'), command=self.do_post)
        self.post_button.pack(side='right')

    def select_image(self):
        """打开文件对话框选择图片"""
        filepath = filedialog.askopenfilename(filetypes=[("图片", "*.jpg *.jpeg *.png")])
        if not filepath: return
        
        try:
            with open(filepath, 'rb') as f:
                self.image_data = f.read()

            # 显示预览图
            img = Image.open(filepath)
            img.thumbnail((100, 100))
            self.photo_image = ImageTk.PhotoImage(img)
            self.image_preview_label.config(image=self.photo_image)
            self.image_preview_label.pack()
        except Exception as e:
            messagebox.showerror("错误", f"加载图片预览失败: {e}", parent=self.master)
            self.image_data = None

    def do_post(self):
        content = self.text_editor.get("1.0", tk.END).strip()
        if not content and not self.image_data:
            messagebox.showerror("错误", "文本和图片不能都为空", parent=self.master)
            return

        self.post_button.config(state='disabled', text="发布中...")
        
        params = {'content': content}
        if self.image_data:
            params['image_data'] = self.image_data
            
        client_memory['sc'].send(MessageType.post_moment, params)

    def socket_listener(self, data):
        if not self.is_listener_active: return
        if data.get('type') == MessageType.post_moment_result:
            if data.get('parameters', {}).get('success'):
                if self.on_post_callback: self.on_post_callback()
                self.on_closing()
            else:
                messagebox.showerror("发布失败", data.get('parameters', {}).get('reason', '未知错误'), parent=self.master)
                self.post_button.config(state='normal', text="发布")

    def on_closing(self):
        if self.is_listener_active:
            remove_listener(self.socket_listener)
            self.is_listener_active = False
        self.master.destroy()