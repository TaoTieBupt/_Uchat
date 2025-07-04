# Uchat/run_server.py
import socket
import select
import traceback
import json

from common.transmission.secure_channel import accept_client_to_secure_channel
from common.message import MessageType
from server import memory
from server.event_handler import handle_event
from server.util.database import init_db
from server.config import initialize_storage
def run_server():
    """
    主服务器运行循环
    """
    init_db()  # 初始化数据库
    initialize_storage()
    # 从 config.json 加载配置
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    server_port = config.get('server_port', 8888)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(False)
    server_socket.bind(('0.0.0.0', server_port))
    server_socket.listen(100)
    print(f"服务器已启动，在 0.0.0.0:{server_port} 上监听...")

    memory.sockets_list.append(server_socket)
    
    while True:
        try:
            readable, _, exceptional = select.select(memory.sockets_list, [], memory.sockets_list)

            for sock in readable:
                if sock == server_socket:
                    # 新连接
                    client_socket, client_address = server_socket.accept()
                    print(f"接受来自 {client_address} 的新连接")
                    sc = accept_client_to_secure_channel(client_socket)
                    if sc:
                        memory.sockets_list.append(client_socket)
                        memory.socket_to_sc[client_socket] = sc
                        memory.scs.append(sc)
                    else:
                        print(f"与 {client_address} 建立安全通道失败")
                else:
                    # 已有连接发送数据
                    sc = memory.socket_to_sc.get(sock)
                    if not sc:
                        continue
                    
                    try:
                        data_list = sc.on_data() # 可能会收到多个拼接的消息
                        if data_list is None: # 连接关闭
                             raise ConnectionResetError
                        
                        for data in data_list:
                            if data:
                                event_type = data['type']
                                parameters = data['parameters']
                                handle_event(sc, event_type, parameters)

                    except (ConnectionResetError, BrokenPipeError):
                        print(f"客户端 {sock.getpeername()} 断开连接")
                        user_id = memory.sc_to_user_id.get(sc)
                        if user_id:
                            # 广播下线通知
                            from server.broadcast import broadcast_user_status_change
                            broadcast_user_status_change(user_id, False)
                            memory.remove_user_sc(user_id)

                        memory.sockets_list.remove(sock)
                        if sock in memory.socket_to_sc:
                            del memory.socket_to_sc[sock]
                        if sc in memory.scs:
                            memory.scs.remove(sc)
                        sock.close()
                    except Exception:
                        print("处理数据时出错:")
                        traceback.print_exc()

            for sock in exceptional:
                print(f"套接字异常: {sock.getpeername()}")
                sc = memory.socket_to_sc.get(sock)
                if sc:
                    user_id = memory.sc_to_user_id.get(sc)
                    if user_id:
                        from server.broadcast import broadcast_user_status_change
                        broadcast_user_status_change(user_id, False)
                        memory.remove_user_sc(user_id)
                
                memory.sockets_list.remove(sock)
                if sock in memory.socket_to_sc:
                    del memory.socket_to_sc[sock]
                sock.close()

        except Exception as e:
            print(f"服务器主循环错误: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    run_server()