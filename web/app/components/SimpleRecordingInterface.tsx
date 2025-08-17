'use client';

import { useState, useEffect, useRef } from 'react';
import { getSupportedAudioFormat, isRecordingSupported } from '../utils/formatSupport';

export default function SimpleRecordingInterface() {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const startTimer = () => {
    setDuration(0);
    timerRef.current = setInterval(() => {
      setDuration(prev => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const startRecording = async () => {
    console.log('START RECORDING CALLED');
    setErrorMessage('');
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        console.log('MediaRecorder stopped');
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        handleUpload(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      startTimer();
      console.log('Recording started successfully');
    } catch (error) {
      console.error('Error starting recording:', error);
      setErrorMessage('Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = () => {
    console.log('STOP RECORDING CALLED');
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      stopTimer();
      console.log('Recording stopped');
    } else {
      console.log('No active recording to stop');
    }
  };

  const handleUpload = async (blob: Blob) => {
    console.log('Uploading blob:', blob);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiToken = process.env.NEXT_PUBLIC_API_TOKEN || 'changeme';

    try {
      const formData = new FormData();
      const filename = `recording_${Date.now()}.webm`;
      const file = new File([blob], filename, { type: 'audio/webm' });
      formData.append('file', file);

      const response = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiToken}`
        },
        body: formData
      });

      if (response.ok) {
        console.log('Upload successful');
      } else {
        console.error('Upload failed:', response.statusText);
      }
    } catch (error) {
      console.error('Upload error:', error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isRecordingSupported()) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <p className="text-gray-600">Recording not supported in this browser</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      {/* Debug info */}
      <div className="mb-4 text-xs text-gray-500">
        Debug: isRecording = {isRecording ? 'true' : 'false'} | duration = {duration}
      </div>

      {/* Recording button */}
      <button
        onClick={() => {
          console.log('Button clicked! isRecording:', isRecording);
          if (isRecording) {
            stopRecording();
          } else {
            startRecording();
          }
        }}
        className={`w-32 h-32 rounded-full border-4 transition-all duration-200 flex items-center justify-center cursor-pointer ${
          isRecording
            ? 'bg-red-500 border-red-600 hover:bg-red-600'
            : 'bg-white border-gray-300 hover:border-gray-400 shadow-lg'
        }`}
        style={{ pointerEvents: 'auto', zIndex: 9999, position: 'relative' }}
      >
        {isRecording ? (
          <div className="w-6 h-6 bg-white rounded-sm" />
        ) : (
          <svg className="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        )}
      </button>

      {/* Duration */}
      {isRecording && (
        <div className="mt-4 text-2xl font-mono font-bold text-gray-800">
          {formatDuration(duration)}
        </div>
      )}

      {/* Status text */}
      <div className="mt-4 text-center">
        {isRecording ? (
          <p className="text-red-600 font-medium">Recording... Click button to stop</p>
        ) : (
          <p className="text-gray-600">Click to start recording</p>
        )}
      </div>

      {/* Error message */}
      {errorMessage && (
        <div className="mt-4 text-red-600 text-sm">
          {errorMessage}
        </div>
      )}
    </div>
  );
}