# Uchat/server/event_handler/login.py
import hashlib
import json
import os # 【新增】
from server import memory
from server.util import database as db
from common.message import MessageType
from server.broadcast import broadcast_user_status_change
from server.config import UPLOAD_STORAGE_PATH # 【新增】

def run(sc, parameters):
    # ... (用户验证逻辑不变) ...
    username, password = parameters.get('username'), parameters.get('password')
    user = db.get_user_by_name(username)
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if not user or user['password'] != password_hash:
        sc.send(MessageType.login_failed, {'reason': '用户不存在或密码错误'}); return
    user_id = user['id']
    if user_id in memory.user_id_to_sc:
        if old_sc := memory.user_id_to_sc.get(user_id):
            try: old_sc.send(MessageType.general_msg, {'type': 'logout', 'message': '您的账号已在别处登录。'}); old_sc.socket.close()
            except Exception as e: print(f"通知被踢下线的用户失败: {e}")
    memory.add_user_sc(user_id, sc)

    # --- 准备登录成功后返回的数据包 ---
    friends, rooms, pending_requests = db.get_all_friends(user_id), db.get_user_rooms(user_id), db.get_pending_friend_requests(user_id)
    chat_history_from_db = db.get_offline_messages(user_id)
    
    contacts_list = []
    online_friend_ids = list(memory.user_id_to_sc.keys())
    contacts_list = []
    online_friend_ids = list(memory.user_id_to_sc.keys())
    for friend in friends:
        contacts_list.append({
            'id': friend['id'], 
            'name': friend['username'], 
            'type': 'user', 
            'online': friend['id'] in online_friend_ids, 
            'pk': friend['pk'],
            'avatar': friend['avatar'] # 【新增】
        })
    for room in rooms:
        contacts_list.append({'id': room['id'], 'name': room['room_name'], 'type': 'room', 'online': True})
    # 【核心修正】处理历史记录，为图片/文件消息加载二进制数据
    formatted_history = []
    for msg_row in chat_history_from_db:
        msg_dict = dict(msg_row)
        try:
            # 数据库中的data字段是JSON字符串，先解析它
            message_obj_meta = json.loads(msg_dict['data'])
            msg_type = message_obj_meta.get('type')
            
            # 如果是图片或文件，需要读取二进制数据并添加到对象中
            if msg_type in ('image', 'file'):
                server_filename = message_obj_meta.get('server_name') or message_obj_meta.get('filename')
                if server_filename:
                    filepath = os.path.join(UPLOAD_STORAGE_PATH, server_filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            # 将二进制数据添加到即将发给客户端的消息对象中
                            message_obj_meta['data'] = f.read()
                    else:
                        # 如果文件在服务器上丢失了，也给一个标记
                        message_obj_meta['data'] = None
                        print(f"警告: 历史消息文件丢失: {filepath}")
            
            # 构建完整的消息格式
            formatted_msg = {
                'sender_id': msg_dict['sender_id'],
                'sender_name': msg_dict['sender_name'],
                'target_id': msg_dict['target_id'],
                'target_type': msg_dict['target_type'],
                'message': message_obj_meta, # 使用包含二进制数据的新对象
                'timestamp': msg_dict['timestamp']
            }
            formatted_history.append(formatted_msg)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"解析历史消息失败: {e}, 消息内容: {msg_dict['data']}")
            continue

    login_bundle = {
        'user_id': user_id,
        'username': username,
        'contacts': contacts_list,
        'pending_requests': [{'id': u['id'], 'username': u['username']} for u in pending_requests],
        'chat_history': formatted_history,
        'my_profile': { # 【新增】返回自己的完整资料
            'signature': user['signature'],
            'avatar': user['avatar']
        }
    }
    
    sc.send(MessageType.login_successful, login_bundle)
    print(f"用户 {username} (ID: {user_id}) 登录成功。")
    
    # 上下线通知中也带上头像信息
    user_info_for_broadcast = {'avatar': user['avatar']}
    broadcast_user_status_change(user_id, True, user_info_for_broadcast)