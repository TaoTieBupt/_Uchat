# Uchat/common/message/__init__.py
import json
import struct
import base64 # 【新增】用于处理二进制数据的编码
from enum import Enum

# ===================================================================
# MessageType Enum (保持不变)
# ===================================================================
class MessageType(Enum):
    """定义了客户端和服务器之间的所有消息类型"""
    # C -> S (Client to Server)
    register = 101
    login = 102
    add_friend = 103
    del_friend = 104
    create_room = 105
    join_room = 106
    resolve_friend_request = 107
    send_message = 108
    query_room_users = 109
    post_moment = 110
    get_moments = 111
    like_moment = 112
    comment_moment = 113
    voice_call_request = 114    # 【新增】发起语音通话请求
    voice_call_response = 115   # 【新增】响应通话请求（接听/拒绝）
    voice_call_hangup = 116     # 【新增】挂断通话
    voice_data = 117            # 【新增】传输Opus编码的音频数据
    invite_to_room = 118      # 【新增】邀请好友入群
    leave_room = 119          # 【新增】退出群聊
    kick_from_room = 120      # 【新增】踢出群成员
    update_profile = 121        # 【新增】更新个人资料（签名/头像）
    get_user_profile = 122      # 【新增】获取指定用户的资料

    # S -> C (Server to Client)
    register_successful = 201
    register_failed = 202
    login_successful = 203
    login_failed = 204
    add_friend_result = 205
    del_friend_result = 206
    incoming_friend_request = 207
    friend_request_resolved = 208
    on_new_message = 209
    contact_info = 210
    del_info = 211
    user_status_change = 212
    room_user_list = 213
    general_msg = 214
    moments_list = 215
    post_moment_result = 216
    moment_update = 217
    incoming_voice_call = 218   # 【新增】收到一个语音通话请求
    voice_call_answered = 219   # 【新增】对方已接听
    voice_call_rejected = 220   # 【新增】对方已拒绝
    voice_call_ended = 221      # 【新增】通话已结束
    room_update_notification = 222 # 【新增】通用的群聊更新通知（成员加入/退出/被踢）
    profile_update_result = 223 # 【新增】更新资料的结果
    user_profile_data = 224     # 【新增】返回用户资料
    contact_profile_updated = 225 # 【新增】通知好友其资料（如头像）已更新

# ===================================================================
# 【核心修改】自定义JSON编码器和解码辅助函数
# ===================================================================
class CustomEncoder(json.JSONEncoder):
    """
    一个自定义的JSON编码器，能够处理 bytes 类型。
    它会将 bytes 对象编码为带有特殊标记的字典，以便后续解码。
    """
    def default(self, obj):
        if isinstance(obj, bytes):
            # 将 bytes 编码为 Base64 字符串，并添加一个特殊标记
            return {'__type__': 'bytes', 'data': base64.b64encode(obj).decode('utf-8')}
        # 对于其他类型，使用默认的编码器
        return super().default(obj)

def custom_decoder(obj):
    """
    一个自定义的JSON解码辅助函数。
    它会在解码过程中查找带有特殊标记的字典，并将其转换回 bytes 对象。
    """
    if '__type__' in obj and obj['__type__'] == 'bytes':
        return base64.b64decode(obj['data'])
    return obj

# ===================================================================
# 【核心修改】重写序列化和反序列化函数
#
# 我们将不再使用复杂的、分类型的二进制打包方案，
# 而是统一使用增强版的 JSON 序列化。
# 这极大地简化了逻辑，并能原生支持任意复杂的嵌套数据结构。
# ===================================================================

def serialize_message(message_type, parameters=None):
    """
    序列化整个消息。
    新方案：将所有参数统一用我们自定义的JSON编码器序列化。
    """
    if parameters is None:
        parameters = {}
    
    # 1. 构造完整的消息体
    full_message = {
        'type': message_type.value,
        'parameters': parameters
    }
    
    # 2. 使用自定义编码器将其转换为JSON字符串，再编码为UTF-8字节流
    #    cls=CustomEncoder 是这里的关键
    serialized_data = json.dumps(full_message, cls=CustomEncoder).encode('utf-8')
    
    return serialized_data

def deserialize_message(data):
    """
    反序列化整个消息。
    新方案：使用我们自定义的解码辅助函数来解析JSON。
    """
    # 1. 将UTF-8字节流解码为JSON字符串，然后解析为Python对象
    #    object_hook=custom_decoder 是这里的关键
    decoded_message = json.loads(data.decode('utf-8'), object_hook=custom_decoder)
    
    # 2. 将消息类型的值转换回 MessageType 枚举成员
    decoded_message['type'] = MessageType(decoded_message['type'])
    
    return decoded_message