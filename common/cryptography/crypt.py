# Uchat/common/cryptography/crypt.py
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 预共享密钥 (Pre-Shared Key): 这是一个硬编码在客户端和服务器中的秘密。
# 为了简化，我们直接在这里定义它。
PRE_SHARED_KEY = b'a-very-secret-preshared-key-for-uchat-2024'

def derive_session_key(salt):
    """
    【新】使用预共享密钥和盐(salt)仅派生出会话密钥。
    我们不再派生固定的IV。
    使用 SHA256 哈希函数进行派生。
    """
    # 将预共享密钥和盐拼接
    combined = PRE_SHARED_KEY + salt
    # 计算哈希值
    hashed = hashlib.sha256(combined).digest()
    # 将哈希值的前16字节作为密钥 (AES-128)
    key = hashed[:16]
    return key

def aes_encrypt(key, plaintext):
    """
    【新】使用 pycryptodome 的 AES-CBC 模式加密数据。
    - plaintext: 需要加密的字节串。
    - 返回值: iv + ciphertext
    """
    # 1. 每次加密都生成一个新的、随机的IV
    iv = os.urandom(16)
    # 2. 创建 AES 加密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # 3. 对明文进行填充 (PKCS7)，然后加密
    padded_plaintext = pad(plaintext, AES.block_size)
    ciphertext = cipher.encrypt(padded_plaintext)
    # 4. 【重要】将 IV 和密文拼接在一起返回
    return iv + ciphertext

def aes_decrypt(key, iv_and_ciphertext):
    """
    【新】使用 pycryptodome 的 AES-CBC 模式解密数据。
    - iv_and_ciphertext: 包含IV和密文的字节串。
    """
    # 1. 从接收到的数据中分离出 IV 和密文
    iv = iv_and_ciphertext[:16]
    ciphertext = iv_and_ciphertext[16:]
    # 2. 创建 AES 解密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # 3. 解密数据
    decrypted_padded = cipher.decrypt(ciphertext)
    # 4. 去除填充，得到原始明文
    plaintext = unpad(decrypted_padded, AES.block_size)
    return plaintext

# 【新增】os 库是生成随机IV所必需的
import os