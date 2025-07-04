# Uchat/server/event_handler/voice_call_request.py
from server import memory
from common.message import MessageType
from server.util import database as db

def run(sc, parameters):
    """处理发起语音通话的请求"""
    caller_id = memory.sc_to_user_id.get(sc)
    if not caller_id: return

    callee_id = parameters.get('callee_id')
    if not callee_id: return

    caller_info = db.get_user_by_id(caller_id)
    if not caller_info: return
    
    callee_sc = memory.user_id_to_sc.get(callee_id)
    if callee_sc:
        print(f"用户 {caller_id} 正在呼叫用户 {callee_id}")
        callee_sc.send(MessageType.incoming_voice_call, {
            'caller_id': caller_id,
            'caller_name': caller_info['username']
        })
    else:
        sc.send(MessageType.voice_call_rejected, {
            'reason': '对方不在线或无法接听。'
        })