# client/forms/profile_form.py
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

from common.global_vars import client_memory
from common.message import MessageType
from common.util.socket_listener import add_listener, remove_listener

IMAGE_CACHE_PATH = 'client/image_cache/'

class ProfileForm(tk.Frame):
    def __init__(self, master=None, user_id=None, is_my_profile=False):
        super().__init__(master)
        self.master = master
        self.user_id = user_id if user_id else client_memory['user_id']
        self.is_my_profile = is_my_profile
        
        self.master.title("个人资料")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.avatar_photo = None # 用于保持对PhotoImage的引用
        
        self.create_widgets()
        self.load_profile_data()

        add_listener(self.socket_listener)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # 头像区域
        avatar_frame = tk.Frame(self)
        avatar_frame.pack(pady=10)
        self.avatar_label = tk.Label(avatar_frame, text="...", width=15, height=8, relief="solid")
        self.avatar_label.pack()
        if self.is_my_profile:
            self.avatar_label.config(cursor="hand2")
            self.avatar_label.bind("<Button-1>", self.change_avatar)

        # 用户名
        self.username_label = tk.Label(self, text="用户名: ...", font=('等线', 14, 'bold'))
        self.username_label.pack(pady=5)
        
        # 个性签名
        tk.Label(self, text="个性签名:", font=('等线', 10, 'italic'), fg="gray").pack(anchor='w', pady=(10,0))
        self.signature_text = tk.Text(self, height=3, font=('等线', 11), wrap=tk.WORD, relief="flat", bg=self.cget('bg'))
        self.signature_text.pack(fill='x')
        if not self.is_my_profile:
            self.signature_text.config(state='disabled')
        else:
            save_btn = tk.Button(self, text="保存签名", command=self.save_signature)
            save_btn.pack(pady=5)

    def load_profile_data(self):
        # 如果是自己的资料，直接从内存加载
        if self.is_my_profile:
            self.display_profile({
                'username': client_memory['username'],
                'signature': client_memory.get('my_profile', {}).get('signature', ''),
                'avatar': client_memory.get('my_profile', {}).get('avatar', 'default.png')
            })
        # 如果是查看好友资料，需要向服务器请求（此处简化，直接从contacts加载）
        else:
            contact_key = f"user_{self.user_id}"
            contact_info = client_memory['contacts'].get(contact_key)
            if contact_info:
                self.display_profile(contact_info)

    def display_profile(self, profile_data):
        self.username_label.config(text=f"用户名: {profile_data.get('name') or profile_data.get('username')}")
        
        if self.is_my_profile:
            self.signature_text.delete("1.0", tk.END)
            self.signature_text.insert("1.0", profile_data.get('signature', ''))
        else:
            self.signature_text.config(state='normal')
            self.signature_text.delete("1.0", tk.END)
            self.signature_text.insert("1.0", profile_data.get('signature', ''))
            self.signature_text.config(state='disabled')
            
        self.load_avatar(profile_data.get('avatar', 'default.png'))

    def load_avatar(self, filename):
        # 简化：假设所有头像都在服务器的上传目录，客户端需要一种方式获取
        # 实际应用中，这里应该是一个HTTP URL。我们简化为请求二进制数据
        # 暂时我们只从本地缓存加载
        # TODO: 实现一个从服务器下载头像的机制
        filepath = f"server/uploaded_files/{filename}" # 伪路径
        try:
            if not os.path.exists(filepath):
                 filepath = f"server/uploaded_files/default.png"
            img = Image.open(filepath)
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            self.avatar_photo = ImageTk.PhotoImage(img)
            self.avatar_label.config(image=self.avatar_photo, text="")
        except Exception as e:
            self.avatar_label.config(image='', text="头像加载失败")
            print(f"加载头像失败: {e}")

    def change_avatar(self, event=None):
        filepath = filedialog.askopenfilename(filetypes=[("图片", "*.jpg *.png")])
        if not filepath: return
        try:
            with open(filepath, 'rb') as f:
                avatar_data = f.read()
            client_memory['sc'].send(MessageType.update_profile, {'avatar_data': avatar_data})
        except Exception as e:
            messagebox.showerror("错误", f"读取头像失败: {e}")

    def save_signature(self):
        signature = self.signature_text.get("1.0", tk.END).strip()
        client_memory['sc'].send(MessageType.update_profile, {'signature': signature})

    def socket_listener(self, data):
        msg_type = data.get('type')
        params = data.get('parameters', {})
        if msg_type == MessageType.profile_update_result:
            if params.get('success'):
                messagebox.showinfo("成功", "个人资料已更新！")
                # 更新本地内存
                new_profile = params['profile']
                client_memory['my_profile']['signature'] = new_profile['signature']
                client_memory['my_profile']['avatar'] = new_profile['avatar']
                self.load_profile_data()
            else:
                messagebox.showerror("失败", params.get('reason', '更新失败'))
    
    def on_closing(self):
        remove_listener(self.socket_listener)
        self.master.destroy()