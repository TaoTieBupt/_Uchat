# server/event_handler/register.py
import hashlib
from server.util import database as db
from common.message import MessageType

def run(sc, parameters):
    username = parameters.get('username')
    password = parameters.get('password')
    email = parameters.get('email')
    
    # 检查用户名是否已被占用
    if db.get_user_by_name(username):
        sc.send(MessageType.register_failed, {'reason': '用户名已被占用'})
        return

    # 对密码进行SHA256哈希存储，不存明文密码
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    try:
        user_id = db.create_user(username, password_hash, email, None, None, '')
        if user_id:
            sc.send(MessageType.register_successful, {'user_id': user_id, 'username': username})
            print(f"新用户注册成功: {username} (ID: {user_id})")
        else:
            raise Exception("数据库插入失败")
    except Exception as e:
        print(f"注册失败: {e}")
        sc.send(MessageType.register_failed, {'reason': f'服务器内部错误: {e}'})