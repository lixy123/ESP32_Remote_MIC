# ESP32_Remote_MIC
ESP32 as Remote MIC
本项目是参考 https://github.com/paranerd/simplecam 项目的ESP32版本移值 

功能：<br/>
利用本程序，可以使esp32成为远程麦克风,树莓派运行Python连接此麦克风可监听到esp32的录音

使用场景：<br/>
单元楼大门声音对话，监听防盗等

使用方法：<br/>
1.esp32_remote_mic 用arduino工具烧录到esp32<br/>
  esp32_remote_mic2 这个版本开发失败，原开发目标是支持浏览器直接监听麦克风， 说明对项目simplecam的技术原理理解不够深入，目前听不到声音，原因不明。<br/>
2.rasberry 下两个py文件分别是监听声音文件直接输出到扬声器，输出到wav文件两个版本。<br/>
