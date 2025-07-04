# server/broadcast/__init__.py
from server import memory
from common.message import MessageType
from server.util import database as db

def broadcast_to_room(room_id, message_type, parameters, exclude_user_id=None):
    """向一个房间的所有在线成员广播消息。"""
    from server.util.database import get_room_member_ids
    
    member_ids = get_room_member_ids(room_id)
    for user_id in member_ids:
        # 排除指定的用户（通常是消息发送者自己）
        if user_id == exclude_user_id:
            continue
        sc = memory.user_id_to_sc.get(user_id) # 检查用户是否在线
        if sc:
            try:
                sc.send(message_type, parameters)
            except Exception as e:
                print(f"向用户 {user_id} 广播时出错: {e}")

def broadcast_user_status_change(user_id, is_online, extra_info=None):
    """通知一个用户的所有好友其状态变化，并能附带额外信息。"""
    user_info = db.get_user_by_id(user_id)
    if not user_info:
        return

    friends = db.get_all_friends(user_id)
    for friend in friends:
        friend_id = friend['id']
        friend_sc = memory.user_id_to_sc.get(friend_id)
        if friend_sc:
            # 1. 构建基础的数据包
            payload = {
                'user_id': user_id,
                'username': user_info['username'],
                'online': is_online
            }
            
            # 2. 如果有额外信息，则合并进去
            if extra_info:
                payload.update(extra_info)
            
            try:
                # 3. 发送最终构建好的数据包
                friend_sc.send(MessageType.user_status_change, payload)
            except Exception as e:
                print(f"通知好友 {friend_id} 状态变化失败: {e}")

def broadcast_profile_update(user_id, updated_fields):
    """【新增】通知一个用户的所有好友其资料已更新"""
    from server.util.database import get_all_friends
    
    friends = get_all_friends(user_id)
    for friend in friends:
        friend_id = friend['id']
        friend_sc = memory.user_id_to_sc.get(friend_id)
        if friend_sc:
            try:
                friend_sc.send(MessageType.contact_profile_updated, {
                    'user_id': user_id,
                    'updates': updated_fields # e.g., {'avatar': 'new_avatar.png'}
                })
            except Exception as e:
                print(f"通知好友 {friend_id} 资料更新失败: {e}")      

def broadcast_user_status_change(user_id, is_online, extra_info=None):
    # ...
    payload = {
        'user_id': user_id,
        'username': user_info['username'],
        'online': is_online
    }
    if extra_info:
        payload.update(extra_info) # 合并额外信息
        
    sc.send(MessageType.user_status_change, payload)                          