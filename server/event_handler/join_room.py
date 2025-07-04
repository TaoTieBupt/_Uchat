# server/event_handler/join_room.py
from server import memory
from server.util import database as db
from common.message import MessageType
from server.broadcast import broadcast_to_room

def run(sc, parameters):
    """
    处理用户加入群聊的请求。
    - 验证用户身份。
    - 根据群聊名称查找群聊。
    - 将用户添加到群聊成员中。
    - 通知请求者加入成功，并推送群聊信息。
    - 广播通知群内其他成员有新人加入。
    """
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id:
        return

    room_name = parameters.get('room_name')
    if not room_name:
        return
        
    user = db.get_user_by_id(user_id)
    if not user:
        return

    room = db.get_room_by_name(room_name)
    if not room:
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '该群聊不存在。'})
        return
    
    room_id = room['id']

    if db.add_user_to_room(user_id, room_id):
        # 响应请求者
        sc.send(MessageType.general_msg, {'type': 'info', 'message': f'成功加入群聊 "{room_name}"'})
        sc.send(MessageType.contact_info, {'contact': {
            'id': room_id, 'name': room_name, 'type': 'room', 'online': True
        }})
        
        # 广播通知群内其他成员
        join_notification = {
            'type': 'system', 
            'message': f"'{user['username']}' 加入了群聊。",
            'room_id': room_id
        }
        broadcast_to_room(room_id, MessageType.general_msg, join_notification, exclude_user_id=user_id)
        print(f"用户 {user['username']} 加入了群聊 {room_name}")
    else:
        sc.send(MessageType.general_msg, {'type': 'warning', 'message': '您已在该群聊中。'})