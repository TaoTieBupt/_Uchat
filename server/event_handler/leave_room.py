# server/event_handler/leave_room.py
from server import memory
from server.util import database as db
from common.message import MessageType
from server.broadcast import broadcast_to_room

def run(sc, parameters):
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id: return

    room_id = parameters.get('room_id')
    
    user = db.get_user_by_id(user_id)
    if not user: return
    
    # 检查是否是群主，群主不能直接退出（需要先转让或解散）
    owner_id = db.get_room_owner_id(room_id)
    if user_id == owner_id:
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '您是群主，不能退出群聊。请先转让群主或解散群聊。'})
        return
        
    if db.leave_room(user_id, room_id):
        # 通知客户端删除该群聊
        sc.send(MessageType.del_info, {'key': f"room_{room_id}"})
        
        # 广播通知群内剩余成员
        notification_text = f"'{user['username']}' 退出了群聊"
        broadcast_to_room(room_id, MessageType.room_update_notification, {
            'room_id': room_id,
            'text': notification_text
        })