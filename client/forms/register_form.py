# client/forms/register_form.py
import tkinter as tk
from tkinter import messagebox
from common.message import MessageType
from common.global_vars import client_memory

class RegisterForm(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("注册 Uchat")
        self.master.geometry("350x250")
        self.master.resizable(False, False)
        self.pack(pady=20)
        self.create_widgets()

    def create_widgets(self):
        fields = ["用户名:", "密码:", "确认密码:", "邮箱:"]
        self.entries = {}
        
        for i, field in enumerate(fields):
            label = tk.Label(self, text=field, font=('Arial', 10))
            label.grid(row=i, column=0, padx=10, pady=8, sticky='w')
            entry = tk.Entry(self, width=25, show="*" if "密码" in field else "", font=('Arial', 10))
            entry.grid(row=i, column=1, padx=10, pady=8)
            self.entries[field] = entry

        self.register_button = tk.Button(self, text="立即注册", command=self.do_register, font=('Arial', 11, 'bold'), width=20)
        self.register_button.grid(row=len(fields), columnspan=2, pady=20)

    def do_register(self):
        username = self.entries["用户名:"].get().strip()
        password = self.entries["密码:"].get()
        confirm_password = self.entries["确认密码:"].get()
        email = self.entries["邮箱:"].get().strip()

        if not all([username, password, confirm_password, email]):
            messagebox.showerror("错误", "所有字段均为必填项", parent=self.master)
            return
        if password != confirm_password:
            messagebox.showerror("错误", "两次输入的密码不匹配", parent=self.master)
            return
        
        sc = client_memory.get('sc')
        if not sc:
            messagebox.showerror("连接错误", "与服务器的连接已断开，请重启客户端", parent=self.master)
            return

        params = {'username': username, 'password': password, 'email': email}
        sc.send(MessageType.register, params)
        # 结果将由登录窗口的监听器处理，并弹出提示
        self.master.destroy() # 发送后关闭注册窗口