# Uchat/client/forms/contacts_form.py
import tkinter as tk
from tkinter import simpledialog, messagebox
from common.global_vars import client_memory
from common.message import MessageType
from common.util.socket_listener import add_listener, remove_listener, get_last_message_display, stop_socket_listener
from client.components.vertical_scrolled_frame import VerticalScrolledFrame
from client.components.contact_item import ContactItem

class ContactsForm(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        username = client_memory['username']
        self.master.title(f"Uchat - {username}")
        self.master.geometry("320x550")
        self.pack(fill="both", expand=True)

        self.contact_widgets = {}

        self.create_widgets()
        self.load_contacts()
        self.update_pending_requests_button()

        add_listener(self.socket_listener)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """创建顶部的功能按钮"""
        top_frame = tk.Frame(self)
        top_frame.pack(fill='x', pady=5, padx=5)
        
        self.add_friend_btn = tk.Button(top_frame, text="+好友", command=self.on_add_friend)
        self.add_friend_btn.pack(side='left', padx=2)
        
        self.create_room_btn = tk.Button(top_frame, text="+群聊", command=self.on_create_room)
        self.create_room_btn.pack(side='left', padx=2)

        self.join_room_btn = tk.Button(top_frame, text="入群", command=self.on_join_room)
        self.join_room_btn.pack(side='left', padx=2)

        self.moments_btn = tk.Button(top_frame, text="动态", command=self.open_moments_view)
        self.moments_btn.pack(side='left', padx=2)

        # 【新增】“我的资料”按钮
        self.profile_btn = tk.Button(top_frame, text="我的", command=self.open_my_profile)
        self.profile_btn.pack(side='left', padx=2)

        self.pending_requests_btn = tk.Button(top_frame, text="好友请求", command=self.show_pending_requests)
        self.pending_requests_btn.pack(side='right', padx=2)
        
        self.scrolled_frame = VerticalScrolledFrame(self)
        self.scrolled_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def refresh_contacts(self):
        """重新加载并排序联系人列表"""
        contacts = sorted(client_memory['contacts'].values(), key=lambda c: (
            -(c['type'] == 'user' and c.get('online', False)),
            c['type'] != 'user',
            c['type'] != 'room',
            c['name'].lower()
        ))
        
        for widget in self.contact_widgets.values():
            widget.destroy()
        self.contact_widgets.clear()

        for contact_data in contacts:
            key = f"{contact_data['type']}_{contact_data['id']}"
            item = ContactItem(self.scrolled_frame.interior, contact_data, onclick=lambda data=contact_data: self.open_chat(data))
            item.pack(fill='x', padx=2, pady=2)
            item.update_last_message(get_last_message_display(key))
            self.contact_widgets[key] = item
            
            if contact_data['type'] == 'user':
                self.create_friend_menu(item, contact_data)

    def create_friend_menu(self, widget, contact_data):
        """为好友联系人创建右键菜单，增加“查看资料”"""
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="发送消息", command=lambda: self.open_chat(contact_data))
        menu.add_command(label="查看资料", command=lambda: self.open_user_profile(contact_data))
        menu.add_separator()
        menu.add_command(label="删除好友", command=lambda: self.on_delete_friend(contact_data))

        def show_menu(event):
            menu.post(event.x_root, event.y_root)

        widget.bind_all_children("<Button-3>", show_menu)
        widget.bind("<Button-3>", show_menu)

    def on_delete_friend(self, contact_data):
        friend_name = contact_data['name']
        if messagebox.askyesno("确认删除", f"您确定要删除好友 '{friend_name}' 吗？\n此操作不可恢复。", parent=self.master):
            client_memory['sc'].send(MessageType.del_friend, {'friend_id': contact_data['id']})

    def load_contacts(self):
        self.refresh_contacts()

    def update_pending_requests_button(self):
        count = len(client_memory['pending_requests'])
        if count > 0:
            self.pending_requests_btn.config(text=f"好友请求 ({count})", fg="red")
        else:
            self.pending_requests_btn.config(text="好友请求", fg="black")

    def on_add_friend(self):
        friend_name = simpledialog.askstring("添加好友", "请输入好友的用户名:", parent=self.master)
        if friend_name and friend_name.strip(): client_memory['sc'].send(MessageType.add_friend, {'username': friend_name.strip()})

    def on_create_room(self):
        room_name = simpledialog.askstring("创建群聊", "请输入群聊名称:", parent=self.master)
        if room_name and room_name.strip(): client_memory['sc'].send(MessageType.create_room, {'room_name': room_name.strip()})

    def on_join_room(self):
        room_name = simpledialog.askstring("加入群聊", "请输入要加入的群聊名称:", parent=self.master)
        if room_name and room_name.strip(): client_memory['sc'].send(MessageType.join_room, {'room_name': room_name.strip()})
        
    def open_my_profile(self):
        from .profile_form import ProfileForm
        profile_win = tk.Toplevel(self.master)
        ProfileForm(master=profile_win, is_my_profile=True)
        
    def open_user_profile(self, contact_data):
        from .profile_form import ProfileForm
        profile_win = tk.Toplevel(self.master)
        ProfileForm(master=profile_win, user_id=contact_data['id'], is_my_profile=False)

    def open_moments_view(self):
        from .moments_form import MomentsForm
        for w in self.master.winfo_children():
            if isinstance(w, tk.Toplevel) and w.title() == "好友动态":
                w.deiconify(); w.lift(); return
        moments_window = tk.Toplevel(self.master)
        MomentsForm(master=moments_window)

    def show_pending_requests(self):
        requests = client_memory['pending_requests']
        if not requests: messagebox.showinfo("提示", "没有待处理的好友请求。", parent=self.master); return
        req_window = tk.Toplevel(self.master); req_window.title("待处理的好友请求"); req_window.geometry("350x200")
        tk.Label(req_window, text="点击接受或拒绝：").pack(pady=5)
        for user_id, username in list(requests.items()):
            frame = tk.Frame(req_window); frame.pack(fill='x', padx=10, pady=5)
            tk.Label(frame, text=f"{username} 请求添加你为好友").pack(side='left', expand=True, anchor='w')
            btn_frame = tk.Frame(frame); btn_frame.pack(side='right')
            tk.Button(btn_frame, text="接受", bg='lightgreen', command=lambda uid=user_id, f=frame: self.resolve_request(uid, True, f)).pack(side='left', padx=5)
            tk.Button(btn_frame, text="拒绝", bg='lightcoral', command=lambda uid=user_id, f=frame: self.resolve_request(uid, False, f)).pack(side='left')

    def resolve_request(self, from_user_id, accepted, frame_widget):
        client_memory['sc'].send(MessageType.resolve_friend_request, {'from_user_id': from_user_id, 'accepted': accepted})
        if from_user_id in client_memory['pending_requests']: del client_memory['pending_requests'][from_user_id]
        self.update_pending_requests_button(); frame_widget.destroy()

    def open_chat(self, contact_data):
        from .chat_form import ChatForm
        target_key = f"{contact_data['type']}_{contact_data['id']}"
        if target_key in client_memory['chat_forms'] and client_memory['chat_forms'][target_key].master.winfo_exists():
            client_memory['chat_forms'][target_key].master.deiconify(); client_memory['chat_forms'][target_key].master.lift(); return
        chat_window = tk.Toplevel(self.master)
        chat_form = ChatForm(contact_data, master=chat_window)
        client_memory['chat_forms'][target_key] = chat_form

    def socket_listener(self, data):
        msg_type = data.get('type')
        params = data.get('parameters', {})
        if msg_type == MessageType.add_friend_result or msg_type == MessageType.general_msg:
            if params.get('type') == 'system': return
            messagebox.showinfo("提示", params.get('message', params.get('reason', '')))
            if params.get('type') == 'logout': self.on_closing(force_close=True)
        elif msg_type == MessageType.contact_info:
            contact = params['contact']; key = f"{contact['type']}_{contact['id']}"; client_memory['contacts'][key] = contact
            self.refresh_contacts(); messagebox.showinfo("新联系人", f"您已添加 '{contact['name']}'！")
        elif msg_type == MessageType.del_info:
            key_to_del = params.get('key')
            if key_to_del in client_memory['contacts']:
                del client_memory['contacts'][key_to_del]
                self.refresh_contacts(); messagebox.showinfo("通知", "一个联系人关系已解除。")
        elif msg_type == MessageType.del_friend_result:
            if params.get('success'): messagebox.showinfo("成功", "好友已删除。")
            else: messagebox.showerror("失败", params.get('reason', '未知错误'))
        elif msg_type == MessageType.incoming_friend_request:
            uid, uname = params['from_user_id'], params['from_username']; client_memory['pending_requests'][uid] = uname
            self.update_pending_requests_button(); messagebox.showinfo("好友请求", f"收到来自 {uname} 的好友请求！")
        elif msg_type == MessageType.friend_request_resolved:
            uname, accepted = params['username'], params['accepted']
            msg = f"{uname} 接受了您的好友请求。" if accepted else f"{uname} 拒绝了您的好友请求。"; messagebox.showinfo("好友请求结果", msg)
        elif msg_type == MessageType.user_status_change:
            user_id, online = params['user_id'], params['online']
            key = f"user_{user_id}"
            if key in client_memory['contacts']:
                client_memory['contacts'][key].update(params) # 更新所有信息，包括头像
                if key in self.contact_widgets:
                    self.contact_widgets[key].update_status(online)
                    if 'avatar' in params: self.contact_widgets[key].update_avatar(params['avatar'])
                self.refresh_contacts()
        elif msg_type == MessageType.on_new_message:
            sender_id, target_type, target_id = params['sender_id'], params['target_type'], params['target_id']
            key_to_update = f"room_{target_id}" if target_type == 'room' else (f"user_{sender_id}" if sender_id != client_memory['user_id'] else f"user_{target_id}")
            if key_to_update:
                if key_to_update not in client_memory['chat_history']: client_memory['chat_history'][key_to_update] = []
                client_memory['chat_history'][key_to_update].append(params)
                if key_to_update in self.contact_widgets:
                    self.contact_widgets[key_to_update].update_last_message(get_last_message_display(key_to_update))
        elif msg_type == MessageType.contact_profile_updated:
            user_id, updates = params.get('user_id'), params.get('updates', {})
            key = f"user_{user_id}"
            if key in client_memory['contacts']:
                client_memory['contacts'][key].update(updates)
                if key in self.contact_widgets and 'avatar' in updates:
                    self.contact_widgets[key].update_avatar(updates['avatar'])

    def on_closing(self, force_close=False):
        if force_close or messagebox.askokcancel("退出", "确定要退出 Uchat 吗？"):
            stop_socket_listener()
            if sc := client_memory.get('sc'):
                try: sc.socket.close()
                except: pass
            self.master.quit(); self.master.destroy()