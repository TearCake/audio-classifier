/**
 * Helper to process, decode, and auto-trim audio in the browser.
 * Reduces large audio files into a clean 5-second 16-bit PCM WAV to avoid
 * payload limits (HTTP 413) and optimize model inference time.
 */

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

function encodeWav(audioBuffer: AudioBuffer, numSamples: number): ArrayBuffer {
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const bytesPerSample = 2; // 16-bit PCM
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = numSamples * blockAlign;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  // RIFF identifier
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(view, 8, "WAVE");

  // fmt sub-chunk
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true); // AudioFormat (1 = PCM)
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true); // BitsPerSample (16 bits)

  // data sub-chunk
  writeString(view, 36, "data");
  view.setUint32(40, dataSize, true);

  // Extract channel samples and interleave them
  const channels: Float32Array[] = [];
  for (let ch = 0; ch < numChannels; ch++) {
    channels.push(audioBuffer.getChannelData(ch));
  }

  let offset = 44;
  for (let i = 0; i < numSamples; i++) {
    for (let ch = 0; ch < numChannels; ch++) {
      const sample = Math.max(-1, Math.min(1, channels[ch]?.[i] ?? 0));
      const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      view.setInt16(offset, intSample, true);
      offset += 2;
    }
  }

  return buffer;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  const chunkSize = 0x8000; // 32KB chunks to prevent stack overflow
  for (let i = 0; i < len; i += chunkSize) {
    const chunk = bytes.subarray(i, Math.min(i + chunkSize, len));
    binary += String.fromCharCode.apply(null, Array.from(chunk));
  }
  return btoa(binary);
}

export interface ProcessedAudio {
  base64String: string;
  duration: number;
  originalDuration: number;
}

export async function processAndTrimAudio(
  file: File,
  maxDurationSeconds = 5.0,
): Promise<ProcessedAudio> {
  const arrayBuffer = await file.arrayBuffer();

  const AudioCtxClass =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext })
      .webkitAudioContext;

  if (!AudioCtxClass) {
    // Fallback: If Web Audio API is not supported in the browser
    const base64String = arrayBufferToBase64(arrayBuffer);
    return {
      base64String,
      duration: 0,
      originalDuration: 0,
    };
  }

  const audioCtx = new AudioCtxClass();

  try {
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    const originalDuration = audioBuffer.duration;
    const duration = Math.min(originalDuration, maxDurationSeconds);
    const numSamples = Math.floor(duration * audioBuffer.sampleRate);

    const wavBuffer = encodeWav(audioBuffer, numSamples);
    const base64String = arrayBufferToBase64(wavBuffer);

    return {
      base64String,
      duration,
      originalDuration,
    };
  } catch {
    throw new Error(
      "Could not decode the selected audio file. Please ensure it is a valid audio file (e.g. WAV or MP3).",
    );
  } finally {
    if (audioCtx.state !== "closed") {
      void audioCtx.close();
    }
  }
}
