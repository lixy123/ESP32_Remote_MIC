
var url = 'ws://' + document.domain + ':' + 1331;
//var url = 'ws://' + document.domain + ':' + 80;
  
let config = {
	bufferSize: 1024*4
}
 
 
$("#listen").on('click', function() {
	if (player.isPlaying()) {
        console.log("trigger listen off");
		$(this).text("listen off");		
		player.stop();
	}
	else {
        console.log("trigger listen on");
		$(this).text("listen on")
		player.play();
        //延时，确保连接成功后再发送信息
		setTimeout(function(){ doSend("0"); },1000);
		//doSend("600"); 
	}
});

// Call this to connect to the WebSocket server
function wsConnect(url) {    
    // Connect to WebSocket server
    websocket = new WebSocket(url);
    
    // Assign callbacks
    websocket.onopen = function(evt) { onOpen(evt) };
    websocket.onclose = function(evt) { onClose(evt) };
    websocket.onmessage = function(evt) { onMessage(evt) };
    websocket.onerror = function(evt) { onError(evt) };
	

    player = new Player(config, websocket);
    //player.play();
}
 
// Called when a WebSocket connection is established with the server
function onOpen(evt) { 
    // Log connection state
    console.log("Connected");    

}
 
// Called when the WebSocket connection is closed
function onClose(evt) { 
    // Log disconnection state
    console.log("Disconnected");    

    // Try to reconnect after a few seconds
    //setTimeout(function() { wsConnect(url) }, 2000);
}
 
// Called when a message is received from the server
function onMessage(evt) { 
    // Print out our received message
    //blob对象
    //console.log(evt.data);
		
	player.write(evt.data);   
}
 
// Called when a WebSocket error occurs
function onError(evt) {
    console.log("ERROR: " + evt.data);
}
 
// Sends a message to the server (and prints it to the console)
function doSend(message) {
    //ESP32是单线程，同一函数一次只能同时服务一个
    //一次只能同时服务一个
    //执行前最好检查下当前连接状态
    //否则容易出现如下错误
    //Uncaught DOMException: Failed to execute 'send' on 'WebSocket': 
    //Still in CONNECTING state.
    console.log("Sending: " + message);
    websocket.send(message);
}
 

 // This is called when the page finishes loading
function init() {   
    // Connect to WebSocket server
    wsConnect(url);
}


		
		
// Call the init function as soon as the page loads
window.addEventListener("load", init, false);
 
