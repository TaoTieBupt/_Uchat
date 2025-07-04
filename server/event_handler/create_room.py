# server/event_handler/create_room.py
from server import memory
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    creator_id = memory.sc_to_user_id.get(sc)
    if not creator_id: return

    room_name = parameters.get('room_name')
    if not room_name or len(room_name) > 50:
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '群聊名称无效'})
        return

    if db.get_room_by_name(room_name):
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '该群聊名称已被占用'})
        return

    room_id = db.create_room(room_name, creator_id)
    if room_id:
        sc.send(MessageType.general_msg, {'type': 'info', 'message': f'群聊 "{room_name}" 创建成功!'})
        # 将新群聊信息推送给创建者，以便更新其联系人列表
        sc.send(MessageType.contact_info, {'contact': {
            'id': room_id, 'name': room_name, 'type': 'room', 'online': True
        }})