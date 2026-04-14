// AudioWorklet processors for PCM audio capture (mic) and playback (speaker).
// Used by the voice chat feature to stream 16-bit PCM to/from Gemini Live API.

class PcmCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input.length === 0) return true;

    const float32 = input[0];
    if (!float32 || float32.length === 0) return true;

    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      int16[i] = Math.max(-0x8000, Math.min(0x7fff, Math.round(float32[i] * 0x7fff)));
    }

    this.port.postMessage(int16.buffer);
    return true;
  }
}

class PcmPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._queue = [];
    this._offset = 0;

    this.port.onmessage = (event) => {
      const float32 = new Float32Array(event.data);
      this._queue.push(float32);
    };
  }

  process(outputs) {
    const output = outputs[0];
    if (output.length === 0) return true;

    const channel = output[0];
    let written = 0;

    while (written < channel.length && this._queue.length > 0) {
      const current = this._queue[0];
      const available = current.length - this._offset;
      const needed = channel.length - written;
      const count = Math.min(available, needed);

      channel.set(current.subarray(this._offset, this._offset + count), written);
      written += count;
      this._offset += count;

      if (this._offset >= current.length) {
        this._queue.shift();
        this._offset = 0;
      }
    }

    for (let i = written; i < channel.length; i++) {
      channel[i] = 0;
    }

    return true;
  }
}

registerProcessor("pcm-capture", PcmCaptureProcessor);
registerProcessor("pcm-player", PcmPlayerProcessor);
