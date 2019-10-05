#include <Arduino.h>
#include <WiFi.h>
#include "I2S.h"
#include "Wav.h"
#include <WebSocketsServer.h>

//本项目是参考 https://github.com/paranerd/simplecam 项目的ESP32版本, 服务端是树莓派，客户端可以直接用支持html5的浏览器监听声音，但无声音,原因不明，
//虽然websocket 服务端没做成被浏览器直接监听声音，但可以被其它客户端连接。
//利用本程序，可以使esp32成为远程麦克风,客户端可以用树莓派运行Python连接此麦克风
//客户端连接使用,有二种方式，一种是实时声音监听，一种是声音录入保存到文件


/*
INMP441-ESP接线定义见I2S.h
SCK IO14
WS  IO27
SD  IO2
L/R GND
*/

const char *ssid = "CMCC-r3Ff";
const char *password =  "9999900000";

WebSocketsServer webSocket = WebSocketsServer(1331);
const int numCommunicationData = 8000;
//数组：8000字节缓冲区
char communicationData[numCommunicationData];   //1char=8bits 1byte=8bits 1int=8*2 1long=8*4
char buff[100];


//wav文件头的44个字节

const int headerSize = 44;
byte  wav_head[headerSize];

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

  switch (type) {

    // Client has disconnected
    case WStype_DISCONNECTED:
      Serial.printf("[%u] Disconnected!\n", client_num);
      break;

    // New client has connected
    case WStype_CONNECTED:
      {
        IPAddress ip = webSocket.remoteIP(client_num);
        Serial.printf("[%u] Connection from ", client_num);
        Serial.println(ip.toString());
      }
      break;

    // Handle text messages from client
    case WStype_TEXT:

      // Print out raw message
      Serial.printf("[%u] [%u] seconds: %s\n", length, client_num, payload);
      sprintf(buff, "%s", payload);

      for (int loop1 = 0; loop1 < length; loop1++)
      {
        char ch = payload[loop1];
        tmpstr += ch;
      }
      Serial.println("tmpstr=" + tmpstr);
      sound_second = tmpstr.toInt();
      Serial.printf("%u seconds", sound_second);

      CreateWavHeader(wav_head, 8000 * sound_second * 4);

      //1/4秒 8000字节
      //每秒要循环4次读取音频数据
      for ( loop1 = 0; loop1 < sound_second * 4; loop1++)
      {
        I2S_Read(communicationData, numCommunicationData);

        //for  提升音量
        for (int loop1 = 0; loop1 < numCommunicationData / 2 ; loop1++)
        {
          val1 = communicationData[loop1 * 2];
          val2 = communicationData[loop1 * 2 + 1] ;
          val16 = val1 + val2 *  256;


          //乘以40 ：音量提升20db
          tmpval = val16 * 40;
          if (abs(tmpval) > 32767 )
          {
            if (val16 > 0)
              tmpval = 32767;
            else
              tmpval = -32767;
          }
          //Serial.println(String(val1) + " " + String(val2) + " " + String(val16) + " " + String(tmpval));
          communicationData[loop1 * 2] =  (byte)(tmpval & 0xFF);
          communicationData[loop1 * 2 + 1] = (byte)((tmpval >> 8) & 0xFF);
        }

        if (loop1 == 0)
          webSocket.sendBIN(client_num, (uint8_t *)wav_head, headerSize);
        //webSocket.broadcastBIN((uint8_t *)wav_head, headerSize, false);

        webSocket.sendBIN(client_num, (uint8_t *)communicationData, numCommunicationData);
        //webSocket.broadcastBIN((uint8_t *)communicationData, numCommunicationData, false);
      }

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




void setup() {

  // Start Serial port
  Serial.begin(115200);


  //I2S_BITS_PER_SAMPLE_8BIT 配置的话，下句会报错，
  //最小必须配置成I2S_BITS_PER_SAMPLE_16BIT
  I2S_Init(I2S_MODE_RX, 16000, I2S_BITS_PER_SAMPLE_16BIT);

  connectwifi();

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
  Serial.print((WiFi.localIP()));
}


void loop() {
  connectwifi();
  // Look for and handle WebSocket data
  webSocket.loop();
}
