class Player {
	constructor(config, socket) {
		let self = this;
		this.config = config;
		this.socket = socket;
		this.audioCtx = null;
		this.silence = new  Float32Array(this.config.bufferSize);
		this.playing = false;

        
		this.audioQueue = {
			buffer: new Float32Array(0),

			write: function(chunk) {
				let currentLength = this.buffer.length;
				let newBuffer = new Float32Array(currentLength + chunk.length);
                //console.log("currentLength",currentLength,newBuffer.length,chunk.length)
				newBuffer.set(this.buffer, 0);
				newBuffer.set(chunk, currentLength);
                //console.log("newBuffer",newBuffer.length)
				this.buffer = newBuffer;
			},

			read: function(nSamples) {
				let samplesToPlay = this.buffer.subarray(0, nSamples);
				this.buffer = this.buffer.subarray(nSamples, this.buffer.length);
				return samplesToPlay;
			},

			length: function() {
				return this.buffer.length;
			},

			clear: function() {
				this.buffer = new Float32Array(0)
			}
		}

	}

	play() {
		this.playing = true;
		this.audioCtx = new AudioContext();
        
        //48000频率 只读属性
        //16000频率的声音传入会导致 3倍加速
        console.log(this.audioCtx.sampleRate);
        //this.audioCtx.sampleRate= 16000;
        
		this.scriptNode = this.audioCtx.createScriptProcessor(this.config.bufferSize, 1, 1);
        console.log("play") 
		this.scriptNode.onaudioprocess = (e) => {
               // console.log("audioQueue") 
               // console.log(this.audioQueue.length())             
			if (this.audioQueue.length()) {

				e.outputBuffer.getChannelData(0).set(this.audioQueue.read(this.config.bufferSize));
			}
			else {
				e.outputBuffer.getChannelData(0).set(this.silence);
			}
		}

		this.scriptNode.connect(this.audioCtx.destination);
	}

    //将传入的16000频率的声音数据转成48000频率的声音数据
    interleave(e){
      let t = e.length;
      let sampleRate = 16000.0 ;
      let outputSampleRate = 48000.0;
      let s = 0;
      let o = sampleRate / outputSampleRate;
      let u = Math.ceil(t * outputSampleRate / sampleRate);      
      let a = new Float32Array(u);
      let i=0;
      for (i = 0; i < u; i++) {
        a[i] = e[Math.floor(s)];
        s += o;
      }
      return a;
    }
    
    //MDN上说，audioporcess缓冲区的数据是，非交错的32位线性PCM，标称范围介于-1和之间+1，
    //即32位浮点缓冲区，每个样本介于-1.0和1.0之间。
    //http://www.i2geek.com/mobile/articleContent.php?id=19544
    //https://webaudio.github.io/web-audio-api/#APIOverview
    write(chunk) {
		//将传入的blob转换成 Float32Array对象 
        var reader = new FileReader(); 
        var my_audioQueue= this.audioQueue;
        var my_int16ToFloat32= this.int16ToFloat32
        var my_interleave= this.interleave;
        reader.onload = function(e) {
           //console.log(reader.result); 
           let new_chunk=reader.result;          
  
           //A.如果输入是: 16000hz 16位声音数据            
           //let testDataInt = new Int8Array(new_chunk);
           let testDataInt = new Int16Array(new_chunk); 
           //16位对象转32位对象                
           let array = my_int16ToFloat32(testDataInt,0,testDataInt.length);
           //16000hz 转 48000hz
           array= my_interleave(array);           
           //console.log(array.length,array);  
           console.log("get wav bytes:",array.length);
           //B.如果输入是: 48000hz 16位声音数据
           /*
           let array = new Float32Array(new_chunk);
           console.log(array.length,array);              
		   */           
		   my_audioQueue.write(array);       
        }; 
        reader.readAsArrayBuffer(chunk);        
	}
    
    
	
	stop() {
		this.audioQueue.clear();
		this.scriptNode.disconnect();
		this.scriptNode = null;
	}

	isPlaying() {
		return !! this.scriptNode;
	}

    int16ToFloat32(inputArray, startIndex, length) {
		var output = new Float32Array(inputArray.length-startIndex);
		for (var i = startIndex; i < length; i++) {
			var int = inputArray[i];
			// If the high bit is on, then it is a negative number, and actually counts backwards.
			var float = (int >= 0x8000) ? -(0x10000 - int) / 0x8000 : int / 0x7FFF;
			output[i] = float;
		}
		return output;
	}
}
