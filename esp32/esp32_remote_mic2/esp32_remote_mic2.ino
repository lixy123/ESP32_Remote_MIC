#include <Arduino.h>
#include <WiFi.h>
#include "I2S.h"
#include "Wav.h"
#include <WebSocketsServer.h>
#include <SPIFFS.h>
#include <ESPAsyncWebServer.h>

//注意：
//  除了编译烧写本程序，还需要使用 ESP32 SKetch Data Upload 将data目录的一些网页文件等上传至 SPIFFS

//声音流: 16000hz, 16位 单声道 pcm数据 32KB/S 256kbps/s
//设置语句如下:
// I2S_Init(I2S_MODE_RX, 16000, I2S_BITS_PER_SAMPLE_16BIT);

const char *ssid = "CMCC-r3Ff";
const char *password =  "9999900000";
AsyncWebServer server(80);
WebSocketsServer webSocket = WebSocketsServer(1331);
const int numCommunicationData = 8000;
//数组：8000字节缓冲区
char communicationData[numCommunicationData];   //1char=8bits 1byte=8bits 1int=8*2 1long=8*4
char buff[100];

//这个psram版本就是提前分配了一个内存区,专用于存放声音数据,调用百度声音识别时不需要借助于SD卡做为交换.
//wav文件头的44个字节, 为base64 处理需要, 必须是6的倍数,  多加点数据

const int headerSize = 44;
byte  wav_head[headerSize];

uint8_t connect_no = -1; //当前连接号
bool sound_skip = false; //控制发送声音html5中断跳出

// Callback: receiving any WebSocket message
void onWebSocketEvent(uint8_t client_num,
                      WStype_t type,
                      uint8_t * payload,
                      size_t length) {
  String tmpstr ;
  int loop1;
  int sound_second = 0;

  int16_t val16 = 0;
  uint8_t val1, val2;
  int32_t tmpval = 0;

  //注意：esp32 对于wssocket 在同一函数中,不支持多并发
  //但同一函数在执行时，可以并发另一函数事件
  //所以如果在供给一个函数mic输出时， 其它用户是进入不了的！

  int32_t low_sound = 10;   //声音下限 低于此值的声音数据截掉
  int32_t high_sound = 5000; //声音上限 高于此值的声音数据截掉

  int add_sound = 40; //音量加倍系数

  File  wav_file ;

  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("client:[%u] Disconnected!\n", client_num);
      Serial.printf("client:[%u] last connect_no=[%u] \n", client_num, connect_no);

      if (connect_no == client_num)
      {
        sound_skip = true;
        Serial.printf("client:[%u] trigger stop wav\n",client_num);
      }
      break;

    // New client has connected
    case WStype_CONNECTED:
      {
        IPAddress ip = webSocket.remoteIP(client_num);
        Serial.printf("client:[%u] Connection from %s\n", client_num,ip.toString().c_str());
        //Serial.println();
      }
      break;

    // Handle text messages from client
    case WStype_TEXT:

      /*
        Serial.printf("client:[%u] begin send test sound...\n",client_num);

        wav_file = SPIFFS.open("/cn_word.wav", FILE_READ);
        //改成文件直接读取，测试效果
        while (wav_file.available())
        {
        int readnum = wav_file.read((uint8_t *)communicationData, numCommunicationData);
        if (readnum > 0)
        {
          webSocket.sendBIN(client_num, (uint8_t *)communicationData, readnum);
        }
        else
          break;
        }
        wav_file.close();

         Serial.printf("client:[%u] end send test sound...\n",client_num);
      */

      // Print out raw message
      //Serial.printf("client:[%u] [%u] seconds: %s\n",client_num, length,  payload);
      sprintf(buff, "%s", payload);

      for (int loop1 = 0; loop1 < length; loop1++)
      {
        char ch = payload[loop1];
        tmpstr += ch;
      }
      //Serial.println("tmpstr=" + tmpstr);
      sound_second = tmpstr.toInt();
      //Serial.println("");
      Serial.printf("client:[%u] request [%u] seconds\n", client_num,sound_second);

      Serial.printf("client:[%u] begin send wav sound ...\n", client_num );

      if (sound_second > 0)
      {
        //先输出wav文件头
        //html5不需要，注意会产生嘀嘀噪音
        //如果用于html5播放端， wav head数据不需要传输
        //8000*4是一秒的wav数据量
        CreateWavHeader(wav_head, 8000 * sound_second * 4);
        webSocket.sendBIN(client_num, (uint8_t *)wav_head, headerSize);
        //send_wavhead = true;
      }

      //如果声音秒数是负数，表示中断上次连接
      if (sound_second < 0)
      {
        Serial.printf("client:[%u] sound_second<0\n",client_num);
        sound_skip = true;
        break;
      }

      //1. 0 表示不限时间输出
      if (sound_second == 0)
      {

        connect_no = client_num;
        sound_skip = false;
        //esp32的线程功能局限，一次只能服务1个网页
        //如果无限循环输出声音，则当html5客户端关闭后，新的连接不能进来，导致esp32必须重启
        //建议一次 30秒或60秒，即使 html5客户端关闭,时间到后也会自动关闭本次连接！
        //Uncaught DOMException: Failed to execute 'send' on 'WebSocket': Still in CONNECTING state.


        //1/4秒 8000字节
        //每秒要循环4次读取音频数据
        //for 指定几秒就传输几秒数据
        //for ( loop1 = 0; loop1 < sound_second * 4; loop1++)
        //无限循环输出，直到当前html5连接主动关闭(比如网页关闭)
        while (true)
        {
          //  yield();
          if (sound_skip == true)
          {
            Serial.printf("client:[%u] skip send wav sound ...\n",client_num);
            break;
          }
          I2S_Read(communicationData, numCommunicationData);

          //for  提升音量
          for (int loop1 = 0; loop1 < numCommunicationData / 2 ; loop1++)
          {
            val1 = communicationData[loop1 * 2];
            val2 = communicationData[loop1 * 2 + 1] ;
            val16 = val1 + val2 *  256;

            //add_sound 配置成40最合适
            //乘以40 ：音量提升20db
            tmpval = val16 * add_sound;
            if (abs(tmpval) > 32767 )
            {
              if (val16 > 0)
                tmpval = 32767;
              else
                tmpval = -32767;
            }

            //对声音设置上下限
            //防止噪音
            //if (abs(tmpval) > high_sound)
            // tmpval = high_sound;

            //Serial.println(String(val1) + " " + String(val2) + " " + String(val16) + " " + String(tmpval));
            communicationData[loop1 * 2] =  (byte)(tmpval & 0xFF);
            communicationData[loop1 * 2 + 1] = (byte)((tmpval >> 8) & 0xFF);
          }

          /*
            //for  排除噪音
            for (int loop1 = 0; loop1 < numCommunicationData / 2 ; loop1++)
            {
            val1 = communicationData[loop1 * 2];
            val2 = communicationData[loop1 * 2 + 1] ;
            val16 = val1 + val2 *  256;

            //将高于指定音量，低于指定音量的数据排除

            tmpval = val16 * 1;
            //高于上限的噪音去除
            if (abs(tmpval) > high_sound )
            {
              if (val16 > 0)
                tmpval = high_sound;
              else
                tmpval = -high_sound;
            }

            //低于下限的噪音，去除
            if (abs(tmpval) < low_sound )
            {
              tmpval = 0;
            }

            //Serial.println(String(val1) + " " + String(val2) + " " + String(val16) + " " + String(tmpval));
            communicationData[loop1 * 2] =  (byte)(tmpval & 0xFF);
            communicationData[loop1 * 2 + 1] = (byte)((tmpval >> 8) & 0xFF);
            }
          */

          //传输声音文件主体
          webSocket.sendBIN(client_num, (uint8_t *)communicationData, numCommunicationData);
          //webSocket.broadcastBIN((uint8_t *)communicationData, numCommunicationData, false);
        }
      }
      //2.有限时间输出
      else
      {
        connect_no = client_num;
        sound_skip = false;
        //esp32的线程功能局限，一次只能服务1个网页
        //如果无限循环输出声音，则当html5客户端关闭后，新的连接不能进来，导致esp32必须重启
        //建议一次 30秒或60秒，即使 html5客户端关闭,时间到后也会自动关闭本次连接！
        //Uncaught DOMException: Failed to execute 'send' on 'WebSocket': Still in CONNECTING state.

        //1/4秒 8000字节
        //每秒要循环4次读取音频数据
        //for 指定几秒就传输几秒数据
        for ( loop1 = 0; loop1 < sound_second * 4; loop1++)
          //无限循环输出，直到当前html5连接主动关闭(比如网页关闭)
          //while (true)
        {
          //  yield();
          if (sound_skip == true)
          {
            Serial.printf("client:[%u] skip wav sound ...\n", client_num);
            break;
          }
          I2S_Read(communicationData, numCommunicationData);

          //for  提升音量
          for (int loop1 = 0; loop1 < numCommunicationData / 2 ; loop1++)
          {
            val1 = communicationData[loop1 * 2];
            val2 = communicationData[loop1 * 2 + 1] ;
            val16 = val1 + val2 *  256;

            //add_sound 配置成40最合适
            //乘以40 ：音量提升20db
            tmpval = val16 * add_sound;
            if (abs(tmpval) > 32767 )
            {
              if (val16 > 0)
                tmpval = 32767;
              else
                tmpval = -32767;
            }

            //对声音设置上下限
            //防止噪音
            //if (abs(tmpval) > high_sound)
            // tmpval = high_sound;

            //Serial.println(String(val1) + " " + String(val2) + " " + String(val16) + " " + String(tmpval));
            communicationData[loop1 * 2] =  (byte)(tmpval & 0xFF);
            communicationData[loop1 * 2 + 1] = (byte)((tmpval >> 8) & 0xFF);
          }

          /*
            //for  排除噪音
            for (int loop1 = 0; loop1 < numCommunicationData / 2 ; loop1++)
            {
            val1 = communicationData[loop1 * 2];
            val2 = communicationData[loop1 * 2 + 1] ;
            val16 = val1 + val2 *  256;

            //将高于指定音量，低于指定音量的数据排除

            tmpval = val16 * 1;
            //高于上限的噪音去除
            if (abs(tmpval) > high_sound )
            {
              if (val16 > 0)
                tmpval = high_sound;
              else
                tmpval = -high_sound;
            }

            //低于下限的噪音，去除
            if (abs(tmpval) < low_sound )
            {
              tmpval = 0;
            }

            //Serial.println(String(val1) + " " + String(val2) + " " + String(val16) + " " + String(tmpval));
            communicationData[loop1 * 2] =  (byte)(tmpval & 0xFF);
            communicationData[loop1 * 2 + 1] = (byte)((tmpval >> 8) & 0xFF);
            }
          */

          //传输声音文件主体
          webSocket.sendBIN(client_num, (uint8_t *)communicationData, numCommunicationData);
          //webSocket.broadcastBIN((uint8_t *)communicationData, numCommunicationData, false);
        }
      }

      Serial.printf("client:[%u] end send wav sound ...\n", client_num );

      break;

    // For everything else: do nothing
    case WStype_BIN:
    case WStype_ERROR:
    case WStype_FRAGMENT_TEXT_START:
    case WStype_FRAGMENT_BIN_START:
    case WStype_FRAGMENT:
    case WStype_FRAGMENT_FIN:
    default:
      break;
  }
}


// Callback: send homepage
void onIndexRequest(AsyncWebServerRequest * request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("  [" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/index.html", "text/html");
}

// Callback: send style sheet
void onCSSRequest(AsyncWebServerRequest * request) {
  IPAddress remote_ip = request->client()->remoteIP();
  //Serial.println("[" + remote_ip.toString() +
  //              "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/style.css", "text/css");
}

void onjs_jqueryRequest(AsyncWebServerRequest * request) {
  IPAddress remote_ip = request->client()->remoteIP();
 // Serial.println("[" + remote_ip.toString() +
 //                "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/jquery-3.4.1.min.js", "text/javascript");
}

void onjs_liveRequest(AsyncWebServerRequest * request) {
  IPAddress remote_ip = request->client()->remoteIP();
  //Serial.println("[" + remote_ip.toString() +
  //               "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/live.js", "text/javascript");
}

void onjs_playerRequest(AsyncWebServerRequest * request) {
  IPAddress remote_ip = request->client()->remoteIP();
  //Serial.println("[" + remote_ip.toString() +
  //               "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/player.js", "text/javascript");
}

//void onjs_socketRequest(AsyncWebServerRequest *request) {
//  IPAddress remote_ip = request->client()->remoteIP();
//  Serial.println("[" + remote_ip.toString() +
//                 "] HTTP GET request of " + request->url());
//  request->send(SPIFFS, "/socket.io.min.js", "text/javascript");
//}

// Callback: send 404 if requested file does not exist
void onPageNotFound(AsyncWebServerRequest * request) {
  IPAddress remote_ip = request->client()->remoteIP();
  //Serial.println("[" + remote_ip.toString() +
  //               "] HTTP GET request of " + request->url());
  request->send(404, "text/plain", "Not found");
}


void setup() {
  Serial.begin(115200);

  // Make sure we can read the file system
  if ( !SPIFFS.begin()) {
    Serial.println("Error mounting SPIFFS");
    while (1);
  }

  //I2S_BITS_PER_SAMPLE_8BIT 配置的话，下句会报错，
  //最小必须配置成I2S_BITS_PER_SAMPLE_16BIT
  //I2S_Init(I2S_MODE_RX, 16000, I2S_BITS_PER_SAMPLE_16BIT);

  I2S_Init(I2S_MODE_RX, 16000, I2S_BITS_PER_SAMPLE_16BIT);
  connectwifi();

  // On HTTP request for root, provide index.html file
  server.on("/", HTTP_GET, onIndexRequest);

  // On HTTP request for style sheet, provide style.css
  server.on("/style.css", HTTP_GET, onCSSRequest);

  server.on("/jquery-3.4.1.min.js", HTTP_GET, onjs_jqueryRequest);
  server.on("/live.js", HTTP_GET, onjs_liveRequest);
  server.on("/player.js", HTTP_GET, onjs_playerRequest);
  //  server.on("/socket.io.min.js", HTTP_GET, onjs_socketRequest);

  // Handle requests for pages that do not exist
  server.onNotFound(onPageNotFound);

  // Start web server
  server.begin();

  // Start WebSocket server and assign callback
  webSocket.begin();
  webSocket.onEvent(onWebSocketEvent);
}

void connectwifi()
{
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.disconnect();
  delay(200);
  WiFi.config(IPAddress(192, 168, 1, 100), //设置静态IP位址
              IPAddress(192, 168, 1, 1),
              IPAddress(255, 255, 255, 0),
              IPAddress(192, 168, 1, 1)
             );
  WiFi.mode(WIFI_STA);
  Serial.println("Connecting to WIFI");
  WiFi.begin(ssid, password);
  while ((!(WiFi.status() == WL_CONNECTED))) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("Connected");
  Serial.println("My Local IP is : ");
  Serial.println(WiFi.localIP());
}


void loop() {
  connectwifi();
  // Look for and handle WebSocket data
  webSocket.loop();
}
