'use client';

import { useState, useEffect, useRef } from 'react';
import { getSupportedAudioFormat, isRecordingSupported } from '../utils/formatSupport';

interface Job {
  id: string;
  status: string;
  progress: number;
  created_at: string;
}

export default function SimpleRecordingInterface() {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [showRecentJobs, setShowRecentJobs] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchRecentJobs();
    
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const fetchRecentJobs = async () => {
    try {
      // Add timestamp to force cache busting
      const timestamp = Date.now();
      const response = await fetch(`/api/jobs?_t=${timestamp}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      });
      
      if (response.ok) {
        const jobs = await response.json();
        console.log('Fetched jobs at', new Date().toISOString(), '- latest:', jobs[0]?.id, jobs[0]?.created_at);
        // Show only the 3 most recent jobs
        setRecentJobs(jobs.slice(0, 3));
      }
    } catch (error) {
      console.error('Failed to fetch recent jobs:', error);
    }
  };

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
    setUploadStatus('uploading');
    setUploadMessage('Uploading recording...');
    setErrorMessage('');

    try {
      const formData = new FormData();
      const filename = `recording_${Date.now()}.webm`;
      const file = new File([blob], filename, { type: 'audio/webm' });
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Upload successful:', result);
        
        setUploadStatus('success');
        if (result.job_id) {
          setUploadMessage(`Recording uploaded successfully! Job ID: ${result.job_id}`);
          // Immediately add this job to recent jobs to show user it was processed
          const newJob = {
            id: result.job_id,
            status: 'RUNNING',
            progress: 0,
            created_at: new Date().toISOString()
          };
          setRecentJobs(prev => [newJob, ...prev.slice(0, 2)]);
        } else {
          setUploadMessage('Recording uploaded successfully!');
        }
        
        // Refresh recent jobs after successful upload
        setTimeout(() => {
          fetchRecentJobs();
          setUploadStatus('idle');
          setUploadMessage('');
        }, 3000);
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Upload failed:', response.statusText, errorData);
        setUploadStatus('error');
        setUploadMessage(`Upload failed: ${errorData.error || response.statusText}`);
        setTimeout(() => {
          setUploadStatus('idle');
          setUploadMessage('');
        }, 5000);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setUploadMessage(`Upload error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadMessage('');
      }, 5000);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return '🔄';
      case 'SUCCEEDED':
        return '✅';
      case 'FAILED':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'text-blue-600';
      case 'SUCCEEDED':
        return 'text-green-600';
      case 'FAILED':
        return 'text-red-600';
      default:
        return 'text-gray-600';
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
        Debug: isRecording = {isRecording ? 'true' : 'false'} | duration = {duration} | Component loaded at: {new Date().toLocaleTimeString()}
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
        disabled={uploadStatus === 'uploading'}
        className={`w-32 h-32 rounded-full border-4 transition-all duration-200 flex items-center justify-center ${
          uploadStatus === 'uploading'
            ? 'bg-gray-400 border-gray-500 cursor-not-allowed'
            : isRecording
            ? 'bg-red-500 border-red-600 hover:bg-red-600 cursor-pointer'
            : 'bg-white border-gray-300 hover:border-gray-400 shadow-lg cursor-pointer'
        }`}
        style={{ pointerEvents: 'auto', zIndex: 9999, position: 'relative' }}
      >
        {uploadStatus === 'uploading' ? (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        ) : isRecording ? (
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
        ) : uploadStatus === 'uploading' ? (
          <p className="text-blue-600 font-medium">Processing recording...</p>
        ) : uploadStatus === 'success' ? (
          <p className="text-green-600 font-medium">Recording processed successfully!</p>
        ) : uploadStatus === 'error' ? (
          <p className="text-red-600 font-medium">Upload failed</p>
        ) : (
          <p className="text-gray-600">Click to start recording</p>
        )}
      </div>

      {/* Upload status message */}
      {uploadMessage && (
        <div className={`mt-4 text-sm text-center p-3 rounded-md ${
          uploadStatus === 'uploading' ? 'bg-blue-50 text-blue-800' :
          uploadStatus === 'success' ? 'bg-green-50 text-green-800' :
          uploadStatus === 'error' ? 'bg-red-50 text-red-800' :
          'bg-gray-50 text-gray-800'
        }`}>
          {uploadStatus === 'uploading' && (
            <div className="flex items-center justify-center mb-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            </div>
          )}
          {uploadMessage}
        </div>
      )}

      {/* Error message */}
      {errorMessage && (
        <div className="mt-4 text-red-600 text-sm">
          {errorMessage}
        </div>
      )}

      {/* Recent Jobs Toggle */}
      {recentJobs.length > 0 && (
        <div className="mt-6">
          <button
            onClick={() => setShowRecentJobs(!showRecentJobs)}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            {showRecentJobs ? '▼' : '▶'} Recent Recordings ({recentJobs.length})
          </button>
          
          {showRecentJobs && (
            <div className="mt-3 space-y-2">
              {recentJobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md border hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{getStatusIcon(job.status)}</span>
                    <div>
                      <div className={`text-sm font-medium ${getStatusColor(job.status)}`}>
                        {job.status}
                        {job.status === 'RUNNING' && ` (${job.progress}%)`}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(job.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <a
                    href={`/jobs/${job.id}`}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View →
                  </a>
                </div>
              ))}
              <div className="text-center pt-2">
                <a
                  href="/jobs"
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  View All Jobs →
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}