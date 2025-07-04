# server/event_handler/add_friend.py
from server import memory
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    from_user_id = memory.sc_to_user_id.get(sc)
    if not from_user_id: return

    to_username = parameters.get('username')
    to_user = db.get_user_by_name(to_username)

    if not to_user:
        sc.send(MessageType.add_friend_result, {'success': False, 'reason': '用户不存在'})
        return
    to_user_id = to_user['id']

    if from_user_id == to_user_id:
        sc.send(MessageType.add_friend_result, {'success': False, 'reason': '不能添加自己为好友'})
        return
    
    if db.are_friends(from_user_id, to_user_id):
        sc.send(MessageType.add_friend_result, {'success': False, 'reason': '你们已经是好友了'})
        return

    if db.add_friend_request(from_user_id, to_user_id) is None:
        sc.send(MessageType.add_friend_result, {'success': False, 'reason': '已发送过好友请求，请耐心等待对方同意'})
        return

    # 通知请求方：请求已成功发送
    sc.send(MessageType.add_friend_result, {'success': True, 'reason': '好友请求已发送'})

    # 如果目标用户在线，实时推送好友请求通知
    to_user_sc = memory.user_id_to_sc.get(to_user_id)
    if to_user_sc:
        from_user = db.get_user_by_id(from_user_id)
        to_user_sc.send(MessageType.incoming_friend_request, {
            'from_user_id': from_user_id,
            'from_username': from_user['username']
        })