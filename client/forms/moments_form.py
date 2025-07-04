# Uchat/client/forms/moments_form.py
import tkinter as tk
import time
import os
import uuid
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk

from common.global_vars import client_memory
from common.message import MessageType
from common.util.socket_listener import add_listener, remove_listener
from client.components.vertical_scrolled_frame import VerticalScrolledFrame
# from .post_moment_form import PostMomentForm # 延迟导入

IMAGE_CACHE_PATH = 'client/image_cache/'
if not os.path.exists(IMAGE_CACHE_PATH):
    os.makedirs(IMAGE_CACHE_PATH)

class MomentsForm(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("好友动态")
        self.master.geometry("500x600")
        self.pack(fill="both", expand=True)
        
        self.moment_widgets = {}
        self.image_references = []
        
        self.is_listener_active = True
        add_listener(self.socket_listener)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_widgets()
        self.load_moments()

    def create_widgets(self):
        # ... (这部分代码保持不变)
        top_frame = tk.Frame(self, bd=1, relief="raised"); top_frame.pack(fill='x')
        self.refresh_btn = tk.Button(top_frame, text="刷新", command=self.load_moments); self.refresh_btn.pack(side='left', padx=5, pady=5)
        self.post_btn = tk.Button(top_frame, text="发布动态", command=self.open_post_window); self.post_btn.pack(side='right', padx=5, pady=5)
        self.scrolled_frame = VerticalScrolledFrame(self); self.scrolled_frame.pack(fill="both", expand=True)

    def open_post_window(self):
        from .post_moment_form import PostMomentForm
        post_window = tk.Toplevel(self.master)
        PostMomentForm(master=post_window, on_post_callback=self.load_moments)

    def load_moments(self):
        if self.refresh_btn['state'] == 'disabled': return
        self.refresh_btn.config(state='disabled', text="正在刷新...")
        client_memory['sc'].send(MessageType.get_moments)

    def display_moments(self, moments_list):
        self.refresh_btn.config(state='normal', text="刷新")
        for widget in self.scrolled_frame.interior.winfo_children():
            widget.destroy()
        self.moment_widgets.clear()
        self.image_references.clear()
        
        if not moments_list:
            tk.Label(self.scrolled_frame.interior, text="还没有任何动态...").pack(pady=20)
        else:
            for moment in moments_list:
                self.create_moment_widget(moment)
        self.refresh_btn.config(state='normal', text="刷新")

    def create_moment_widget(self, moment):
        """【修改】创建包含真实图片的动态UI"""
        moment_id = moment['id']
        
        if moment_id in self.moment_widgets: self.moment_widgets[moment_id].destroy()

        moment_frame = tk.Frame(self.scrolled_frame.interior, bd=2, relief="groove")
        moment_frame.pack(fill='x', padx=10, pady=5)
        self.moment_widgets[moment_id] = moment_frame
        
        header_frame = tk.Frame(moment_frame); header_frame.pack(fill='x', padx=5, pady=5)
        tk.Label(header_frame, text=moment['username'], font=('Arial', 12, 'bold'), fg="blue").pack(side='left')
        tk.Label(header_frame, text=time.strftime('%Y-%m-%d %H:%M', time.localtime(moment['timestamp'])), font=('Arial', 8), fg="gray").pack(side='right')
        
        if moment.get('content'):
            tk.Label(moment_frame, text=moment['content'], wraplength=450, justify='left', anchor='w').pack(fill='x', padx=10, pady=(0, 10))
        
        # 【核心修改】真实地显示图片
        image_data = moment.get('image_data')
        if image_data and isinstance(image_data, bytes):
            try:
                # 为了在Tkinter中显示，需要将二进制数据写入临时文件或内存流
                # 然后用Pillow打开
                image_id = f"{uuid.uuid4()}.png"
                filepath = os.path.join(IMAGE_CACHE_PATH, image_id)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                img = Image.open(filepath)
                # 限制图片在动态中显示的大小
                img.thumbnail((400, 400)) 
                photo = ImageTk.PhotoImage(img)
                
                # 【重要】保持对 PhotoImage 对象的引用，防止被垃圾回收
                self.image_references.append(photo)
                
                # 创建并显示图片标签
                img_label = tk.Label(moment_frame, image=photo)
                img_label.pack(padx=10, pady=5)
            except Exception as e:
                print(f"渲染动态图片失败: {e}")
                tk.Label(moment_frame, text="[图片加载失败]", fg="red").pack(padx=10, pady=5)
        
        actions_frame = tk.Frame(moment_frame); actions_frame.pack(fill='x', padx=10, pady=2)
        tk.Button(actions_frame, text="👍 赞", command=lambda mid=moment_id: self.like_moment(mid), relief="flat").pack(side='right', padx=5)
        tk.Button(actions_frame, text="💬 评论", command=lambda mid=moment_id: self.comment_moment(mid), relief="flat").pack(side='right')

        # ... (点赞和评论区显示逻辑保持不变) ...
        ttk.Separator(moment_frame, orient='horizontal').pack(fill='x', padx=5, pady=5)
        likes = moment.get('likes', [])
        if likes:
            likes_frame = tk.Frame(moment_frame, bg="#f0f0f0"); likes_frame.pack(fill='x', padx=10, pady=(0, 5))
            tk.Label(likes_frame, text="❤️", fg="red", bg="#f0f0f0").pack(side='left', anchor='n')
            tk.Label(likes_frame, text=", ".join(likes), wraplength=420, justify='left', bg="#f0f0f0").pack(side='left', padx=5)
        comments = moment.get('comments', [])
        if comments:
            for comment in comments:
                comment_frame = tk.Frame(moment_frame, bg="#f0f0f0"); comment_frame.pack(fill='x', padx=10, pady=1)
                comment_text = tk.Text(comment_frame, font=('Arial', 10), relief="flat", bg="#f0f0f0", height=1, wrap="word"); comment_text.pack(fill='x')
                comment_text.tag_configure("user", foreground="blue", font=('Arial', 10, 'bold'))
                comment_text.insert(tk.END, f"{comment['username']}: ", "user"); comment_text.insert(tk.END, comment['content']); comment_text.config(state="disabled")

    # ... (like_moment, comment_moment, socket_listener, on_closing 保持不变) ...
    def like_moment(self, moment_id): client_memory['sc'].send(MessageType.like_moment, {'moment_id': moment_id})
    def comment_moment(self, moment_id):
        content = simpledialog.askstring("发表评论", "请输入你的评论:", parent=self.master)
        if content and content.strip(): client_memory['sc'].send(MessageType.comment_moment, {'moment_id': moment_id, 'content': content.strip()})
    def socket_listener(self, data):
        if not self.is_listener_active: return
        msg_type, params = data.get('type'), data.get('parameters', {})
        if msg_type == MessageType.moments_list: self.display_moments(params.get('moments', []))
        elif msg_type == MessageType.moment_update:
            if updated_moment := params.get('moment'): self.create_moment_widget(updated_moment)
    def on_closing(self):
        if self.is_listener_active:
            remove_listener(self.socket_listener)
            self.is_listener_active = False
        self.master.destroy()