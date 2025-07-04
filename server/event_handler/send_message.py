# Uchat/server/event_handler/send_message.py
import os
import time
import uuid
import json

from server import memory
from server.util import database as db
from common.message import MessageType
from server.broadcast import broadcast_to_room

UPLOAD_STORAGE_PATH = 'server/uploaded_files/'
if not os.path.exists(UPLOAD_STORAGE_PATH):
    os.makedirs(UPLOAD_STORAGE_PATH)

def run(sc, parameters):
    sender_id = memory.sc_to_user_id.get(sc)
    if not sender_id: return
    target_id, target_type, original_message_obj, timestamp = parameters.get('target_id'), parameters.get('target_type'), parameters.get('message'), parameters.get('time')
    sender_info = db.get_user_by_id(sender_id);
    if not sender_info: return
    sender_name = sender_info['username']

    message_type = original_message_obj.get('type')
    db_message_dict = {}

    if message_type == 'text':
        db_message_dict = original_message_obj
    
    # 【核心修正】统一图片和文件的处理
    elif message_type in ('image', 'file'):
        file_data = original_message_obj.get('data')
        # 为图片生成一个默认名
        original_name = original_message_obj.get('name', f'image_{int(timestamp)}.jpg') 
        file_size = original_message_obj.get('size', len(file_data) if file_data else 0)

        if not isinstance(file_data, bytes):
            print(f"错误: 收到的 {message_type} 消息中不包含有效的二进制数据。")
            return
            
        _, ext = os.path.splitext(original_name)
        server_filename = f"{uuid.uuid4()}{ext if ext else '.dat'}"
        filepath = os.path.join(UPLOAD_STORAGE_PATH, server_filename)

        try:
            with open(filepath, 'wb') as f: f.write(file_data)
            db_message_dict = {
                'type': message_type,
                'original_name': original_name,
                'server_name': server_filename,
                'size': file_size
            }
            print(f"用户 {sender_id} 上传了一个 {message_type}: {original_name}")
        except Exception as e:
            print(f"保存 {message_type} 失败: {e}")
            return
    else:
        print(f"收到未知消息类型: {message_type}"); return

    if db_message_dict:
        db.add_to_chat_history(sender_id, sender_name, target_id, target_type, db_message_dict, timestamp)

    forward_params = {
        'sender_id': sender_id, 'sender_name': sender_name, 'target_id': target_id,
        'target_type': target_type, 'message': original_message_obj, 'timestamp': timestamp
    }

    if target_type == 'user':
        if target_sc := memory.user_id_to_sc.get(target_id):
            try: target_sc.send(MessageType.on_new_message, forward_params)
            except Exception as e: print(f"向用户 {target_id} 实时发送消息失败: {e}")
    elif target_type == 'room':
        broadcast_to_room(target_id, MessageType.on_new_message, forward_params, exclude_user_id=sender_id)