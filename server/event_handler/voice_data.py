# server/event_handler/voice_data.py
from server import memory
from common.message import MessageType

def run(sc, parameters):
    """处理并转发语音数据"""
    sender_id = memory.sc_to_user_id.get(sc)
    if not sender_id: return
    
    receiver_id = parameters.get('to_id')
    opus_data = parameters.get('data')
    
    # 直接将数据包转发给接收方
    receiver_sc = memory.user_id_to_sc.get(receiver_id)
    if receiver_sc:
        try:
            # 转发时，需要告诉接收方数据是谁发来的
            receiver_sc.send(MessageType.voice_data, {
                'from_id': sender_id,
                'data': opus_data
            })
        except Exception:
            # 如果发送失败（例如对方网络突然中断），可以考虑通知发送方
            pass