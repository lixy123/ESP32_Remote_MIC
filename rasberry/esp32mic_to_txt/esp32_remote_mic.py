# -*- coding: utf-8-*-
import snowboydetect
import wave,time
import numpy as np 
import sys,string

from datetime import datetime
import logging
import tempfile
from threading import Thread
import threading
import gc
import urllib,os
import shutil
import logging.handlers
import websocket
import baidu_sound_rec
# 树莓派做客户端，通过websocket连接ESP32做的声音服务端(远程麦克风)
#
# 运行环境: 树莓派3B Linux raspberrypi  
#           理论上其它树莓派都可以运行

# 采集到的声音文件，日志,临时文件都存在放 /myram/
# 此目录我把内存虚拟成了目录，这样速度快，可增加TF卡寿命，不虚拟目录也没关系
# 运行方法
# 1.进入此目录
# 2.执行 python esp32_remote_mic.py 60
#     参数是使用麦克风的最长连接秒数，不带参数是60秒. 目前算法不支持多并发.






#线程方式录音转文字的文字集合,最多同时5线程同时工作,目前只用到1线程,如要多线程,还需要调试
threadResult=[]
threadResult.append("")
threadResult.append("")
threadResult.append("")
threadResult.append("")
threadResult.append("")

#线程方式录音转文字的线程类
class Recorder_Thread(threading.Thread):
    def __init__(self, func, number,no):
        Thread.__init__(self)
        self.func = func
        self.args = number
        self.no=no
 
    def run(self):
        #time.sleep(2)
        threadResult[self.no] = self.func(self.args)
        #print threadResult[self.no]

        
model ="/home/pi/snowboy/snowboy.pmdl"

reload(sys)
sys.setdefaultencoding('utf8')   

time.sleep(3)

logOutFilename='/myram/snowboy.log'  

# choose between DEBUG (log every information) or warning (change of state) or CRITICAL (only error)
#logLevel=logging.DEBUG
logLevel=logging.INFO
#logLevel=logging.CRITICAL


FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#logging.basicConfig(format=FORMAT,filename=logOutFilename,level=logLevel)


# logging初始化工作
# https://www.cnblogs.com/andy9468/p/8378492.html
logging.basicConfig()
myapp_log = logging.getLogger('mylog')
myapp_log.setLevel(logLevel)
 
# 添加TimedRotatingFileHandler
# 定义一个1天换一次log文件的handler
# 保留5个旧log文件
timefilehandler = logging.handlers.TimedRotatingFileHandler(logOutFilename, when='D', interval=1, backupCount=5,encoding="utf-8")
# 设置后缀名称，跟strftime的格式一样
timefilehandler.suffix = "%Y-%m-%d.log"
formatter = logging.Formatter(FORMAT)
timefilehandler.setFormatter(formatter)
myapp_log.addHandler(timefilehandler)


myapp_log.info("程序开始...")

#刚启用录音时，前几秒丢掉
skiptime=0

LIST_MAXLEN=20  #20秒 最长录音10秒, 20秒够用了
list_sound=[None for i in range(LIST_MAXLEN)]
nowindex=0
#录音开始的时间指针
record_startindex=0
record_starttime=0
#1 开始识别
record_sound_status=0
 
detector = snowboydetect.SnowboyDetect(resource_filename="/home/pi/snowboy/resources/common.res",model_str=model)
checklist = []



def getwav():
    wav_fp = wave.open('/myram/snowboy.wav', 'wb')
    wav_fp.setnchannels(1)
    #wav_fp.setsampwidth(pa.get_sample_size(paInt16))
    wav_fp.setsampwidth(2) #2字节 16位
    wav_fp.setframerate(16000)
    #print "索引:",record_startindex, nowindex
    #nowindex这一列数据不要，因为数据是指向下一个，当前的数据还是空
    if (nowindex>record_startindex):   
        list1=    range(record_startindex,nowindex)
        for sound_p in list1:
            #print "get:", sound_p
            frames=list_sound[sound_p]
            if  frames is not None:
                wav_fp.writeframes(''.join(frames))   
        del list1                
    else:    
        list1= range(record_startindex,LIST_MAXLEN)
        for sound_p in list1:
            #print "get:", sound_p
            frames=list_sound[sound_p]
            if  frames is not None:
                wav_fp.writeframes(''.join(frames))   
        del list1                
        list1=range(0,nowindex)                
        for sound_p in list1:
            #print "get:", sound_p
            frames=list_sound[sound_p]
            if  frames is not None:
                wav_fp.writeframes(''.join(frames))   
        del list1                
    wav_fp.close()
    #f.seek(0)
    #return f

#保存到文件的录音声音文件编号
bakfile_index=1
#百度识别数据
def baidu_rec(pa):
    global record_sound_status
    global bakfile_index
    getwav() 
    retstr=""
    try:
        print("文字识别开始")
        retstr=baidu_sound_rec.baidu_rec_fn('/myram/snowboy.wav')
    except Exception as e:
        print "baidu_rec_fn异常:",e
    if len(retstr)>0:
        print "识别出文字:",retstr
        #循环1,2,3保存最近10次有文字识别的wav文件
        if bakfile_index>20:
            bakfile_index=1                    
        shutil.copyfile("/myram/snowboy.wav","/myram/snowboy_"+str(bakfile_index)+".wav")
        retstr= " _" + str(bakfile_index)+".wav " + retstr
        bakfile_index=bakfile_index+1
        
        myapp_log.info("识别:"+retstr + " " + datetime.now().strftime('%m-%d %H:%M'))   
        #提交到中心信息服务端        
        #report_url = "http://192.168.1.20:1990/method=info&txt=20>"+ urllib.quote(retstr);
        #os.system("curl -X GET '"+ report_url+"'" )
        
    #声音识别完成,进入声音检测状态
    record_sound_status=0    
    print ">"    
    return retstr
    
def pop_sound(frames,flag):
    global nowindex,checklist
    if record_sound_status==1:
        if flag==0:
            checklist.append(0)
        else:
            checklist=[]
    if flag==9:
        print "pop_sound",nowindex,flag
    #if flag==1:
    #    print "pop_sound",nowindex,flag
    #print "pop_sound",nowindex,flag
    #print type(frames),len(frames)
    #print frames
    list_sound[nowindex]=frames
    #list_sound_flag[nowindex]=flag
    nowindex=nowindex+1
    if nowindex>=LIST_MAXLEN:        
        nowindex=0
        

        
def snowboy_check(frames):
    ans = detector.RunDetection(frames)
    if ans > 0:
        return 1
    else:
        return 0
        
#默认声音监听总时间: 60秒 
g_all_second=60  
#记录esp32 传回数据的次数 
g_index=1
g_esp32_quit=False  #ESP32 结束标志,当其结束后，main循环也必须马上结束

#最小声音单位是1/4秒，队列
esp32_LIST_MAXLEN=240  #60秒声音信息=240个声音片断
esp32_list_sound=[None for i in range(esp32_LIST_MAXLEN)]
#esp32声音信息指针
esp32_nowindex=0
#已接收到的数据包个数,当达到g_all_second*4时就可以结束应用了
esp32_receive_cnt=0

def esp32_pop_sound(frames):
  global esp32_nowindex,checklist,g_esp32_quit,esp32_receive_cnt
  #如果10秒，此时最高会输出40,结束
  #print("esp32_pop_sound",esp32_nowindex)
  esp32_list_sound[esp32_nowindex]=frames
  #list_sound_flag[nowindex]=flag
  esp32_nowindex=esp32_nowindex+1
  if esp32_nowindex>=esp32_LIST_MAXLEN:        
    esp32_nowindex=0 
    
  esp32_receive_cnt=esp32_receive_cnt+1  
  if esp32_receive_cnt>g_all_second*4:
    g_esp32_quit=True
    print("ESP32 信息正常接收完毕 "+ datetime.now().strftime("%H:%M:%S"))
    thread1.stop()   #关闭本程序，退出 
      
def on_message(ws, message):
  global g_index
  one_len=len(message)
  timestamp= datetime.now()    
  #print(timestamp.strftime("%H:%M:%S"), g_index," Get:",one_len)
  g_index=g_index+1

  #放入队列
  esp32_pop_sound(message)
    
def on_error(ws, error):
  global g_esp32_quit
  print("wssocket: on_error")
  g_esp32_quit=True
  print(error)

    
def on_close(ws):
  print("wssocket: on_close")

def on_open(ws):
  global g_index,g_all_second
  #print("on_open")
  g_index=1
  print("ESP32连接成功 "+ datetime.now().strftime("%H:%M:%S"))    
  ws.send(str(g_all_second)) 
    
#此线程不断接收声音信号到队列
class timer(threading.Thread): #The timer class is derived from the class threading.Thread  
  def __init__(self, num, interval):  
    threading.Thread.__init__(self)  
    self.thread_num = num  
    self.interval = interval  
    self.thread_stop = False  
    self.ws=None 
   
  def run(self):   
    #websocket.enableTrace(True)
    self.ws = websocket.WebSocketApp("ws://192.168.1.100:1331/",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    self.ws.on_open = on_open
    #print("run_forever")
    self.ws.run_forever(ping_timeout=30)
    print("ESP32连接断开")
    
  def stop(self):  
    self.thread_stop = True 
    self.ws.close()      #关闭本程序，退出 

#无限录音
def main():
    global record_sound_status,record_startindex,record_starttime,checklist,skiptime,esp32_nowindex,g_esp32_quit

    #print sens
    detector.SetAudioGain(1)
    detector.SetSensitivity(str(sens))

    
    # number of seconds to allow to establish threshold
    THRESHOLD_TIME = 1
    
    esp32_read_index=0                    
    skiptime=0
    print ">"                          
    try:                              
        #除非键盘中断，不用考虑退出
        loop1=1

        while (True):
            #time.sleep(1)
            #1.录音1秒
            # stores the audio data
            frames = []
            starttime=time.time()
            # calculate the long run average, and thereby the proper threshold
            # 如果连接取数，则读取声音的时间和程序同步，如果等待，同因为缓存原因，读数据会很快           
          
            #读入4次为1秒
            #esp32_read_index不断加1，直到与esp32_nowindex相等
            read_cnt=0
            while True:
                if g_esp32_quit:
                    print("main quit "+ datetime.now().strftime("%H:%M:%S"))
                    return                 
                if esp32_read_index!=esp32_nowindex:
                    #print("read sound",esp32_read_index,read_cnt)
                    read_cnt=read_cnt+1
                    data=esp32_list_sound[esp32_read_index]
                    frames.append(data)
                    esp32_read_index=esp32_read_index+1
                    #到队列尾后转到头
                    if esp32_read_index>=esp32_LIST_MAXLEN:
                        esp32_read_index=0
                    if read_cnt>=4:
                        break
                else:
                    time.sleep(0.05)                 
            #print(datetime.now().strftime("%H:%M:%S"),"read 1 second")  
            
            #语音转文字过程中，读到的声音丢掉
            if record_sound_status==3:
                continue
                
            if skiptime>0:
                skiptime=skiptime-1
                continue   

            #2.检查数据的音量,并放入20秒的音量缓冲区
            #如果发现有动静,转入监听状态
            #join 列表对象转成字符串
            val= snowboy_check(''.join(frames))
            #0 1.000633955
            #print val, time.time()-starttime
            
            #2.检查数据的音量,并放入20秒的音量缓冲区
            #如果发现有动静,转入监听状态
            if val>0:
                pop_sound(frames,1)
                if record_sound_status==0:
                    if nowindex>2:
                        record_startindex=nowindex-3;
                    elif  nowindex==2:
                        record_startindex=LIST_MAXLEN-1;
                    elif nowindex==1:
                        record_startindex=LIST_MAXLEN-2;
                    else:
                        record_startindex=LIST_MAXLEN-3;    
                    record_starttime=time.time()
                    print "record... ",datetime.now().strftime('%m-%d %H:%M')
                    #myapp_log.info("record... "+ datetime.now().strftime('%m-%d %H:%M'))     
                    checklist=[]                    
                    record_sound_status=1 
            else:
                pop_sound(frames,0)
                
            #3.如果在监听状态,检查是否该停止监听
            if record_sound_status==1:
                #超过12秒,停止录音,并进行百度识别
                if time.time()-record_starttime>12 or  len(checklist)>2:
                    #百度识别 3-4秒就可以识别完成
                    print ("声音时长:"+str(int(time.time()-record_starttime))+"秒")
                    #myapp_log.info(str(int(time.time()-record_starttime))+"秒")
                    task1 = Recorder_Thread(baidu_rec, None,0)
                    task1.start()   
                    #进入声音文件识别状态
                    record_sound_status=3                    
                    #skiptime=5
            del frames
            loop1=loop1+1
            #20秒清一次
            if (loop1 % 20==0 and loop1!=0):
                gc.collect()  

            #判断是否应用结束时间到了,只要不在线程转文字状态就退出 
            #增加15秒
            if  g_esp32_quit:
                print("main quit "+ datetime.now().strftime("%H:%M:%S"))
                return           
                    
    except Exception as e:    
        #KeyboardInterrupt    
        print "中断退出:",e
    

    return 0
    
#0.8基本上是有声音就会算唤醒了
sens=0.8
if len(sys.argv) > 1:
    g_all_second= string.atoi(sys.argv[1])    
print("ESP32语音监听将在"+str( g_all_second)+"秒后自动退出 " + datetime.now().strftime("%H:%M:%S"))
thread1 = timer(1, 0.1)
thread1.start() 
#print("thread1.start")
main()
print("app quit " + datetime.now().strftime("%H:%M:%S"))
