# Uchat/server/event_handler/query_room_users.py
from server import memory
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    """
    处理查询群成员列表的请求。
    这个版本确保会返回每个成员是否为群主的信息。
    """
    requester_id = memory.sc_to_user_id.get(sc)
    if not requester_id:
        return

    room_id = parameters.get('room_id')
    if not room_id:
        return
        
    # 1. 权限检查：确保请求者是群成员
    if not db.is_user_in_room(requester_id, room_id):
        sc.send(MessageType.general_msg, {'type': 'error', 'message': '您不是该群成员，无权查看。'})
        return

    # 2. 从数据库获取所有成员的ID列表
    member_ids = db.get_room_member_ids(room_id)
    
    # 3. 【关键】从数据库获取群主的ID
    owner_id = db.get_room_owner_id(room_id)
    
    # 4. 遍历成员ID，构建包含详细信息的列表
    members_list = []
    online_user_ids = memory.user_id_to_sc.keys()

    for mid in member_ids:
        user_info = db.get_user_by_id(mid)
        if user_info:
            # 5. 【关键】为每个成员构建字典，并附加 is_owner 标记
            members_list.append({
                'id': user_info['id'],
                'username': user_info['username'],
                'online': user_info['id'] in online_user_ids,
                'is_owner': (user_info['id'] == owner_id) # 判断当前成员ID是否与群主ID相同
            })

    # 6. 将包含完整信息的列表返回给客户端
    sc.send(MessageType.room_user_list, {
        'room_id': room_id,
        'users': members_list
    })