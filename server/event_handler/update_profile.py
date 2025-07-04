# server/event_handler/update_profile.py
import os
import uuid
from server import memory
from server.util import database as db
from common.message import MessageType
from server.config import UPLOAD_STORAGE_PATH
from server.broadcast import broadcast_profile_update # 我们将创建一个新的广播函数

def run(sc, parameters):
    user_id = memory.sc_to_user_id.get(sc)
    if not user_id: return

    updated = False
    response = {'success': False, 'reason': ''}
    
    # 更新个性签名
    if 'signature' in parameters:
        signature = parameters['signature']
        if len(signature) <= 100:
            db.update_user_signature(user_id, signature)
            updated = True
            print(f"用户 {user_id} 更新了签名。")
        else:
            response['reason'] = '签名过长。'
            sc.send(MessageType.profile_update_result, response)
            return

    # 更新头像
    if 'avatar_data' in parameters:
        avatar_data = parameters['avatar_data']
        if isinstance(avatar_data, bytes) and len(avatar_data) < 2 * 1024 * 1024: # 限制2MB
            ext = '.png' # 简单处理，都视为png
            server_filename = f"{uuid.uuid4()}{ext}"
            filepath = os.path.join(UPLOAD_STORAGE_PATH, server_filename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(avatar_data)
                
                # 删除旧头像（可选，防止磁盘空间无限增长）
                old_avatar = db.get_user_by_id(user_id)['avatar']
                if old_avatar and old_avatar != 'default.png':
                    old_filepath = os.path.join(UPLOAD_STORAGE_PATH, old_avatar)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)

                db.update_user_avatar(user_id, server_filename)
                updated = True
                print(f"用户 {user_id} 更新了头像: {server_filename}")
            except Exception as e:
                print(f"保存头像失败: {e}")
                response['reason'] = '服务器保存头像失败。'
                sc.send(MessageType.profile_update_result, response)
                return
        else:
            response['reason'] = '头像数据无效或过大。'
            sc.send(MessageType.profile_update_result, response)
            return
            
    if updated:
        response['success'] = True
        # 通知客户端更新成功，并附带最新的个人信息
        updated_user_info = db.get_user_by_id(user_id)
        response['profile'] = dict(updated_user_info)
        sc.send(MessageType.profile_update_result, response)
        
        # 广播通知所有好友，我的资料更新了
        broadcast_profile_update(user_id, {'avatar': updated_user_info['avatar']})
    else:
        response['reason'] = '没有提供任何要更新的信息。'
        sc.send(MessageType.profile_update_result, response)