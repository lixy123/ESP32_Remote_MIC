import websocket
import _thread as thread
import time,datetime
import threading 


g_lasttime=time.time()
g_starttime=time.time()
g_file= None 
g_index=1
#10秒
g_all_second=10 

fn="esp32.wav"

class timer(threading.Thread): #The timer class is derived from the class threading.Thread  
  def __init__(self, num, interval):  
    threading.Thread.__init__(self)  
    self.thread_num = num  
    self.interval = interval  
    self.thread_stop = False  
            
  def run(self):   
    global g_starttime,g_lasttime,g_index
    #平均一张图片用时0.2秒, 存入处理一张图片0.02秒
    #10张缓存用2秒
    while not self.thread_stop:  
        if g_index>g_all_second*4+1:
            g_index=1
            timestamp = datetime.datetime.now() 
            g_file.close()    
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
    g_file.write(message);
    
def on_error(ws, error):
    print(error)
    #time.sleep(10)  # 延时十秒，预防假死
    #Start() # 重连
    
def on_close(ws):
    thread1.stop()
    print("### closed ###")

def on_open(ws):
    global g_starttime,g_lasttime,g_index,g_file
    print("on_open")
    g_starttime=time.time()
    g_lasttime=time.time()
    g_file=open('/myram/'+fn, 'wb')   
    g_index=1
    timestamp = datetime.datetime.now()
    print(timestamp.strftime("%H:%M:%S"),"file receive start...")    
    ws.send(str(g_all_second)) 

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