#include <Arduino.h>
#include <WiFi.h>
#include "I2S.h"
#include "Wav.h"
#include <WebSocketsServer.h>
#include <SPIFFS.h>
#include <ESPAsyncWebServer.h>

//用浏览器播放不出wav声音，原因不明！！！

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



// Callback: send homepage
void onIndexRequest(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/index.html", "text/html");
}

// Callback: send style sheet
void onCSSRequest(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/style.css", "text/css");
}

void onjs_jqueryRequest(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/jquery-3.4.1.min.js", "text/javascript");
}

void onjs_liveRequest(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/live.js", "text/javascript");
}

void onjs_playerRequest(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/player.js", "text/javascript");
}

void onjs_socketRequest(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(SPIFFS, "/socket.io.min.js", "text/javascript");
}

// Callback: send 404 if requested file does not exist
void onPageNotFound(AsyncWebServerRequest *request) {
  IPAddress remote_ip = request->client()->remoteIP();
  Serial.println("[" + remote_ip.toString() +
                 "] HTTP GET request of " + request->url());
  request->send(404, "text/plain", "Not found");
}


void setup() {



  // Start Serial port
  Serial.begin(115200);

  // Make sure we can read the file system
  if ( !SPIFFS.begin()) {
    Serial.println("Error mounting SPIFFS");
    while (1);
  }

  //I2S_BITS_PER_SAMPLE_8BIT 配置的话，下句会报错，
  //最小必须配置成I2S_BITS_PER_SAMPLE_16BIT
  I2S_Init(I2S_MODE_RX, 16000, I2S_BITS_PER_SAMPLE_16BIT);

  connectwifi();



  // On HTTP request for root, provide index.html file
  server.on("/", HTTP_GET, onIndexRequest);

  // On HTTP request for style sheet, provide style.css
  server.on("/style.css", HTTP_GET, onCSSRequest);

  server.on("/jquery-3.4.1.min.js", HTTP_GET, onjs_jqueryRequest);
  server.on("/live.js", HTTP_GET, onjs_liveRequest);
  server.on("/player.js", HTTP_GET, onjs_playerRequest);
  server.on("/socket.io.min.js", HTTP_GET, onjs_socketRequest);



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
  Serial.print((WiFi.localIP()));
}


void loop() {
  connectwifi();
  // Look for and handle WebSocket data
  webSocket.loop();
}
