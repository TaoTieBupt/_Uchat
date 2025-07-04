# server/event_handler/del_friend.py
from server import memory
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    """
    处理删除好友请求。
    - 验证请求者身份。
    - 从数据库中双向删除好友关系。
    - 通知请求者删除成功，并让其客户端更新UI。
    - 如果被删除的好友在线，同样通知他/她更新UI。
    """
    user_a_id = memory.sc_to_user_id.get(sc)
    if not user_a_id:
        return

    user_b_id = parameters.get('friend_id')
    if not user_b_id:
        return

    if db.delete_friendship(user_a_id, user_b_id):
        # 通知请求者 (User A) 删除成功
        sc.send(MessageType.del_friend_result, {'success': True, 'friend_id': user_b_id})
        sc.send(MessageType.del_info, {'key': f"user_{user_b_id}"})
        print(f"用户 {user_a_id} 删除了好友 {user_b_id}")

        # 如果被删除方 (User B) 在线，也通知他
        user_b_sc = memory.user_id_to_sc.get(user_b_id)
        if user_b_sc:
            try:
                user_b_sc.send(MessageType.del_info, {'key': f"user_{user_a_id}"})
            except Exception as e:
                print(f"通知用户 {user_b_id} 被删除失败: {e}")
    else:
        sc.send(MessageType.del_friend_result, {'success': False, 'reason': '删除好友失败，可能已不是好友关系。'})