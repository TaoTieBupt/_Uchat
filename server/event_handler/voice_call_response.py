# server/event_handler/voice_call_response.py
from server import memory
from common.message import MessageType

def run(sc, parameters):
    """处理响应通话的请求"""
    callee_id = memory.sc_to_user_id.get(sc)
    if not callee_id: return

    caller_id = parameters.get('caller_id')
    accepted = parameters.get('accepted')
    
    caller_sc = memory.user_id_to_sc.get(caller_id)
    if not caller_sc: return # 呼叫方已掉线

    if accepted:
        # 如果接听，通知呼叫方对方已接听
        print(f"用户 {callee_id} 接听了来自 {caller_id} 的通话")
        caller_sc.send(MessageType.voice_call_answered, {
            'callee_id': callee_id
        })
    else:
        # 如果拒绝，通知呼叫方对方已拒绝
        caller_sc.send(MessageType.voice_call_rejected, {
            'reason': '对方已拒绝您的通话请求。'
        })