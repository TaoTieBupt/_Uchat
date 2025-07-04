# Uchat/server/event_handler/like_moment.py
from server import memory
from common.message import MessageType
from server.util import database as db

def run(sc, parameters):
    """处理点赞动态的请求"""
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id: return

    moment_id = parameters.get('moment_id')
    if not moment_id: return

    user = db.get_user_by_id(user_id)
    if not user: return

    if db.add_like_to_moment(moment_id, user_id, user['username']):
        updated_moment = db.get_moment_by_id(moment_id)
        if updated_moment:
            moment_author_id = updated_moment['user_id']
            author_sc = memory.user_id_to_sc.get(moment_author_id)
            if author_sc:
                author_sc.send(MessageType.moment_update, {'moment': updated_moment})
            
            if sc != author_sc:
                sc.send(MessageType.moment_update, {'moment': updated_moment})