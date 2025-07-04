# server/event_handler/get_user_profile.py
from server import memory
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    user_id_to_get = parameters.get('user_id')
    if not user_id_to_get: return
    
    profile_data = db.get_user_by_id(user_id_to_get)
    if profile_data:
        # 出于安全，不发送密码等敏感信息
        safe_profile = {
            'id': profile_data['id'],
            'username': profile_data['username'],
            'signature': profile_data['signature'],
            'avatar': profile_data['avatar'],
        }
        sc.send(MessageType.user_profile_data, {'profile': safe_profile})