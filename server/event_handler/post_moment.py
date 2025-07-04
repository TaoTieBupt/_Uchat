# Uchat/server/event_handler/post_moment.py
import time
import os
import uuid
from server import memory
from server.util import database as db
from common.message import MessageType

IMAGE_STORAGE_PATH = 'server/uploaded_images/'
if not os.path.exists(IMAGE_STORAGE_PATH):
    os.makedirs(IMAGE_STORAGE_PATH)

def run(sc, parameters):
    """【修改版】处理用户发布新动态的请求，支持图片"""
    print("\n--- [服务器] 开始处理 post_moment 请求 ---")
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id:
        # ... (错误处理不变)
        return

    content = parameters.get('content', '') # 文本内容现在是可选的
    image_data = parameters.get('image_data') # 获取图片二进制数据
    
    # 校验：文本和图片不能都为空
    if not content.strip() and not image_data:
        sc.send(MessageType.post_moment_result, {'success': False, 'reason': '动态内容和图片不能都为空'})
        return
        
    image_filename = None
    # 如果有图片数据，则保存图片
    if image_data:
        if not isinstance(image_data, bytes):
            sc.send(MessageType.post_moment_result, {'success': False, 'reason': '图片数据格式错误'})
            return
        
        image_filename = f"{uuid.uuid4()}.png" # 假设都转为png
        filepath = os.path.join(IMAGE_STORAGE_PATH, image_filename)
        try:
            with open(filepath, 'wb') as f:
                f.write(image_data)
            print(f"图片已保存: {filepath}")
        except Exception as e:
            print(f"保存动态图片失败: {e}")
            sc.send(MessageType.post_moment_result, {'success': False, 'reason': '服务器保存图片失败'})
            return

    # 将动态信息写入数据库
    try:
        moment_id = db.create_moment(user_id, content, time.time(), image_filename)
        if moment_id:
            sc.send(MessageType.post_moment_result, {'success': True})
            print(f"用户 {user_id} 发布了一条新动态 (ID: {moment_id})")
        else:
            raise Exception("数据库插入失败")
    except Exception as e:
        print(f"发布动态到数据库失败: {e}")
        sc.send(MessageType.post_moment_result, {'success': False, 'reason': '服务器内部错误'})
    
    print("--- [服务器] 结束处理 post_moment 请求 ---\n")