# server/event_handler/voice_call_hangup.py
from server import memory
from common.message import MessageType

def run(sc, parameters):
    """处理挂断通话的请求"""
    hanger_id = memory.sc_to_user_id.get(sc)
    if not hanger_id: return
    
    other_party_id = parameters.get('other_party_id')
    
    # 通知另一方通话已结束
    other_party_sc = memory.user_id_to_sc.get(other_party_id)
    if other_party_sc:
        print(f"通话结束：{hanger_id} 与 {other_party_id}")
        other_party_sc.send(MessageType.voice_call_ended, {
            'reason': '对方已挂断。'
        })