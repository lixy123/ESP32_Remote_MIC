# -*- coding: utf-8-*-
import requests
import urllib
import json
import base64
import wave
from pydub import AudioSegment
import os,sys
import time, datetime



class BaiduRest:
    def __init__(self, cu_id, api_key, api_secert):
        # token认证的url
        self.token_url = "http://openapi.baidu.com/oauth/2.0/token"
        # 语音合成的resturl
        self.getvoice_url = "http://tsn.baidu.com/text2audio"
        # 语音识别的resturl
        self.upvoice_url = 'http://vop.baidu.com/server_api'

        self.cu_id = cu_id
        self.getToken(api_key, api_secert)
        self.api_key=api_key
        self.api_secert=api_secert
        self.last_getToken=datetime.datetime.now()
        return

    def check_getToken(self):
        # 计算token是否过期 官方说明一个月，这里保守28天
        endtime = datetime.datetime.now()
        if (endtime - self.last_getToken).days >= 28:
            print("re_getToken")
            self.getToken(self.api_key, self.api_secert)
            self.last_getToken=datetime.datetime.now()
                    
    def getToken(self, api_key, api_secert):
        # 1.获取token
        token_url = self.token_url 
        params = urllib.urlencode({'grant_type': 'client_credentials',
                                   'client_id': api_key,
                                   'client_secret': api_secert})
        print("token_url="+token_url)
        r_str = requests.get(token_url, params=params)
        #print(r_str)
        token_data = r_str.json()
        #print(token_data)
        self.token_str = token_data['access_token']
        print(self.token_str)
        pass

    def getVoice(self, text, filename):
        self.check_getToken()
        # 2. 向Rest接口提交数据
        #get_url = self.getvoice_url % (urllib.p1arse.quote(text), self.cu_id, self.token_str)
        query = {'tex': text,
                 'lan': 'zh',
                 'tok': self.token_str,
                 'ctp': 1,
                 'cuid': self.cu_id
                 }
                 
        
        voice_data = requests.post(self.getvoice_url,
                          data=query,
                          headers={'content-type': 'application/json'})
        print("getVoice ok\n");
        #voice_data = requests.get(get_url)
        print("filelen="+str(len(voice_data.content)))
        # 3.处理返回数据
        voice_fp = open(filename,'wb+')
        voice_fp.write(voice_data.content)
        voice_fp.close()
        pass

    def getVoice_wav(self, text, filename):
        self.check_getToken()
        # 2. 向Rest接口提交数据
        #get_url = self.getvoice_url % (urllib.p1arse.quote(text), self.cu_id, self.token_str)
        query = {'tex': text,
                 'lan': 'zh',
                 'tok': self.token_str,
                 'ctp': 1,
                 'cuid': self.cu_id,
                 'aue': 6  # 4为pcm-16k；5为pcm-8k；6为wav 16k16位带文件头 pcm不带wav头
                 }
                 
        
        voice_data = requests.post(self.getvoice_url,
                          data=query,
                          headers={'content-type': 'application/json'})
        print("getVoice ok\n");
        #voice_data = requests.get(get_url)
        print("filelen="+str(len(voice_data.content)))
        # 3.处理返回数据
        voice_fp = open(filename,'wb+')
        voice_fp.write(voice_data.content)
        voice_fp.close()
        pass
        
    
    def getText_bydata(self, audio):
        self.check_getToken()
        
        data = {}
        # 语音的一些参数
        data['format'] = 'wav'
       
        data['channel'] = 1  #双通道
        data['cuid'] = self.cu_id
        data['token'] = self.token_str
        base_data = base64.b64encode(audio)
        data['rate'] = 16000
        data['speech'] = base_data
        data['len'] =len(audio)
        #print (str(frame_rate))
        post_data = json.dumps(data)
        r_data = requests.post(self.upvoice_url,data=post_data,headers={'content-type': 'application/json'})
        # 3.处理返回数据
        #print("post ok")
        #print(r_data)
        r_data_json=r_data.json()
        #print(r_data_json)
        if (r_data_json["err_no"]==0):
            rec_text=r_data_json['result'][0].encode('utf-8')
            #print(rec_text)
            return rec_text
        else:
            return ""
            
    def getText(self, filename):
        self.check_getToken()
        wav_file = wave.open(filename, 'rb')
        data = {}
        # 语音的一些参数
        data['format'] = 'wav'
       
        data['channel'] = 1  #双通道
        data['cuid'] = self.cu_id
        data['token'] = self.token_str
        n_frames = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        audio = wav_file.readframes(n_frames)
        base_data = base64.b64encode(audio)
        data['rate'] = frame_rate
#        wav_fp = open(filename,'rb')
#        voice_data = wav_fp.read()
#        data['len'] = len(voice_data)
        data['speech'] = base_data
        data['len'] =len(audio)
        #print (str(frame_rate))
        post_data = json.dumps(data)
        wav_file.close()
        r_data = requests.post(self.upvoice_url,data=post_data,headers={'content-type': 'application/json'})
        # 3.处理返回数据
        #print("post ok")
        #print(r_data)
        r_data_json=r_data.json()
        #print(r_data_json)
        if (r_data_json["err_no"]==0):
            rec_text=r_data_json['result'][0].encode('utf-8')
            #print(rec_text)
            return rec_text
        else:
            return ""
 
# 需要到如下网址:百度语音服务 注册并获得用于语音服务需要的api_key,api_secert
# 以下变量是随意写的,需要替换成可用的key
# http://yuyin.baidu.com/
api_key = "@@@@@@@@@@@@@@"
api_secert = "@@@@@@@@@@@@@@"
# 初始化
bdr = BaiduRest("test_python", api_key, api_secert)
print("BaiduRest start...")
     
def esp32_baidu_token():
    bdr.check_getToken()
    return bdr.token_str
    
def esp32_baidu_mp3(txt_baidu):
    bdr.getVoice(txt_baidu, "/home/pi/esp32_tmp.mp3")

def wav_wav_8k(fn_wav,new_fn):
    sound = AudioSegment.from_file(fn_wav,format="wav")
    sound= sound.set_sample_width(1).set_frame_rate(8000)
    sound.export(new_fn, format="wav")
    
def mp3_wav_8k(fn_wav,new_fn):
    sound = AudioSegment.from_file(fn_wav,format="mp3")
    sound= sound.set_sample_width(1).set_frame_rate(8000)
    sound.export(new_fn, format="wav")

#https://github.com/jiaaro/pydub/blob/master/API.markdown
def sound_louder(fn_type, fn,new_fn, louder):
    sound = AudioSegment.from_file(fn,format=fn_type)
    sound_louder=sound+louder
    sound_louder.export(new_fn, format=fn_type)
    
def mp3_wav(fn_mp3,fn_wav):
    sound = AudioSegment.from_mp3(fn_mp3)
    sound.export(fn_wav, format="wav")
    
def amr_mp3(fn_amr,fn_wav):
    sound = AudioSegment.from_file(fn_amr,format="amr")
    sound.export(fn_wav, format="mp3")

def baidu_rec_ram(fn):
    # 将字符串语音合成并保存为out.mp3
    #bdr.getVoice("你好北京邮电大学!", "/home/pi/out.mp3")
    # 识别test.wav语音内容并显示
    #注意：生成是mp3,转换需要是wav  
    return (bdr.getText("/myram/"+ fn))
   
def baidu_rec_fn(f):
    return (bdr.getText(f))
    
def baidu_rec(fn):
    #print "baidu_rec",fn
    # 将字符串语音合成并保存为out.mp3
    #bdr.getVoice("你好北京邮电大学!", "/home/pi/out.mp3")
    # 识别test.wav语音内容并显示
    #注意：生成是mp3,转换需要是wav  
    return (bdr.getText("/home/pi/"+ fn))
    
def baidu_wav_text(txt_baidu):
    bdr.getVoice_wav(txt_baidu, "/home/pi/tmp1.wav")
    
def baidu_text(txt_baidu):
    # 将字符串语音合成并保存为out.mp3
    #bdr.getVoice("你好北京邮电大学!", "/home/pi/out.mp3")
    # 识别test.wav语音内容并显示
    #注意：生成是mp3,转换需要是wav    
    bdr.getVoice(txt_baidu, "/home/pi/esp32_s.mp3")
    mp3_wav("/home/pi/esp32_s.mp3","/home/pi/esp32_s.wav")

def baidu_text_player(txt_baidu):
    # 将字符串语音合成并保存为out.mp3 并播放
    #bdr.getVoice("你好北京邮电大学!", "/home/pi/out.mp3")
    # 识别test.wav语音内容并显示
    #注意：生成是mp3,转换需要是wav   
    print("语音生成 baidu_out.mp3")    
    bdr.getVoice(txt_baidu, "/home/pi/baidu_out.mp3")
    print("mpg123 baidu_out.mp3")
    os.system("mpg123 '/home/pi/baidu_out.mp3'")
    
#wav_wav_8k('/home/pi/tmp1.wav','/home/pi/esp328k.wav')
#baidu_wav_text("今天星期三,今天的天气真不错")
#ret=baidu_rec("esp32_rec.wav")
#print(ret)
#amr_louder("weixin.wav","new_weixin.wav",20)
#amr_wav("weixin.wav","new_weixin.mp3")
#sound_louder("new_weixin.mp3","new_weixin1.mp3",3)
#sound_louder("new_weixin.mp3","new_weixin2.mp3",5)
#sound_louder("new_weixin.mp3","new_weixin3.mp3",7)
#print("quit")
