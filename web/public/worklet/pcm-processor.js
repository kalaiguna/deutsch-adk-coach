// AudioWorklet processor: forwards 16kHz PCM Float32 chunks to the main thread
class PcmProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel) this.port.postMessage(channel.slice());
    return true;
  }
}
registerProcessor("pcm-processor", PcmProcessor);
