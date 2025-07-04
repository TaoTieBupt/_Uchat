# server/event_handler/__init__.py
from common.message import MessageType
# 导入所有事件处理器模块
from . import (
    register, login, send_message, add_friend, 
    resolve_friend_request, create_room, del_friend, 
    join_room, query_room_users,
    post_moment, get_moments,like_moment, comment_moment,  # 【新增】导入动态相关的处理器
    voice_call_request, voice_call_response, 
    voice_call_hangup, voice_data, # 【新增】导入语音通话处理器
    invite_to_room, leave_room, kick_from_room,
    update_profile, get_user_profile
)

# 事件类型到处理函数的映射
event_handler_map = {
    MessageType.register: register.run,
    MessageType.login: login.run,
    MessageType.send_message: send_message.run,
    MessageType.add_friend: add_friend.run,
    MessageType.resolve_friend_request: resolve_friend_request.run,
    MessageType.create_room: create_room.run,
    MessageType.del_friend: del_friend.run,
    MessageType.join_room: join_room.run,
    MessageType.query_room_users: query_room_users.run,
    MessageType.post_moment: post_moment.run,    # 【新增】
    MessageType.get_moments: get_moments.run,    # 【新增】
    MessageType.like_moment: like_moment.run,          # 【新增】
    MessageType.comment_moment: comment_moment.run,    # 【新增】
    # 【新增】
    MessageType.voice_call_request: voice_call_request.run,
    MessageType.voice_call_response: voice_call_response.run,
    MessageType.voice_call_hangup: voice_call_hangup.run,
    MessageType.voice_data: voice_data.run,
    # 【新增】
    MessageType.invite_to_room: invite_to_room.run,
    MessageType.leave_room: leave_room.run,
    MessageType.kick_from_room: kick_from_room.run,
    # 【新增】
    MessageType.update_profile: update_profile.run,
    MessageType.get_user_profile: get_user_profile.run,
}
def handle_event(sc, event_type, parameters):
    """
    主事件分发器。根据消息类型查找并执行相应处理器。
    """
    handler = event_handler_map.get(event_type)
    if handler:
        try:
            handler(sc, parameters)
        except Exception as e:
            import traceback
            print(f"处理事件 {event_type.name} 时出错: {e}")
            traceback.print_exc()
    else:
        print(f"警告: 未找到事件类型 {event_type.name} 的处理器")