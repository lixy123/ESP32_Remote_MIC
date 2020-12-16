ESP32 as Remote MIC
本项目是参考 https://github.com/paranerd/simplecam 项目的ESP32版本移植，原项目的技术点是可以用网页直接访问终端监听图像和声音.目前只移植了部分声音相关的功能. Arduino for esp32 自带摄像头的例子，已经有了摄像头功能，唯独缺少声音功能。

功能：<br/>
利用本程序，可以使esp32成为远程麦克风, 被树莓派开发的智能音箱系统用作硬件扩展 <br/>
 
示意图:<br/>
<img src= 'https://github.com/lixy123/ESP32_Remote_MIC/blob/master/ESP32_MIC.jpg?raw=true' />
<br/>
硬件: 以下三种方案任选一种<br/>
1.ESP32+ INMP441(I2S麦克风模块)<br/>
   推荐硬件：<br/>
   A.普通ESP32+INMP441 成本低，连接较臃肿<br/>
/* ESP32+INMP441(I2S麦克风模块) 接线定义见I2S.h <br/>
SCK IO14<br/>
WS  IO27<br/>
SD  IO2<br/>
L/R GND<br/>
*/<br/>
   B.ESP-EYE 很小巧，隐蔽性好,成本较高 <br/>
   C.TTGO T-Camera Plus ESP32 体积大了些，不隐蔽<br/>
   D.TTGO T-Watch 带MIC扩展板 成本高,隐蔽性好,有些浪费硬件 <br/>
   
2.树莓派<br/>
   推荐用树莓派3B, 不推荐树莓派4B, 4B发热量大，用起来要加风扇，风扇噪音影响录音效果

使用场景：<br/>
   单元楼大门声音对话，监听防盗, 作为智能音箱远程附件等

使用方法：<br/>
场景1:<br/>
   直接用网页浏览器访问监听esp32的MIC,耳机监听到声音<br/>
1. 服务端<br/>
  esp32_remote_mic2 <br/> 
  用arduino工具烧录到esp32<br/>
  
2. 客户端 <br/>
  通过网页浏览器访问地址 http://192.168.1.100 实时收听声音<br/>
  未设计成支持多并发，同一时间只允许一个客户端<br/>
  注: 必须支持html5的浏览器,  PC电脑不支持IE, 需要用chrome浏览器, 安卓,苹果手机内置的浏览器基本上都是html5.可在局域网直接访问此ip<BR/>
  测试注: 如果电脑播放声音为杂音, 电脑控制面板找到声音设置,将声音播放格式改成48000hz<BR/>
 <br/>
 
 
场景2:<br/>
   用树莓派获取esp32上的MIC声音信号, 监听,播放,存储,甚至实时采集后识别出文字等<br/>
1. 服务端<br/>
  esp32_remote_mic  初级版<br/>
  创建一个静态固定IP的Websocket服务器等待客户端. 当收到客户端发来的文字数据秒数后，在指定秒数内把声音信号发回客户端。<br/>
  未设计成支持多并发，同一时间只允许一个客户端<br/>
  用arduino工具烧录到esp32<br/>
 
2. 客户端 <br/>
  树莓派接收esp32的mic信号, 协议使用Websocket
  预安装sudo pip install websocket_client <br/>
  文件拷入树莓派目录 <br/>
  A. esp32mic_to_file.py <br/>
     执行: python esp32mic_to_file.py<br/>
     连接ESP32远程麦克风，声音文件输出至文件。<br/>
  B. esp32mic_to_speaker.py<br/>
     执行: python esp32mic_to_speaker.py<br/>
     连接ESP32远程麦克风，声音文件输出树莓派的扬声器。<br/>
  C. esp32mic_to_txt (用到了snowboy库，辅助文件较多) <br/>
     执行: 先进入子目录，执行python esp32_remote_mic.py <br/>
     默认60秒,带参数可延长时间.  <br/>
     连接ESP32远程麦克风，声音数据实时由树莓派处理，当检测到有人说话时识别出声音中的文字<br/>
  注意修改路由器连接密码以及IP地址,文件引用地址.

