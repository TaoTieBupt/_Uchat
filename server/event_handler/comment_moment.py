# Uchat/server/event_handler/comment_moment.py
import time
from server import memory
from common.message import MessageType
from server.util import database as db

def run(sc, parameters):
    """处理评论动态的请求"""
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id: return

    moment_id = parameters.get('moment_id')
    content = parameters.get('content')
    if not moment_id or not content or not content.strip(): return

    user = db.get_user_by_id(user_id)
    if not user: return

    db.add_comment_to_moment(moment_id, user_id, user['username'], content, time.time())
    
    updated_moment = db.get_moment_by_id(moment_id)
    if updated_moment:
        moment_author_id = updated_moment['user_id']
        author_sc = memory.user_id_to_sc.get(moment_author_id)
        if author_sc:
            author_sc.send(MessageType.moment_update, {'moment': updated_moment})
        
        if sc != author_sc:
            sc.send(MessageType.moment_update, {'moment': updated_moment})