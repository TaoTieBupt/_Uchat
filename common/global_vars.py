# common/global_vars.py
# 客户端全局变量，用于在不同窗口和模块间共享状态
client_memory = {
    "tk_root": None,        # Tkinter 的根窗口实例
    "sc": None,             # SecureChannel 安全信道实例
    "user_id": None,        # 当前登录用户的ID
    "username": None,       # 当前登录用户的用户名
    "contacts": {},         # 联系人列表 {'user_1': {...}, 'room_1': {...}}
    "chat_history": {},     # 聊天记录 {'user_1': [msg1, ...], 'room_1': [msg1, ...]}
    "chat_forms": {},       # 打开的聊天窗口实例 {'user_1': chat_form_instance, ...}
    "pending_requests": {}  # 待处理的好友请求 {'user_id': 'username'}
}