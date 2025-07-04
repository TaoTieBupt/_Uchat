# client/forms/login_form.py
import tkinter as tk
from tkinter import messagebox
from common.message import MessageType
from common.transmission.secure_channel import establish_secure_channel_to_server
from common.config import get_config
from common.util.socket_listener import start_socket_listener, add_listener, stop_socket_listener, remove_listener
from common.global_vars import client_memory

from .register_form import RegisterForm
from .contacts_form import ContactsForm

class LoginForm(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Uchat - 登录")
        self.master.geometry("350x280")
        self.master.resizable(False, False)
        self.pack(pady=20)

        self.create_widgets()
        self.connect_to_server()

    def create_widgets(self):
        tk.Label(self, text="Uchat", font=('Arial', 24, 'bold')).pack(pady=(0, 20))
        
        tk.Label(self, text="用户名:", font=('Arial', 10)).pack(anchor='w', padx=25)
        self.username_entry = tk.Entry(self, width=30, font=('Arial', 10))
        self.username_entry.pack(pady=5)

        tk.Label(self, text="密码:", font=('Arial', 10)).pack(anchor='w', padx=25)
        self.password_entry = tk.Entry(self, show="*", width=30, font=('Arial', 10))
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<Return>", lambda e: self.do_login()) # 支持回车登录

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        self.login_button = tk.Button(btn_frame, text="登录", command=self.do_login, width=10, font=('Arial', 10))
        self.login_button.pack(side='left', padx=10)

        self.register_button = tk.Button(btn_frame, text="注册", command=self.show_register, width=10, font=('Arial', 10))
        self.register_button.pack(side='left', padx=10)
        
        self.status_label = tk.Label(self, text="正在连接服务器...", fg="orange")
        self.status_label.pack(pady=10)

    def connect_to_server(self):
        """尝试与服务器建立安全信道"""
        self.login_button.config(state=tk.DISABLED)
        self.register_button.config(state=tk.DISABLED)
        
        config = get_config()
        sc = establish_secure_channel_to_server(config['server_ip'], config['server_port'])

        if not sc:
            self.status_label.config(text="连接服务器失败", fg="red")
            messagebox.showerror("连接失败", "无法连接到服务器。请检查配置或服务器状态。")
            return
        
        self.status_label.config(text="连接成功", fg="green")
        client_memory['sc'] = sc
        # 添加监听器并启动后台监听线程
        add_listener(self.socket_listener)
        start_socket_listener()
        
        self.login_button.config(state=tk.NORMAL)
        self.register_button.config(state=tk.NORMAL)

    def do_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        self.login_button.config(state=tk.DISABLED)
        client_memory['sc'].send(MessageType.login, {'username': username, 'password': password})

    def socket_listener(self, data):
        """处理来自服务器的消息"""
        msg_type = data.get('type')
        params = data.get('parameters', {})

        if msg_type == MessageType.login_successful:
            remove_listener(self.socket_listener) # 登录成功，此窗口的任务完成，移除监听器
            
            # 将服务器返回的初始化数据存入客户端全局内存
            client_memory['user_id'] = params['user_id']
            client_memory['username'] = params['username']
            client_memory['my_profile'] = params.get('my_profile', {})

            for contact in params.get('contacts', []):
                key = f"{contact['type']}_{contact['id']}"
                client_memory['contacts'][key] = contact
            
            for msg in params.get('chat_history', []):
                target_key = ""
                # 确定这条历史记录属于哪个对话窗口
                if msg['target_type'] == 'room':
                    target_key = f"room_{msg['target_id']}"
                elif msg['target_type'] == 'user':
                    # 私聊消息，key是对方的id
                    target_id = msg['target_id'] if msg['sender_id'] == params['user_id'] else msg['sender_id']
                    target_key = f"user_{target_id}"

                if target_key:
                    if target_key not in client_memory['chat_history']:
                        client_memory['chat_history'][target_key] = []
                    client_memory['chat_history'][target_key].append(msg)
            
            for req in params.get('pending_requests', []):
                client_memory['pending_requests'][req['id']] = req['username']

            # 切换到联系人主界面
            self.master.withdraw()
            contacts_window = tk.Toplevel(self.master)
            ContactsForm(master=contacts_window)

        elif msg_type == MessageType.login_failed:
            messagebox.showerror("登录失败", params.get('reason', '未知错误'))
            self.login_button.config(state=tk.NORMAL)
        
        elif msg_type == MessageType.register_successful:
             messagebox.showinfo("注册成功", f"用户 {params.get('username')} 注册成功！现在可以登录了。")

        elif msg_type == MessageType.register_failed:
            messagebox.showerror("注册失败", params.get('reason', '未知错误'))
            
        elif msg_type == 'DISCONNECTED':
            if self.master.winfo_exists():
                messagebox.showerror("连接中断", "与服务器的连接已断开。")
                self.login_button.config(state=tk.DISABLED)
                self.register_button.config(state=tk.DISABLED)
                self.status_label.config(text="连接已断开", fg="red")

    def show_register(self):
        register_window = tk.Toplevel(self.master)
        register_window.transient(self.master) # 使注册窗口成为登录窗口的子窗口
        RegisterForm(master=register_window)