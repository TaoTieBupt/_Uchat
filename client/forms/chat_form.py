# Uchat/client/forms/chat_form.py
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import os
import shutil
import uuid
from PIL import Image, ImageTk

from common.global_vars import client_memory
from common.message import MessageType
from common.util.socket_listener import add_listener, remove_listener
from client.voice_call_manager import VoiceCallManager
from client.components.vertical_scrolled_frame import VerticalScrolledFrame

IMAGE_CACHE_PATH = 'client/image_cache/'
if not os.path.exists(IMAGE_CACHE_PATH): os.makedirs(IMAGE_CACHE_PATH)
    
FILE_CACHE_PATH = 'client/file_cache/'
if not os.path.exists(FILE_CACHE_PATH): os.makedirs(FILE_CACHE_PATH)


class ChatForm(tk.Frame):
    def __init__(self, contact_data, master=None):
        super().__init__(master)
        self.master = master
        self.contact_data = contact_data
        self.target_key = f"{contact_data['type']}_{contact_data['id']}"
        self.image_references = []

        self.master.title(f"与 {contact_data['name']} 聊天中")
        self.master.geometry("550x500")
        self.center_window()
        self.pack(fill="both", expand=True)

        self.voice_manager = VoiceCallManager()

        self.create_widgets()
        self.load_history()

        self.is_listener_active = True
        add_listener(self.socket_listener)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.voice_manager.set_ui_callback(self.update_call_ui)

    def center_window(self):
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - 550) // 2
        y = (screen_height - 500) // 2
        self.master.geometry(f"+{x}+{y}")

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill='x', padx=10, pady=5)
        title_label = tk.Label(top_frame, text=self.contact_data['name'], font=('等线', 12, 'bold'))
        title_label.pack(side='left')
        
        if self.contact_data['type'] == 'user':
            self.call_button = tk.Button(top_frame, text="📞", font=('Arial', 12), command=self.start_voice_call, relief="flat", cursor="hand2")
            self.call_button.pack(side='right', padx=5)
        elif self.contact_data['type'] == 'room':
            members_button = tk.Button(top_frame, text="查看成员", command=self.query_room_members)
            members_button.pack(side='right')

        self.call_status_frame = tk.Frame(self, bg="lightblue")
        self.call_status_label = tk.Label(self.call_status_frame, text="", bg="lightblue", font=('Arial', 10, 'bold'))
        self.call_status_label.pack(side="left", padx=10, pady=5)
        self.hangup_button = tk.Button(self.call_status_frame, text="挂断", bg="red", fg="white", command=self.hangup_voice_call)
        
        self.text_frame = tk.Frame(self)
        self.text_frame.pack(padx=10, pady=5, fill='both', expand=True)

        self.chat_canvas = tk.Canvas(self.text_frame, bg='#f0f0f0', highlightthickness=0)
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(self.text_frame, orient="vertical", command=self.chat_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.chat_frame = tk.Frame(self.chat_canvas, bg='#f0f0f0')
        self.chat_frame_id = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        
        self.chat_frame.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)

        input_frame = tk.Frame(self, height=40)
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.msg_entry = tk.Entry(input_frame, font=('等线', 11))
        self.msg_entry.pack(side='left', fill='x', expand=True, ipady=5)
        self.msg_entry.bind("<Return>", self.send_text_message)
        
        self.send_button = tk.Button(input_frame, text="发送", command=self.send_text_message)
        self.send_button.pack(side='right', padx=5)
        
        self.plus_button = tk.Button(input_frame, text="+", font=('Arial', 14, 'bold'), relief="flat", cursor="hand2")
        self.plus_button.pack(side='right', padx=(0, 5))
        
        self.attachment_menu = tk.Menu(self.master, tearoff=0)
        self.attachment_menu.add_command(label="🖼️ 发送图片", command=self.send_image)
        self.attachment_menu.add_command(label="📎 发送文件", command=self.send_file)
        self.plus_button.bind("<Button-1>", self.show_attachment_menu)

    def show_attachment_menu(self, event):
        try: self.attachment_menu.post(event.x_root, event.y_root)
        finally: self.attachment_menu.grab_release()

    def on_frame_configure(self, event=None):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)

    def on_canvas_configure(self, event=None):
        self.chat_canvas.itemconfig(self.chat_frame_id, width=event.width)

    def load_history(self):
        history = client_memory['chat_history'].get(self.target_key, [])
        for msg in history: self.append_message(msg)

    def append_message(self, msg_data):
        is_me = (msg_data.get('sender_id') == client_memory['user_id'])
        msg_container = tk.Frame(self.chat_frame, bg='#f0f0f0'); msg_container.pack(fill='x', padx=5, pady=5)
        align_frame = tk.Frame(msg_container, bg='#f0f0f0'); align_frame.pack(side='right' if is_me else 'left', anchor='e' if is_me else 'w')
        bubble_frame = tk.Frame(align_frame, bg='#95ec69' if is_me else 'white', bd=1, relief="solid", padx=10, pady=5); bubble_frame.pack()
        self.create_message_content(bubble_frame, msg_data, is_me)
        self.master.after(100, self.on_frame_configure)

    def create_message_content(self, parent_frame, msg_data, is_me):
        message_obj = msg_data.get('message', {}); timestamp_str = time.strftime('%H:%M:%S', time.localtime(msg_data.get('timestamp', time.time())))
        if self.contact_data['type'] == 'room' and not is_me:
            tk.Label(parent_frame, text=msg_data.get('sender_name', 'Unknown'), font=('等线', 10, 'bold'), bg=parent_frame.cget('bg'), fg='#555555', anchor='w').pack(anchor='w', padx=0, pady=(0, 2))
        msg_type = message_obj.get('type')
        if msg_type == 'text': tk.Label(parent_frame, text=message_obj.get('data', ''), wraplength=300, justify='left', bg=parent_frame.cget('bg'), font=('等线', 12)).pack(anchor='w', padx=0, pady=0)
        elif msg_type == 'image': self.display_image(parent_frame, message_obj.get('data'))
        elif msg_type == 'file': self.display_file_card(parent_frame, message_obj)
        tk.Label(parent_frame, text=timestamp_str, font=('等线', 8), fg='#888888', bg=parent_frame.cget('bg'), anchor='e' if is_me else 'w').pack(fill='x', padx=0, pady=(2, 0))

    def display_image(self, parent_frame, image_data):
        if not isinstance(image_data, bytes): tk.Label(parent_frame, text="[图片数据错误]", bg=parent_frame.cget('bg'), font=('等线', 10), fg='red').pack(); return
        try:
            filepath = os.path.join(IMAGE_CACHE_PATH, f"{uuid.uuid4()}.png");
            with open(filepath, 'wb') as f: f.write(image_data)
            img = Image.open(filepath); img.thumbnail((200, 200)); photo = ImageTk.PhotoImage(img)
            self.image_references.append(photo)
            tk.Label(parent_frame, image=photo, bg=parent_frame.cget('bg'), bd=1, relief="solid").pack(padx=5, pady=5)
        except Exception as e: tk.Label(parent_frame, text="[图片加载失败]", bg=parent_frame.cget('bg'), font=('等线', 10), fg='red').pack(); print(f"加载图片失败: {e}")
            
    def display_file_card(self, parent_frame, message_obj):
        file_data, original_name, file_size = message_obj.get('data'), message_obj.get('original_name', 'unknown_file'), message_obj.get('size', 0)
        _, ext = os.path.splitext(original_name); cache_filepath = os.path.join(FILE_CACHE_PATH, f"{uuid.uuid4()}{ext}")
        try:
            with open(cache_filepath, 'wb') as f: f.write(file_data)
            file_card = tk.Frame(parent_frame, bd=1, relief="solid", bg="white", cursor="hand2")
            info_text = f"📎 {original_name}\n({self.format_file_size(file_size)})"; tk.Label(file_card, text=info_text, justify='left', bg="white").pack(side='left', padx=10, pady=5)
            file_card.bind("<Button-1>", lambda e, p=cache_filepath, on=original_name: self.save_file(p, on)); file_card.winfo_children()[0].bind("<Button-1>", lambda e, p=cache_filepath, on=original_name: self.save_file(p, on))
            file_card.pack(padx=5, pady=5)
        except Exception as e: tk.Label(parent_frame, text=f"[文件'{original_name}'接收失败]", bg=parent_frame.cget('bg'), font=('等线', 10), fg='red').pack(); print(f"处理接收的文件失败: {e}")

    def save_file(self, cache_path, original_name):
        save_path = filedialog.asksaveasfilename(title="保存文件", initialfile=original_name);
        if not save_path: return
        try: shutil.copy(cache_path, save_path); messagebox.showinfo("成功", f"文件已保存到:\n{save_path}", parent=self.master)
        except Exception as e: messagebox.showerror("错误", f"保存文件失败: {e}", parent=self.master)

    def send_text_message(self, event=None):
        message = self.msg_entry.get();
        if not message.strip(): return
        self.send_message({'type': 'text', 'data': message}); self.msg_entry.delete(0, tk.END)

    def send_image(self):
        filepath = filedialog.askopenfilename(title="选择一张图片", filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif")]);
        if not filepath: return
        try:
            if os.path.getsize(filepath) > 5 * 1024 * 1024: messagebox.showerror("错误", "图片大小不能超过5MB", parent=self.master); return
            with open(filepath, 'rb') as f: image_data = f.read()
            self.send_message({'type': 'image', 'name': os.path.basename(filepath), 'data': image_data})
        except Exception as e: messagebox.showerror("错误", f"读取图片失败: {e}", parent=self.master)

    def send_file(self):
        filepath = filedialog.askopenfilename(title="选择一个文件");
        if not filepath: return
        try:
            file_size = os.path.getsize(filepath)
            if file_size > 20 * 1024 * 1024: messagebox.showerror("错误", "文件大小不能超过20MB", parent=self.master); return
            with open(filepath, 'rb') as f: file_data = f.read()
            self.send_message({'type': 'file', 'name': os.path.basename(filepath), 'size': file_size, 'data': file_data})
        except Exception as e: messagebox.showerror("错误", f"读取文件失败: {e}", parent=self.master)

    def send_message(self, message_obj):
        params = {'target_id': self.contact_data['id'], 'target_type': self.contact_data['type'], 'message': message_obj, 'time': time.time()}
        client_memory['sc'].send(MessageType.send_message, params)
        my_msg_data = {**params, 'sender_id': client_memory['user_id'], 'sender_name': '我'}
        self.append_message(my_msg_data)
        if self.target_key not in client_memory['chat_history']: client_memory['chat_history'][self.target_key] = []
        client_memory['chat_history'][self.target_key].append(my_msg_data)
        
    def format_file_size(self, size_in_bytes):
        if size_in_bytes < 1024: return f"{size_in_bytes} B"
        elif size_in_bytes < 1024**2: return f"{size_in_bytes/1024:.1f} KB"
        elif size_in_bytes < 1024**3: return f"{size_in_bytes/1024**2:.1f} MB"
        else: return f"{size_in_bytes/1024**3:.1f} GB"

    def start_voice_call(self): self.voice_manager.start_call(self.contact_data['id'])
    def hangup_voice_call(self): self.voice_manager.hangup_call()

    def update_call_ui(self, status, data=None):
        if not self.master.winfo_exists(): return # 防御性检查
        current_contact_id = self.contact_data['id']
        is_relevant_call = (self.voice_manager.other_party_id == current_contact_id)
        is_relevant_incoming = (data and data.get('id') == current_contact_id)
        if status == "incoming":
            if is_relevant_incoming:
                if messagebox.askyesno("语音通话", f"{data['name']} 邀请您进行语音通话，是否接听？", parent=self.master): self.voice_manager.answer_call(data['id'], True)
                else: self.voice_manager.answer_call(data['id'], False)
            return
        if is_relevant_call or (not self.voice_manager.is_in_call):
            if self.voice_manager.is_in_call or status in ["正在呼叫..."]:
                self.call_status_frame.pack(fill='x', before=self.text_frame)
                self.hangup_button.pack(side="right", padx=10, pady=5)
            else:
                self.call_status_frame.pack_forget(); self.hangup_button.pack_forget()
            self.call_status_label.config(text=status)

    def socket_listener(self, data):
        if not self.is_listener_active: return
        msg_type, params = data.get('type'), data.get('parameters', {})
        if msg_type == MessageType.on_new_message:
            sender_id, target_type, target_id = params.get('sender_id'), params.get('target_type'), params.get('target_id')
            is_our_message = (target_type == 'room' and target_id == self.contact_data['id']) or (target_type == 'user' and sender_id == self.contact_data['id'])
            if is_our_message: self.append_message(params)
        elif msg_type == MessageType.room_user_list and params.get('room_id') == self.contact_data['id']: self.show_room_members_window(params.get('users', []))
        elif msg_type in (MessageType.general_msg, MessageType.room_update_notification):
             if params.get('type') == 'system' or msg_type == MessageType.room_update_notification:
                 if params.get('room_id') == self.contact_data['id']:
                     self.append_system_message(params.get('text') or params.get('message'))

    def append_system_message(self, message):
        msg_container = tk.Frame(self.chat_frame, bg='#f0f0f0'); msg_container.pack(fill='x', padx=5, pady=5)
        tk.Label(msg_container, text=f"--- {message} ---", font=('等线', 9), fg='#888888', bg='#f0f0f0').pack()
        self.master.after(100, self.on_frame_configure)

    def on_closing(self):
        if self.voice_manager.is_in_call and self.voice_manager.other_party_id == self.contact_data['id']: self.hangup_voice_call()
        if self.is_listener_active: remove_listener(self.socket_listener); self.is_listener_active = False
        self.voice_manager.set_ui_callback(None)
        if self.target_key in client_memory['chat_forms']: del client_memory['chat_forms'][self.target_key]
        self.master.destroy()

    def query_room_members(self): client_memory['sc'].send(MessageType.query_room_users, {'room_id': self.contact_data['id']})

    def show_room_members_window(self, users):
        # 【核心修复】在创建新窗口前，检查父窗口是否存在
        if not self.master.winfo_exists():
            return
            
        win = tk.Toplevel(self.master); win.title(f"'{self.contact_data['name']}' 成员"); win.geometry("300x400"); win.transient(self.master)
        
        win.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - 300) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - 400) // 2
        win.geometry(f"+{x}+{y}")
        
        action_frame = tk.Frame(win); action_frame.pack(fill='x', padx=5, pady=5)
        tk.Button(action_frame, text="邀请好友", command=lambda: self.invite_friend_to_room(win, users)).pack(side='left')
        tk.Button(action_frame, text="退出群聊", bg="lightcoral", command=lambda: self.leave_this_room(win)).pack(side='right')
        
        list_frame = VerticalScrolledFrame(win); list_frame.pack(fill='both', expand=True)

        my_id = client_memory['user_id']
        am_i_owner = any(u['id'] == my_id and u.get('is_owner') for u in users)
        
        sorted_users = sorted(users, key=lambda u: (not u.get('is_owner'), not u.get('online'), u.get('username', '').lower()))

        for user in sorted_users:
            member_frame = tk.Frame(list_frame.interior); member_frame.pack(fill='x', pady=1, padx=2)
            tk.Label(member_frame, text="●", fg="green" if user.get('online') else "gray", font=('Arial', 12)).pack(side='left', padx=5)
            tk.Label(member_frame, text=user['username'], anchor='w', font=('等线', 10)).pack(side='left')
            
            if user.get('is_owner'):
                tk.Label(member_frame, text="[群主]", font=('等线', 8, 'bold'), fg="orange").pack(side='left', padx=5)
            
            if am_i_owner and user['id'] != my_id:
                tk.Button(member_frame, text="移出", font=('等线', 8), bg="#ffcccc", 
                          command=lambda u_id=user['id'], u_name=user['username']: self.kick_user(u_id, u_name, win)).pack(side='right', padx=5)

    def invite_friend_to_room(self, parent_window, current_members):
        current_member_ids = {m['id'] for m in current_members}
        friends_to_invite = [f for f in client_memory['contacts'].values() if f['type'] == 'user' and f['id'] not in current_member_ids]
        if not friends_to_invite: messagebox.showinfo("提示", "您所有好友都已在群聊中。", parent=parent_window); return
        
        invite_win = tk.Toplevel(parent_window); invite_win.title("选择好友邀请"); invite_win.geometry("250x300"); invite_win.transient(parent_window)
        tk.Label(invite_win, text="请选择要邀请的好友:").pack(pady=5)
        
        list_box = tk.Listbox(invite_win, selectmode=tk.SINGLE); list_box.pack(fill='both', expand=True, padx=5)
        friend_map = {friend['name']: friend['id'] for friend in friends_to_invite}
        for friend in friends_to_invite: list_box.insert(tk.END, friend['name'])
        
        def do_invite():
            selected_indices = list_box.curselection()
            if not selected_indices: return
            selected_name = list_box.get(selected_indices[0])
            if friend_id := friend_map.get(selected_name):
                client_memory['sc'].send(MessageType.invite_to_room, {'room_id': self.contact_data['id'], 'invitee_id': friend_id})
                invite_win.destroy()
        tk.Button(invite_win, text="确认邀请", command=do_invite).pack(pady=10)

    def leave_this_room(self, parent_window):
        if messagebox.askyesno("确认", "您确定要退出该群聊吗？", parent=parent_window):
            client_memory['sc'].send(MessageType.leave_room, {'room_id': self.contact_data['id']})
            parent_window.destroy()
            self.master.destroy()

    def kick_user(self, user_id, username, parent_window):
        if messagebox.askyesno("确认", f"您确定要将 '{username}' 移出群聊吗？", parent=parent_window):
            client_memory['sc'].send(MessageType.kick_from_room, {
                'room_id': self.contact_data['id'],
                'kicked_id': user_id
            })
            parent_window.destroy()
            self.query_room_members()