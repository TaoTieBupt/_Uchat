# Uchat/server/config.py
import os

# --- 存储路径配置 ---
# 所有上传的文件（包括图片）都将保存在这里
UPLOAD_STORAGE_PATH = 'server/uploaded_files/'

def initialize_storage():
    """
    检查并创建所有必需的存储目录。
    这个函数应该在服务器启动时被调用一次。
    """
    if not os.path.exists(UPLOAD_STORAGE_PATH):
        os.makedirs(UPLOAD_STORAGE_PATH)
        print(f"创建了上传目录: {UPLOAD_STORAGE_PATH}")