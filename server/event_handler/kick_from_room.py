# server/event_handler/kick_from_room.py
from server import memory
from server.util import database as db
from common.message import MessageType
from server.broadcast import broadcast_to_room

def run(sc, parameters):
    kicker_id = memory.sc_to_user_id.get(sc)
    if not kicker_id: return
    
    room_id = parameters.get('room_id')
    kicked_id = parameters.get('kicked_id')
    
    # 权限检查：只有群主才能踢人
    owner_id = db.get_room_owner_id(room_id)
    if kicker_id != owner_id:
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '您不是群主，没有权限踢人。'})
        return
        
    if kicker_id == kicked_id:
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '不能将自己踢出群聊。'})
        return
        
    kicked_user = db.get_user_by_id(kicked_id)
    if not kicked_user: return

    # 执行踢人操作（本质上和退群一样）
    if db.leave_room(kicked_id, room_id):
        notification_text = f"'{kicked_user['username']}' 已被群主移出群聊"
        
        # 广播通知群内所有人
        broadcast_to_room(room_id, MessageType.room_update_notification, {
            'room_id': room_id,
            'text': notification_text
        })
        
        # 单独通知被踢的人
        kicked_sc = memory.user_id_to_sc.get(kicked_id)
        if kicked_sc:
            kicked_sc.send(MessageType.del_info, {'key': f"room_{room_id}"})
            kicked_sc.send(MessageType.general_msg, {'type': 'info', 'message': f"您已被移出群聊 '{db.get_room_by_id(room_id)['room_name']}'"})