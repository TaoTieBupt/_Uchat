# Uchat/common/transmission/secure_channel.py
import socket
import struct
import os
import hashlib

# 确保导入的是新的、基于JSON的序列化模块
from common.message import serialize_message, deserialize_message
# 【重要】确保导入的是上面新的、基于PSK的加密模块
from common.cryptography.crypt import derive_session_key, aes_encrypt, aes_decrypt

# 辅助函数 recv_all (保持不变)
def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data.extend(packet)
    return bytes(data)

# 【新】数据包结构: | 总长度(4B) | 摘要(16B) | 加密数据(包含IV) |
HEADER_LEN = 4
DIGEST_LEN = 16

class SecureChannel:
    def __init__(self, sock, key=None):
        self.socket = sock
        self.key = key
        self.socket.setblocking(False)
        self._recv_buffer, self._expected_len = b'', None

    def send(self, message_type, parameters=None):
        """【新】使用PSK方案加密并发送消息"""
        if not self.key:
            raise ValueError("安全信道密钥尚未建立。")

        plaintext = serialize_message(message_type, parameters)
        
        # 加密 (加密函数内部会处理IV和填充)
        encrypted_data_with_iv = aes_encrypt(self.key, plaintext)
        
        # 计算完整性校验
        digest = hashlib.md5(encrypted_data_with_iv).digest()

        # 打包发送
        data_to_send = digest + encrypted_data_with_iv
        header = struct.pack('>I', len(data_to_send))
        self.socket.sendall(header + data_to_send)

    def on_data(self):
        """【新】使用PSK方案读取、解包、解密数据"""
        try:
            chunk = self.socket.recv(8192)
            if not chunk: return None
            self._recv_buffer += chunk
        except (BlockingIOError, InterruptedError): return []
        except Exception as e:
            print(f"接收数据时发生错误: {e}")
            return None

        messages = []
        while True:
            if self._expected_len is None:
                if len(self._recv_buffer) < HEADER_LEN: break
                self._expected_len = struct.unpack('>I', self._recv_buffer[:HEADER_LEN])[0]
                self._recv_buffer = self._recv_buffer[HEADER_LEN:]
            
            if len(self._recv_buffer) < self._expected_len: break

            message_data = self._recv_buffer[:self._expected_len]
            self._recv_buffer, self._expected_len = self._recv_buffer[self._expected_len:], None

            # 1. 解包
            received_digest = message_data[:DIGEST_LEN]
            encrypted_data_with_iv = message_data[DIGEST_LEN:]

            # 2. 验证完整性
            calculated_digest = hashlib.md5(encrypted_data_with_iv).digest()
            if received_digest != calculated_digest:
                print("错误: 消息摘要不匹配！")
                continue
            
            # 3. 解密 (解密函数内部会处理IV和去除填充)
            try:
                decrypted_data = aes_decrypt(self.key, encrypted_data_with_iv)
                message = deserialize_message(decrypted_data)
                messages.append(message)
            except Exception as e:
                print(f"解密或反序列化失败: {e}")
                continue
        
        return messages

# ===================================================================
# 【新】基于PSK+Salt的握手函数
# ===================================================================
def establish_secure_channel_to_server(ip, port):
    """【客户端】使用PSK+Salt建立安全信道"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        # 1. 客户端生成一个16字节的随机盐
        salt = os.urandom(16)
        
        # 2. 将盐发送给服务器
        sock.sendall(salt)
        
        # 3. 客户端使用盐派生出会话密钥
        session_key = derive_session_key(salt)
        
        print("与服务器的安全信道已建立 (PSK模式)。")
        return SecureChannel(sock, session_key)
        
    except Exception as e:
        print(f"建立安全信道失败: {e}")
        return None

def accept_client_to_secure_channel(client_socket):
    """【服务器端】使用PSK+Salt建立安全信道"""
    try:
        client_socket.setblocking(True)

        # 1. 服务器接收客户端发来的16字节的盐
        salt = recv_all(client_socket, 16)
        if not salt:
            print(f"与 {client_socket.getpeername()} 的连接在接收盐时中断")
            client_socket.close()
            return None
        
        # 2. 服务器使用相同的盐派生出相同的会话密钥
        session_key = derive_session_key(salt)
        
        print(f"与 {client_socket.getpeername()} 的安全信道已建立 (PSK模式)。")
        return SecureChannel(client_socket, session_key)
        
    except Exception as e:
        print(f"接受来自 {client_socket.getpeername()} 的安全信道失败: {e}")
        client_socket.close()
        return None