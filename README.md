ESP32 as Remote MIC

<b>一.功能：</b><br/>
本应用让esp32成为网页控制的远程麦克风<br/>
项目参考 https://github.com/paranerd/simplecam 项目进行的ESP32版本移植，原项目可以通过网页监听树莓派上传入的图像和声音. <br/>
esp32也能实现图像声音传输功能,目前只开发了声音功能.<br/>
使用场景：单元楼大门声音对话，监听防盗, 作为智能音箱远程附件等<br/>

<b>二.硬件:</b> <br/>
 ESP32+ INMP441(I2S麦克风模块)<br/>
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
   
<b>三.使用方法：</b><br/>
  打开网页浏览器, 输入访问地址 http://192.168.1.100 , 
  网页打开后有一个按钮, 点击切换是否让浏览器接收并播放声音. <br/>
  暂不支付多并发，同一时间只允许一个客户端<br/>
  注: <br/>
  必须用支持html5的浏览器, IE不支持html,所以不可以用. pc上可以用chrome浏览器, 手机上内置的浏览器基本上都支持html5<BR/>
  测试注: 如果电脑播放声音为杂音, 电脑控制面板找到声音设置,将声音播放格式改成48000hz<BR/>



