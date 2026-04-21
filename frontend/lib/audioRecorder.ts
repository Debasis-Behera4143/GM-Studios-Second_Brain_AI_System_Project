/**
 * Audio Recording Utility
 * Provides browser microphone recording and WAV file generation
 */

export interface RecorderConfig {
  sampleRate?: number;
  numChannels?: number;
  onStart?: () => void;
  onStop?: () => void;
  onError?: (error: Error) => void;
}

export class AudioRecorder {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private scriptProcessor: ScriptProcessorNode | null = null;
  private chunks: Float32Array[] = [];
  private isRecording = false;
  private sampleRate: number;
  private numChannels: number;
  private onStart?: () => void;
  private onStop?: () => void;
  private onError?: (error: Error) => void;

  constructor(config: RecorderConfig = {}) {
    this.sampleRate = config.sampleRate || 44100;
    this.numChannels = config.numChannels || 1;
    this.onStart = config.onStart;
    this.onStop = config.onStop;
    this.onError = config.onError;
  }

  async start(): Promise<void> {
    try {
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      // Create audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: this.sampleRate,
      });

      // Create analyser for audio visualization (optional)
      this.analyser = this.audioContext.createAnalyser();

      // Create script processor for recording
      this.scriptProcessor = this.audioContext.createScriptProcessor(4096, this.numChannels, this.numChannels);

      // Get microphone input
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Connect nodes
      source.connect(this.scriptProcessor);
      this.scriptProcessor.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);

      // Handle audio data
      this.scriptProcessor.onaudioprocess = (e: AudioProcessingEvent) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const chunk = new Float32Array(inputData.length);
        chunk.set(inputData);
        this.chunks.push(chunk);
      };

      this.isRecording = true;
      this.onStart?.();
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.onError?.(err);
      throw err;
    }
  }

  stop(): Blob {
    if (!this.isRecording || !this.audioContext) {
      throw new Error('Recorder is not currently recording');
    }

    this.isRecording = false;

    // Stop all audio nodes
    this.scriptProcessor?.disconnect();
    this.analyser?.disconnect();
    this.audioContext?.destination;

    // Stop microphone stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // Generate WAV file
    const wavBlob = this.encodeWAV(this.chunks);
    this.chunks = [];

    this.onStop?.();
    return wavBlob;
  }

  isRecordingNow(): boolean {
    return this.isRecording;
  }

  private encodeWAV(chunks: Float32Array[]): Blob {
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const audioData = new Float32Array(totalLength);
    
    let offset = 0;
    for (const chunk of chunks) {
      audioData.set(chunk, offset);
      offset += chunk.length;
    }

    return this.floatTo16BitPCM(audioData);
  }

  private floatTo16BitPCM(floatArray: Float32Array): Blob {
    const buffer = new ArrayBuffer(floatArray.length * 2);
    const view = new DataView(buffer);
    let offset = 0;

    // Convert float samples to 16-bit PCM
    for (let i = 0; i < floatArray.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, floatArray[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return this.encodeWAVHeader(buffer, floatArray.length);
  }

  private encodeWAVHeader(pcmData: ArrayBuffer, pcmSamples: number): Blob {
    const bytesPerSample = 2;
    const blockAlign = this.numChannels * bytesPerSample;
    const byteRate = this.sampleRate * blockAlign;
    const dataLength = pcmSamples * bytesPerSample;

    const header = new ArrayBuffer(44);
    const headerView = new DataView(header);

    // RIFF identifier
    this.writeString(headerView, 0, 'RIFF');
    headerView.setUint32(4, 36 + dataLength, true);
    this.writeString(headerView, 8, 'WAVE');

    // fmt chunk
    this.writeString(headerView, 12, 'fmt ');
    headerView.setUint32(16, 16, true); // chunk size
    headerView.setUint16(20, 1, true); // PCM format
    headerView.setUint16(22, this.numChannels, true);
    headerView.setUint32(24, this.sampleRate, true);
    headerView.setUint32(28, byteRate, true);
    headerView.setUint16(32, blockAlign, true);
    headerView.setUint16(34, 16, true); // bits per sample

    // data chunk
    this.writeString(headerView, 36, 'data');
    headerView.setUint32(40, dataLength, true);

    return new Blob([header, pcmData], { type: 'audio/wav' });
  }

  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }
}

/**
 * Convert blob to File object
 */
export function blobToFile(blob: Blob, filename: string): File {
  return new File([blob], filename, { type: blob.type });
}

/**
 * Check if browser supports audio recording
 */
export function isAudioRecordingSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    navigator?.mediaDevices?.getUserMedia &&
    (window.AudioContext || (window as any).webkitAudioContext)
  );
}
