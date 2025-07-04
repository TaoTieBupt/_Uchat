# Uchat/server/event_handler/get_moments.py
import os
import json
from server import memory
from server.util import database as db
from common.message import MessageType

IMAGE_STORAGE_PATH = 'server/uploaded_images/'

def run(sc, parameters):
    """
    【修改版】处理获取好友动态列表的请求。
    职责：查询数据库，并【主动读取图片文件】，将图片二进制数据一起返回。
    """
    print("\n--- [服务器] 开始处理 get_moments 请求 (包含图片数据) ---")
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id:
        # ... (错误处理不变)
        return

    try:
        # 1. 从数据库获取基础动态数据（包括image_filename）
        moments_data_from_db = db.get_friends_moments(user_id)
        
        # 2. 【核心修改】遍历每条动态，如果有关联的图片，则读取并添加到数据中
        full_moments_list = []
        for moment in moments_data_from_db:
            moment_dict = dict(moment) # 将数据库行转换为字典
            image_filename = moment_dict.get('image_filename')
            
            if image_filename:
                filepath = os.path.join(IMAGE_STORAGE_PATH, image_filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'rb') as f:
                            # 将图片二进制数据添加到字典中
                            moment_dict['image_data'] = f.read()
                    except Exception as e:
                        print(f"读取图片文件 {filepath} 失败: {e}")
                        # 如果读取失败，可以不传这个字段，或传一个错误标记
                        moment_dict['image_data'] = None
                else:
                    print(f"警告: 数据库记录了图片 {image_filename}，但文件不存在。")
            
            full_moments_list.append(moment_dict)
        
        print(f"准备向客户端发送包含 {len(full_moments_list)} 条完整动态（含图片）的 moments_list 消息...")
        sc.send(MessageType.moments_list, {'moments': full_moments_list})
        print("moments_list 消息已发送。")

    except Exception as e:
        print(f"异常: 获取动态列表失败: {e}")
        import traceback
        traceback.print_exc()
        sc.send(MessageType.moments_list, {'moments': []})
    
    print("--- [服务器] 结束处理 get_moments 请求 ---\n")