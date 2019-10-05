class Player {
	constructor(config, socket) {
		let self = this;
		this.config = config;
		this.socket = socket;
		this.audioCtx = null;
		this.silence = new  Int8Array(this.config.bufferSize);
		this.playing = false;

		this.audioQueue = {
			buffer: new Int8Array(0),

			write: function(chunk) {
				let currentLength = this.buffer.length;
				let newBuffer = new Int8Array(currentLength + chunk.length);
				newBuffer.set(this.buffer, 0);
				newBuffer.set(chunk, currentLength);
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
				this.buffer = new Int8Array(0)
			}
		}

	}

	play() {
		this.playing = true;
		this.audioCtx = new AudioContext();
		this.scriptNode = this.audioCtx.createScriptProcessor(this.config.bufferSize, 1, 1);
		this.scriptNode.onaudioprocess = (e) => {
			if (this.audioQueue.length()) {
				e.outputBuffer.getChannelData(0).set(this.audioQueue.read(this.config.bufferSize));
			}
			else {
				e.outputBuffer.getChannelData(0).set(this.silence);
			}
		}

		this.scriptNode.connect(this.audioCtx.destination);
	}

    write(chunk) {
		//let array = new Float32Array(chunk);
		//this.audioQueue.write(array);	
        console.log(chunk)   
        let array =new Int8Array(chunk);
        console.log(chunk.length) 
        this.audioQueue.write(array);
	
	}
	
	stop() {
		this.audioQueue.clear();
		this.scriptNode.disconnect();
		this.scriptNode = null;
	}

	isPlaying() {
		return !! this.scriptNode;
	}


}
