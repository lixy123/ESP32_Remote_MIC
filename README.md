# ESP32_Remote_MIC
ESP32 as Remote MIC
本项目是参考 https://github.com/paranerd/simplecam 项目的ESP32版本移植，原项目的技术点是可以用网页直接访问终端监听图像和声音.目前只移植了部分声音相关的功能. 视频功能ESP32-CAM自身有带例子，如果视频声音一起传输性能不够，就没有一块移植上.

功能：<br/>
利用本程序，可以使esp32成为远程麦克风,树莓派运行Python连接此麦克风可监听到esp32的实时录音

硬件:<br/>
1.ESP32+ INMP441(I2S麦克风模块)<br/>
/* ESP32+INMP441(I2S麦克风模块) 接线定义见I2S.h <br/>
SCK IO14<br/>
WS  IO27<br/>
SD  IO2<br/>
L/R GND<br/>
*/<br/>
2.树莓派<br/>

使用场景：<br/>
单元楼大门声音对话，监听防盗等

使用方法：<br/>
1. 服务端<br/>
  A.esp32_remote_mic  <br/>
  本程序很简单，创建一个固定IP的Websocket服务器，当收到客户端发来的文字数据秒数，就在接连的秒数内把声音信号发回客户端。没考虑并发，一次同时只服务一个客户端。
  用arduino工具烧录到esp32<br/>
  B.esp32_remote_mic2 <br/>
  本程序较复杂，除了创建Websocket服务器，兼容上一版本的功能，另外还创建了Web服务器，客户端用网页浏览器访问后可以通过浏览器直接听到声音。此程序有bug,最终完全无声，后来经过改进已经能发出声音，但混杂有较大杂音，正在恶补web Audio实现pcm音频数据播放的知识。如果有高手可拿去修改. (注:此程序有bug,还不可用) <br/>
2. 客户端<br/>
  A. esp32mic_to_file.py <br/>
     执行: python esp32mic_to_file.py<br/>
     连接ESP32远程麦克风，声音文件输出至文件。<br/>
  B. esp32mic_to_speaker.py<br/>
     执行: python esp32mic_to_speaker.py<br/>
     连接ESP32远程麦克风，声音文件输出树莓派的扬声器。<br/>
  C. esp32mic_to_txt (用到了snowboy库，辅助文件较多) <br/>
     执行: python esp32_remote_mic.py <br/>
     默认60秒,带参数可延长时间.  <br/>
     连接ESP32远程麦克风，声音数据实时由树莓派处理，当检测到有人说话时识别出声音中的文字<br/>
  注意修改路由器连接密码以及IP地址,文件引用地址.

