'use client';

import { useState, useEffect, useRef } from 'react';
import { useReactMediaRecorder } from 'react-media-recorder';
import { getSupportedAudioFormat, isRecordingSupported } from '../utils/formatSupport';
import { useOfflineRecordings } from '../hooks/useOfflineRecordings';

type RecordingState = 'idle' | 'recording' | 'stopped' | 'uploading' | 'error';

function RecordingInterfaceCore() {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [duration, setDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const durationRef = useRef<NodeJS.Timeout>();
  
  const { addPendingRecording, isOnline, pendingRecordings } = useOfflineRecordings();
  
  const supportedFormat = getSupportedAudioFormat();
  const recordingSupported = isRecordingSupported();

  const {
    status,
    startRecording,
    stopRecording,
    mediaBlobUrl,
    error: recorderError
  } = useReactMediaRecorder({
    audio: true,
    onStop: (blobUrl, blob) => {
      console.log('Recording stopped:', { blobUrl, blob });
      setRecordingState('stopped');
      stopDurationTimer();
    }
  });

  // Update recording state based on media recorder status
  useEffect(() => {
    console.log('Media recorder status changed:', status);
    switch (status) {
      case 'idle':
        setRecordingState('idle');
        break;
      case 'recording':
        setRecordingState('recording');
        startDurationTimer();
        break;
      case 'stopped':
        setRecordingState('stopped');
        stopDurationTimer();
        break;
    }
  }, [status]);

  // Handle recorder errors
  useEffect(() => {
    if (recorderError) {
      setRecordingState('error');
      setErrorMessage('Recording failed. Please check your microphone permissions.');
      console.error('Recorder error:', recorderError);
    }
  }, [recorderError]);

  // Auto-upload when recording stops and blob is available
  useEffect(() => {
    if (mediaBlobUrl && recordingState === 'stopped') {
      handleUpload();
    }
  }, [mediaBlobUrl, recordingState]);

  const startDurationTimer = () => {
    setDuration(0);
    durationRef.current = setInterval(() => {
      setDuration(prev => prev + 1);
    }, 1000);
  };

  const stopDurationTimer = () => {
    if (durationRef.current) {
      clearInterval(durationRef.current);
    }
  };

  const handleStartRecording = async () => {
    setErrorMessage('');
    setDuration(0);
    
    try {
      await startRecording();
    } catch (error) {
      setRecordingState('error');
      setErrorMessage('Failed to start recording. Please check microphone permissions.');
      console.error('Start recording error:', error);
    }
  };

  const handleStopRecording = () => {
    console.log('Attempting to stop recording, current status:', status);
    try {
      stopRecording();
      console.log('stopRecording() called successfully');
    } catch (error) {
      console.error('Error calling stopRecording():', error);
      setRecordingState('error');
      setErrorMessage('Failed to stop recording.');
    }
    stopDurationTimer();
  };

  const handleUpload = async () => {
    if (!mediaBlobUrl || !supportedFormat) return;

    setRecordingState('uploading');

    try {
      // Fetch the blob from the URL
      const response = await fetch(mediaBlobUrl);
      const blob = await response.blob();

      if (isOnline) {
        // Upload directly
        await uploadRecording(blob);
      } else {
        // Store for later upload
        const pendingRecording = {
          id: `recording_${Date.now()}`,
          blob,
          timestamp: Date.now(),
          duration,
          format: supportedFormat.mimeType
        };
        addPendingRecording(pendingRecording);
        setRecordingState('idle');
      }
    } catch (error) {
      setRecordingState('error');
      setErrorMessage('Failed to process recording.');
      console.error('Upload error:', error);
    }
  };

  const uploadRecording = async (blob: Blob) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiToken = process.env.NEXT_PUBLIC_API_TOKEN || 'changeme';

    try {
      const formData = new FormData();
      const filename = `recording_${Date.now()}.${supportedFormat?.extension || 'wav'}`;
      const file = new File([blob], filename, { type: supportedFormat?.mimeType || 'audio/wav' });
      formData.append('file', file);

      const response = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiToken}`
        },
        body: formData
      });

      if (response.ok) {
        setRecordingState('idle');
        setDuration(0);
      } else {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
    } catch (error) {
      setRecordingState('error');
      setErrorMessage('Upload failed. Recording saved for later.');
      console.error('Upload error:', error);
      
      // Save for offline upload
      const pendingRecording = {
        id: `recording_${Date.now()}`,
        blob,
        timestamp: Date.now(),
        duration,
        format: supportedFormat?.mimeType || 'audio/wav'
      };
      addPendingRecording(pendingRecording);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!recordingSupported) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <div className="text-center">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Recording Not Supported</h3>
          <p className="text-gray-600 mb-4">Your browser doesn't support audio recording.</p>
          <p className="text-sm text-gray-500">Please use the file upload feature instead.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      {/* Status indicators */}
      <div className="mb-6 text-center">
        {!isOnline && (
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-yellow-100 text-yellow-800 mb-2">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Offline - recordings will be uploaded later
          </div>
        )}
        
        {pendingRecordings.length > 0 && (
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
            {pendingRecordings.length} recording{pendingRecordings.length !== 1 ? 's' : ''} pending upload
          </div>
        )}
      </div>

      {/* Main recording button */}
      <div className="relative mb-6">
        <button
          onClick={(e) => {
            console.log('BUTTON CLICKED! Current state:', recordingState);
            e.preventDefault();
            e.stopPropagation();
            if (recordingState === 'recording') {
              console.log('Calling handleStopRecording');
              handleStopRecording();
            } else {
              console.log('Calling handleStartRecording');
              handleStartRecording();
            }
          }}
          disabled={recordingState === 'uploading'}
          style={{ pointerEvents: 'auto', zIndex: 1000 }}
          className={`w-32 h-32 rounded-full border-4 transition-all duration-200 flex items-center justify-center cursor-pointer ${
            recordingState === 'recording'
              ? 'bg-red-500 border-red-600 hover:bg-red-600 animate-pulse'
              : recordingState === 'uploading'
              ? 'bg-gray-400 border-gray-500 cursor-not-allowed'
              : recordingState === 'error'
              ? 'bg-red-100 border-red-300 hover:bg-red-200'
              : 'bg-white border-gray-300 hover:border-gray-400 shadow-lg hover:shadow-xl'
          }`}
          aria-label={recordingState === 'recording' ? 'Stop recording' : 'Start recording'}
        >
          {recordingState === 'uploading' ? (
            <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : recordingState === 'recording' ? (
            <div className="w-6 h-6 bg-white rounded-sm" />
          ) : (
            <svg className="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          )}
        </button>

        {/* Recording pulse animation */}
        {recordingState === 'recording' && (
          <div className="absolute inset-0 rounded-full border-4 border-red-500 animate-ping" />
        )}
      </div>

      {/* Duration display */}
      {recordingState === 'recording' && (
        <div className="text-2xl font-mono font-bold text-gray-800 mb-4">
          {formatDuration(duration)}
        </div>
      )}

      {/* Status text */}
      <div className="text-center">
        <div className="text-xs text-gray-400 mb-2">
          Debug: recordingState = "{recordingState}" | status = "{status}"
        </div>
        {recordingState === 'idle' && (
          <p className="text-gray-600">Tap to start recording</p>
        )}
        {recordingState === 'recording' && (
          <p className="text-red-600 font-medium">Recording... tap to stop</p>
        )}
        {recordingState === 'uploading' && (
          <p className="text-blue-600 font-medium">Uploading recording...</p>
        )}
        {recordingState === 'error' && (
          <div className="text-red-600">
            <p className="font-medium mb-1">Error</p>
            <p className="text-sm">{errorMessage}</p>
          </div>
        )}
      </div>

      {/* Format info */}
      {supportedFormat && (
        <div className="mt-6 text-xs text-gray-500 text-center">
          Recording format: {supportedFormat.name}
        </div>
      )}
    </div>
  );
}

export default function ClientOnlyRecordingInterface() {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Loading recording interface...</p>
        </div>
      </div>
    );
  }

  return <RecordingInterfaceCore />;
}