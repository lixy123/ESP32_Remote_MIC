#!/usr/bin/python3
# -*- coding: utf-8 -*-
import snowboydecoder
import sys
import signal



from pyaudio import PyAudio, paInt16 
import numpy as np 
from datetime import datetime 
import wave

interrupted = False

class recoder:
    NUM_SAMPLES = 2000      #pyaudio内置缓冲大小
    SAMPLING_RATE = 8000    #取样频率
    LEVEL = 500         #声音保存的阈值
    COUNT_NUM = 20      #NUM_SAMPLES个取样之内出现COUNT_NUM个大于LEVEL的取样则记录声音
    SAVE_LENGTH = 8         #声音记录的最小长度：SAVE_LENGTH * NUM_SAMPLES 个取样
    TIME_COUNT = 10     #录音时间，单位s

    Voice_String = []
    
    def __init__(self,sec):
        self.TIME_COUNT=sec

    def savewav(self,filename):
        wf = wave.open(filename, 'wb') 
        wf.setnchannels(1) 
        wf.setsampwidth(2) 
        wf.setframerate(self.SAMPLING_RATE) 
        wf.writeframes(np.array(self.Voice_String).tostring()) 
        # wf.writeframes(self.Voice_String.decode())
        wf.close() 

    def recoder(self):
        pa = PyAudio() 
        stream = pa.open(format=paInt16, channels=1, rate=self.SAMPLING_RATE, input=True, 
            frames_per_buffer=self.NUM_SAMPLES) 
        save_count = 0 
        save_buffer = [] 
        time_count = self.TIME_COUNT

        while True:
            time_count -= 1
            # print time_count
            # 读入NUM_SAMPLES个取样
            string_audio_data = stream.read(self.NUM_SAMPLES) 
            # 将读入的数据转换为数组
            audio_data = np.fromstring(string_audio_data, dtype=np.short)
            # 计算大于LEVEL的取样的个数
            large_sample_count = np.sum( audio_data > self.LEVEL )
            #print(np.max(audio_data))
            # 如果个数大于COUNT_NUM，则至少保存SAVE_LENGTH个块
            if large_sample_count > self.COUNT_NUM:
                save_count = self.SAVE_LENGTH 
            else: 
                save_count -= 1

            if save_count < 0:
                save_count = 0 

            if save_count > 0 : 
            # 将要保存的数据存放到save_buffer中
                #print  save_count > 0 and time_count >0
                save_buffer.append( string_audio_data ) 
            else: 
            #print save_buffer
            # 将save_buffer中的数据写入WAV文件，WAV文件的文件名是保存的时刻
                #print "debug"
                if len(save_buffer) > 0 : 
                    self.Voice_String = save_buffer
                    save_buffer = [] 
                    #print("Recode a piece of  voice successfully!")
                    return True
            if time_count==0: 
                if len(save_buffer)>0:
                    self.Voice_String = save_buffer
                    save_buffer = [] 
                    #print("Recode a piece of  voice successfully!")
                    return True
                else:
                    return False

ctrl_c=False
def signal_handler(signal, frame):
    global interrupted,ctrl_c
    ctrl_c=True
    interrupted = True

r = recoder(10)

record_flag=0
def snowboy_callback():
    global record_flag,interrupted,record_flag
    if (record_flag==1):
        print ("sorry, no record...")
        return
    
    record_flag=1    
    interrupted=True
    detector.terminate()    
    #print ("detected snowboy at " + datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))   
    
    file_name = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")+'.wav'
    print("Recode begin...10s... "+ file_name)
    r.recoder()
    r.savewav(file_name) 
    print("Recode end...10s... " + file_name)      


def interrupt_callback():
    global interrupted
    return interrupted

model ="snowboy.pmdl"

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

loop1=0;
while True:
    interrupted=False
    record_flag=0
    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
    print('Listening... Press Ctrl+C to exit')
    detector.start(detected_callback=snowboy_callback,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)
    if (record_flag==0):
        detector.terminate()               
    print("loop...")
    loop1=loop1+1
    if (loop1==10 or ctrl_c):
        break



