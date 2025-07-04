# Uchat/common/util/socket_listener/__init__.py
import threading
import time
from common.global_vars import client_memory

_callback_funcs = []
_thread = None
_stop_event = threading.Event()


def add_listener(func):
    if func not in _callback_funcs:
        _callback_funcs.append(func)


def remove_listener(func):
    if func in _callback_funcs:
        _callback_funcs.remove(func)


def _dispatch_to_main_thread(data):
    tk_root = client_memory.get("tk_root")
    if tk_root and tk_root.winfo_exists():
        for func in _callback_funcs[:]:
            tk_root.after(0, func, data)


def socket_listener_thread_func():
    sc = client_memory.get("sc")
    if not sc:
        print("监听线程：安全信道不可用。")
        return

    while not _stop_event.is_set():
        try:
            messages = sc.on_data()
            if messages is None:
                print("与服务器的连接已断开。")
                _dispatch_to_main_thread({'type': 'DISCONNECTED'})
                break

            for message in messages:
                _dispatch_to_main_thread(message)

            time.sleep(0.1)

        except Exception as e:
            print(f"套接字监听线程出错: {e}")
            _dispatch_to_main_thread({'type': 'DISCONNECTED'})
            break


def start_socket_listener():
    global _thread, _stop_event
    if _thread and _thread.is_alive():
        return

    _stop_event.clear()
    _thread = threading.Thread(target=socket_listener_thread_func, daemon=True)
    _thread.start()
    print("客户端套接字监听线程已启动。")


def stop_socket_listener():
    global _thread
    _stop_event.set()
    if _thread:
        _thread.join(timeout=1)
    _thread = None
    _callback_funcs.clear()
    print("客户端套接字监听线程已停止。")


# ===================================================================
# 【核心修正】
# ===================================================================
def get_last_message_display(contact_key):
    """
    【修正版】生成联系人列表中最后一条消息的显示文本。
    能够智能处理文本和图片消息。
    """
    history = client_memory['chat_history'].get(contact_key, [])
    if not history:
        return ""

    last_msg_obj = history[-1]
    sender_name = last_msg_obj.get('sender_name', '我')  # 如果是自己发的，名字可能是'我'
    message_obj = last_msg_obj.get('message', {})

    preview_content = ""
    # 1. 根据消息类型生成不同的预览内容
    if message_obj.get('type') == 'text':
        preview_content = message_obj.get('data', '')
    elif message_obj.get('type') == 'image':
        preview_content = "[图片]"  # 对于图片消息，只显示占位符
    else:
        preview_content = "[未知消息]"

    # 2. 组合成最终的显示文本
    #    现在 preview_content 永远是字符串(str)，不会再有类型错误
    if contact_key.startswith('room_') and sender_name != '我':
        display_text = f"{sender_name}: {preview_content}"
    else:
        display_text = preview_content

    # 3. 截断长文本
    return display_text[:25] + '...' if len(display_text) > 25 else display_text