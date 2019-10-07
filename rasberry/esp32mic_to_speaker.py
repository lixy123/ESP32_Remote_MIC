import websocket
import _thread as thread
import time,datetime
import threading 
import pyaudio
#import wave
import sys

#本程序是客户端，服务端是esp32 websocket server录音服务器
#客户端使用ws协议连接到录音服务器后，可接收录音服务器上实时发送的声音，相当于连接远程麦克风
#偶尔发现卡顿，与网络连接稳定性有关,如果不需要实时发声，可以直接转录成wav或实时压缩成mp3
#下一步计划:
#1.监听声音流已固定写成: 16位录音,单声道 16000HZ 此声音质量可以用于百度语音文字识别的要求,如果监听用，可考虑降低声音等级，这样可改进声音流卡顿问题
#  每秒32K字节(16000*16/8) =256Kbsp 网络传输压力不太大
#2.没有用到psram,因为考虑到监听需要,录制的声音没必要用到psram转存，如果不监听，可考虑把一部分声音数据缓存到psram中，避免声音数据因为传输处理过快丢失。

CHUNK = 8000
g_lasttime=time.time()
g_starttime=time.time()

g_index=1
#10秒
g_all_second=10 
g_audio=None
g_stream=None

#网速不稳定，声音会卡

class timer(threading.Thread): #The timer class is derived from the class threading.Thread  
  def __init__(self, num, interval):  
    threading.Thread.__init__(self)  
    self.thread_num = num  
    self.interval = interval  
    self.thread_stop = False  
            
  def run(self):   
    global g_starttime,g_lasttime,g_index
    while not self.thread_stop:  
        #每一个声音片断1/4秒，所以乘以4, 因为还有44个字节的wav文件头，所以要加1
        if g_index>g_all_second*4+1:
            g_index=1
            timestamp = datetime.datetime.now() 
            #sleep 确保播放完上一次数据
            time.sleep(3)
            g_stream.stop_stream()   # 停止数据流 
            g_audio.terminate()  # 关闭 PyAudio            
            print(timestamp.strftime("%H:%M:%S"),"file receive end...") 
            ws.close()      #关闭本程序，退出      
        time.sleep(self.interval)
	  
  def stop(self):  
    self.thread_stop = True 
    
def on_message(ws, message):
    global g_lasttime,g_index
    one_len=len(message)

    timestamp= datetime.datetime.now()    
    print(timestamp.strftime("%H:%M:%S"), g_index," Get:",one_len)
    g_index=g_index+1
    g_lasttime=time.time()
    g_stream.write(message)
    
def on_error(ws, error):
    print(error)
    
def on_close(ws):
    thread1.stop()
    print("### closed ###")

def on_open(ws):
    global g_starttime,g_lasttime,g_index,g_audio,g_stream
    print("on_open")
    g_starttime=time.time()
    g_lasttime=time.time()
    g_index=1
    timestamp = datetime.datetime.now()
    print(timestamp.strftime("%H:%M:%S"),"file receive start...")    
    ws.send(str(g_all_second)) 
    #wf=wave.open('/myram/'+fn,'rb')
    g_audio=pyaudio.PyAudio()
    #g_stream=g_audio.open(format=g_audio.get_format_from_width(wf.getsampwidth()),channels=wf.getnchannels(),rate=wf.getframerate(),output=True)
    #存入的wav实例数据是8位，但用vlc显示是16位，原因?
    g_stream=g_audio.open(format=8,channels=1,rate=16000,output=True)
    #print(g_audio.get_format_from_width(wf.getsampwidth()),wf.getnchannels(),wf.getframerate())
    
#实时监听声音秒数
if len(sys.argv)>1:
    g_all_second = int(sys.argv[1])
    
websocket.enableTrace(True)
ws = websocket.WebSocketApp("ws://192.168.1.100:1331/",
                          on_message = on_message,
                          on_error = on_error,
                          on_close = on_close)
ws.on_open = on_open
thread1 = timer(1, 0.1)
thread1.start()

ws.run_forever(ping_timeout=30)
