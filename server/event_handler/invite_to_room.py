# server/event_handler/invite_to_room.py
from server import memory
from server.util import database as db
from common.message import MessageType
from server.broadcast import broadcast_to_room

def run(sc, parameters):
    inviter_id = memory.sc_to_user_id.get(sc)
    if not inviter_id: return

    room_id = parameters.get('room_id')
    invitee_id = parameters.get('invitee_id')
    
    # 权限检查：只有群成员才能邀请
    if not db.is_user_in_room(inviter_id, room_id): return
    
    inviter = db.get_user_by_id(inviter_id)
    invitee = db.get_user_by_id(invitee_id)
    room = db.get_room_by_id(room_id)
    if not all([inviter, invitee, room]): return

    # 添加用户到群聊
    if db.add_user_to_room(invitee_id, room_id):
        notification_text = f"'{inviter['username']}' 邀请 '{invitee['username']}' 加入了群聊"
        
        # 广播通知群内所有人
        broadcast_to_room(room_id, MessageType.room_update_notification, {
            'room_id': room_id,
            'text': notification_text
        })
        
        # 单独给被邀请者推送完整的群聊信息，以便他更新联系人列表
        invitee_sc = memory.user_id_to_sc.get(invitee_id)
        if invitee_sc:
            invitee_sc.send(MessageType.contact_info, {'contact': {
                'id': room['id'], 'name': room['room_name'], 'type': 'room', 'online': True
            }})