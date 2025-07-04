# server/event_handler/resolve_friend_request.py
from server import memory
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    # to_user_id 是操作者（接受/拒绝请求的人）
    to_user_id = memory.sc_to_user_id.get(sc)
    if not to_user_id: return

    from_user_id = parameters.get('from_user_id')
    accepted = parameters.get('accepted')

    from_user = db.get_user_by_id(from_user_id)
    to_user = db.get_user_by_id(to_user_id)
    if not from_user or not to_user: return

    if accepted:
        # 更新数据库中的关系为“已接受”
        if db.accept_friend_request(from_user_id, to_user_id):
            # 通知请求方(from_user)，他的请求已被接受
            from_user_sc = memory.user_id_to_sc.get(from_user_id)
            if from_user_sc:
                # 1. 发送请求被处理的通知
                from_user_sc.send(MessageType.friend_request_resolved, {
                    'username': to_user['username'], 'accepted': True
                })
                # 2. 实时推送新好友的信息给请求方，以便更新联系人列表
                from_user_sc.send(MessageType.contact_info, {'contact': {
                    'id': to_user['id'], 'name': to_user['username'], 'type': 'user', 
                    'online': True, 'pk': to_user['pk'] # to_user肯定在线
                }})

            # 推送新好友的信息给接受方(to_user，也就是自己)
            sc.send(MessageType.contact_info, {'contact': {
                'id': from_user['id'], 'name': from_user['username'], 'type': 'user', 
                'online': bool(from_user_sc), 'pk': from_user['pk']
            }})
    else: # 拒绝请求
        # 直接从数据库删除这条未接受的请求记录
        db.delete_friendship(from_user_id, to_user_id)
        from_user_sc = memory.user_id_to_sc.get(from_user_id)
        if from_user_sc:
            from_user_sc.send(MessageType.friend_request_resolved, {
                'username': to_user['username'], 'accepted': False
            })