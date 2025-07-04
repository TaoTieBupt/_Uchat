# client/components/contact_item.py
import tkinter as tk
from PIL import Image, ImageTk
import os

class ContactItem(tk.Frame):
    def __init__(self, parent, contact_data, onclick, **kwargs):
        super().__init__(parent, bd=1, relief="solid", **kwargs)
        self.pack_propagate(False)
        self.config(height=60, bg='white', cursor="hand2")

        self.contact_data = contact_data
        self.onclick = onclick
        self.avatar_photo = None # 保持引用

        # 左侧头像
        self.avatar_label = tk.Label(self, bg="white")
        self.avatar_label.pack(side='left', padx=5, pady=5)
        self.load_avatar(contact_data.get('avatar'))

        # 右侧信息区
        info_frame = tk.Frame(self, bg="white")
        info_frame.pack(side='left', fill='both', expand=True, padx=5)

        # 名字和在线状态
        name_frame = tk.Frame(info_frame, bg="white")
        name_frame.pack(fill='x')
        self.name_label = tk.Label(name_frame, text=contact_data.get('name', 'N/A'), font=('等线', 12, 'bold'), bg='white', anchor='w')
        self.name_label.pack(side='left')
        status_color = 'green' if contact_data.get('online', False) else 'gray'
        self.status_indicator = tk.Label(name_frame, text="●", font=('Arial', 10), fg=status_color, bg='white')
        self.status_indicator.pack(side='left', padx=5)
        
        # 最后一条消息
        self.last_msg_label = tk.Label(info_frame, text="", font=('等线', 9), fg='gray', bg='white', anchor='w')
        self.last_msg_label.pack(fill='x', anchor='w')
        
        self.bind_all_children("<Button-1>", self.handle_click)

    def load_avatar(self, filename):
        if not filename: filename = 'default.png'
        # 简化处理：假设头像文件在本地已缓存或与服务器路径一致
        filepath = f"server/uploaded_files/{filename}"
        try:
            if not os.path.exists(filepath):
                 filepath = f"server/uploaded_files/default.png"
            img = Image.open(filepath)
            img = img.resize((40, 40), Image.Resampling.LANCZOS)
            self.avatar_photo = ImageTk.PhotoImage(img)
            self.avatar_label.config(image=self.avatar_photo)
        except Exception as e:
            self.avatar_label.config(text="ERR")
            print(f"加载联系人头像失败: {e}")

    def handle_click(self, event): self.onclick(self.contact_data)
    def bind_all_children(self, sequence, func):
        self.bind(sequence, func)
        for child in self.winfo_children(): child.bind(sequence, func)
    def update_last_message(self, text): self.last_msg_label.config(text=text[:25] + '...' if len(text) > 25 else text)
    def update_status(self, online): self.status_indicator.config(fg='green' if online else 'gray')
    def update_avatar(self, filename): self.load_avatar(filename)