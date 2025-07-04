# server/memory.py

# 用于 select() 的所有活动套接字列表
sockets_list = []

# 管理连接和用户的映射关系
# {SecureChannel_instance: user_id}
sc_to_user_id = {}
# {user_id: SecureChannel_instance}
user_id_to_sc = {}
# {socket_instance: SecureChannel_instance}
socket_to_sc = {}
# 所有活动的 SecureChannel 实例
scs = []

def add_user_sc(user_id, sc):
    """当用户登录成功时，将其会话信息添加到内存中。"""
    sc_to_user_id[sc] = user_id
    user_id_to_sc[user_id] = sc

def remove_user_sc(user_id):
    """当用户下线时，从内存中移除其会话信息。"""
    if user_id in user_id_to_sc:
        sc = user_id_to_sc.pop(user_id)
        if sc in sc_to_user_id:
            sc_to_user_id.pop(sc)