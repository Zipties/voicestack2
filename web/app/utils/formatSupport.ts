export interface AudioFormat {
  mimeType: string;
  extension: string;
  name: string;
}

export const AUDIO_FORMATS: AudioFormat[] = [
  {
    mimeType: 'audio/webm;codecs=opus',
    extension: 'webm',
    name: 'WebM Opus'
  },
  {
    mimeType: 'audio/mp4;codecs=mp4a.40.2',
    extension: 'mp4',
    name: 'MP4 AAC'
  },
  {
    mimeType: 'audio/webm;codecs=vorbis',
    extension: 'webm',
    name: 'WebM Vorbis'
  },
  {
    mimeType: 'audio/wav',
    extension: 'wav',
    name: 'WAV'
  }
];

export function getSupportedAudioFormat(): AudioFormat | null {
  if (typeof window === 'undefined' || !('MediaRecorder' in window)) {
    return null;
  }

  for (const format of AUDIO_FORMATS) {
    if (MediaRecorder.isTypeSupported(format.mimeType)) {
      return format;
    }
  }

  return null;
}

export function isRecordingSupported(): boolean {
  return typeof window !== 'undefined' && 
         'MediaRecorder' in window && 
         'navigator' in window && 
         'mediaDevices' in navigator && 
         'getUserMedia' in navigator.mediaDevices;
}