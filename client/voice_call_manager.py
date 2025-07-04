# Uchat/client/voice_call_manager.py
import pyaudio
# import opuslib  <-- 【移除】不再需要导入 opuslib
import threading
import time
from common.global_vars import client_memory
from common.message import MessageType
from common.util.socket_listener import add_listener, remove_listener

# 音频参数（低音质配置）
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000 # 采样率
FRAME_DURATION = 20  # ms
FRAME_SIZE = int(RATE * FRAME_DURATION / 1000) # 16000 * 20 / 1000 = 320
# PCM数据大小 = FRAME_SIZE * CHANNELS * BYTES_PER_SAMPLE = 320 * 1 * 2 = 640 字节
# 每秒带宽 = 640 * (1000 / 20) = 32000 字节/秒 ≈ 256 kbps (相对较高)
BUFFER_SIZE = FRAME_SIZE * 10

class VoiceCallManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VoiceCallManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.p = pyaudio.PyAudio()
        # 【移除】不再需要 encoder 和 decoder
        # self.encoder = opuslib.Encoder(RATE, CHANNELS, opuslib.APPLICATION_VOIP)
        # self.decoder = opuslib.Decoder(RATE, CHANNELS)
        
        self.stream_out = None
        self.stream_in = None
        
        self.is_in_call = False
        self.other_party_id = None
        self.audio_thread = None
        self.stop_audio_thread = threading.Event()
        
        self.ui_update_callback = None
        
        add_listener(self.socket_listener)
        
    def set_ui_callback(self, callback):
        self.ui_update_callback = callback
        
    def start_call(self, callee_id):
        if self.is_in_call:
            self._update_ui("错误: 已在通话中")
            return
            
        self._update_ui(f"正在呼叫...")
        client_memory['sc'].send(MessageType.voice_call_request, {'callee_id': callee_id})
        self.other_party_id = callee_id
    
    def answer_call(self, caller_id, accepted=True):
        client_memory['sc'].send(MessageType.voice_call_response, {
            'caller_id': caller_id,
            'accepted': accepted
        })
        if accepted:
            self._initiate_call_session(caller_id)
        else:
            self._update_ui("已拒接")
            
    def hangup_call(self):
        if not self.is_in_call:
            return
            
        client_memory['sc'].send(MessageType.voice_call_hangup, {'other_party_id': self.other_party_id})
        self._end_call_session("已挂断")

    def _initiate_call_session(self, other_party_id):
        if self.is_in_call: return
        
        print("初始化通话会话 (无编码)...")
        self.is_in_call = True
        self.other_party_id = other_party_id
        
        try:
            self.stream_out = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=BUFFER_SIZE)
            self.stream_in = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=FRAME_SIZE)
        except Exception as e:
            print(f"打开音频流失败: {e}")
            self._end_call_session("音频设备错误")
            return

        self.stop_audio_thread.clear()
        self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.audio_thread.start()
        
        self._update_ui(f"通话中...")

    def _end_call_session(self, reason="通话已结束"):
        if not self.is_in_call: return
        
        print("结束通话会话...")
        self.is_in_call = False
        self.stop_audio_thread.set()
        
        if self.audio_thread:
            self.audio_thread.join(timeout=1)
        
        if self.stream_in:
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.stream_in = None
            
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.stream_out = None
        
        self._update_ui(reason)
        self.other_party_id = None

    def _audio_loop(self):
        """【核心修改】音频收发循环 (无编码)"""
        while not self.stop_audio_thread.is_set():
            try:
                # 1. 从麦克风录制原始PCM音频数据
                pcm_data = self.stream_in.read(FRAME_SIZE, exception_on_overflow=False)
                
                # 2. 【移除】不再需要编码
                # opus_data = self.encoder.encode(pcm_data, FRAME_SIZE)
                
                # 3. 直接发送原始PCM数据到服务器
                client_memory['sc'].send(MessageType.voice_data, {
                    'to_id': self.other_party_id,
                    'data': pcm_data  # 直接发送 pcm_data
                })
            except IOError as e:
                # 捕获可能的音频设备读取错误
                print(f"音频读取/发送错误: {e}")
                # 可以在这里触发通话结束
                self.hangup_call()
                break
            except Exception as e:
                print(f"音频线程未知错误: {e}")
                break

    def _play_audio(self, pcm_data):
        """【核心修改】播放音频 (无解码)"""
        if not self.is_in_call or not self.stream_out:
            return
        try:
            # 1. 【移除】不再需要解码
            # pcm_data = self.decoder.decode(opus_data, FRAME_SIZE)
            
            # 2. 直接将收到的PCM数据写入播放流
            self.stream_out.write(pcm_data)
        except IOError as e:
            print(f"音频播放错误: {e}")
            # 同样可以触发通话结束
            self.hangup_call()
        except Exception as e:
            print(f"音频播放未知错误: {e}")


    def socket_listener(self, data):
        """处理与语音通话相关的信令和数据"""
        msg_type = data.get('type')
        params = data.get('parameters', {})
        
        # 【修改】将 voice_data 的处理移到最前面，因为它最频繁
        if msg_type == MessageType.voice_data:
            # 只处理来自通话对象的数据
            if self.is_in_call and params.get('from_id') == self.other_party_id:
                self._play_audio(params.get('data'))
            return # 处理完直接返回，不继续往下判断

        # 处理信令
        if msg_type == MessageType.incoming_voice_call:
            caller_id = params['caller_id']
            caller_name = params['caller_name']
            if self.ui_update_callback:
                self.ui_update_callback("incoming", {'id': caller_id, 'name': caller_name})

        elif msg_type == MessageType.voice_call_answered:
            callee_id = params['callee_id']
            self._initiate_call_session(callee_id)

        elif msg_type == MessageType.voice_call_rejected:
            self._end_call_session(params.get('reason', '对方已拒接'))
            
        elif msg_type == MessageType.voice_call_ended:
            self._end_call_session(params.get('reason', '对方已挂断'))
            
    def _update_ui(self, status, data=None):
        if self.ui_update_callback:
            if client_memory.get('tk_root') and client_memory['tk_root'].winfo_exists():
                client_memory['tk_root'].after(0, self.ui_update_callback, status, data)
            
    def close(self):
        """在程序退出时调用，释放资源"""
        if self.is_in_call:
            self.hangup_call()
        self.p.terminate()
        remove_listener(self.socket_listener)
        VoiceCallManager._instance = None