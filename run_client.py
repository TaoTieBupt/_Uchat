# Uchat/run_client.py
import tkinter as tk
from client.forms.login_form import LoginForm
from common.global_vars import client_memory
# 【新增】
from client.voice_call_manager import VoiceCallManager

def on_app_closing():
    """在主窗口关闭时调用的清理函数"""
    print("应用程序正在关闭，释放资源...")
    # 关闭语音管理器，释放PyAudio资源
    VoiceCallManager().close()
    # 销毁Tkinter根窗口
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    client_memory['tk_root'] = root 
    
    # 【新增】拦截主窗口的关闭事件
    root.protocol("WM_DELETE_WINDOW", on_app_closing)
    
    LoginForm(master=root)
    root.mainloop()