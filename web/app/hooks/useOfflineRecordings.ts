import { useState, useEffect, useCallback } from 'react';

export interface PendingRecording {
  id: string;
  blob: Blob;
  timestamp: number;
  duration: number;
  format: string;
}

const STORAGE_KEY = 'voicestack_pending_recordings';
const MAX_STORAGE_SIZE = 50 * 1024 * 1024; // 50MB limit

export function useOfflineRecordings() {
  const [pendingRecordings, setPendingRecordings] = useState<PendingRecording[]>([]);
  const [isOnline, setIsOnline] = useState(true);

  // Load pending recordings from localStorage on mount
  useEffect(() => {
    loadPendingRecordings();
  }, []);

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    setIsOnline(navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Auto-sync when coming back online
  useEffect(() => {
    if (isOnline && pendingRecordings.length > 0) {
      syncPendingRecordings();
    }
  }, [isOnline]);

  // Monitor page visibility for background sync
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isOnline && pendingRecordings.length > 0) {
        syncPendingRecordings();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isOnline, pendingRecordings.length]);

  const loadPendingRecordings = useCallback(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const recordings = JSON.parse(stored);
        setPendingRecordings(recordings.map((r: any) => ({
          ...r,
          blob: new Blob([new Uint8Array(r.blobData)], { type: r.format })
        })));
      }
    } catch (error) {
      console.error('Failed to load pending recordings:', error);
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const savePendingRecordings = useCallback((recordings: PendingRecording[]) => {
    try {
      const serializable = recordings.map(async (r) => ({
        id: r.id,
        timestamp: r.timestamp,
        duration: r.duration,
        format: r.format,
        blobData: Array.from(new Uint8Array(await r.blob.arrayBuffer()))
      }));

      Promise.all(serializable).then((data) => {
        const serialized = JSON.stringify(data);
        if (serialized.length > MAX_STORAGE_SIZE) {
          console.warn('Storage quota exceeded, removing oldest recordings');
          const reduced = recordings.slice(-Math.floor(recordings.length / 2));
          savePendingRecordings(reduced);
          return;
        }
        localStorage.setItem(STORAGE_KEY, serialized);
      });
    } catch (error) {
      console.error('Failed to save pending recordings:', error);
    }
  }, []);

  const addPendingRecording = useCallback((recording: PendingRecording) => {
    const updated = [...pendingRecordings, recording];
    setPendingRecordings(updated);
    savePendingRecordings(updated);
  }, [pendingRecordings, savePendingRecordings]);

  const removePendingRecording = useCallback((id: string) => {
    const updated = pendingRecordings.filter(r => r.id !== id);
    setPendingRecordings(updated);
    savePendingRecordings(updated);
  }, [pendingRecordings, savePendingRecordings]);

  const syncPendingRecordings = useCallback(async () => {
    if (!isOnline || pendingRecordings.length === 0) return;

    for (const recording of pendingRecordings) {
      try {
        const formData = new FormData();
        const file = new File(
          [recording.blob], 
          `recording_${recording.timestamp}.${recording.format.split('/')[1]}`,
          { type: recording.format }
        );
        formData.append('file', file);

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          removePendingRecording(recording.id);
        } else {
          console.error('Failed to upload recording:', response.statusText);
          break; // Stop trying if one fails
        }
      } catch (error) {
        console.error('Error uploading recording:', error);
        break; // Stop trying if one fails
      }
    }
  }, [isOnline, pendingRecordings, removePendingRecording]);

  const clearAllPendingRecordings = useCallback(() => {
    setPendingRecordings([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    pendingRecordings,
    isOnline,
    addPendingRecording,
    removePendingRecording,
    syncPendingRecordings,
    clearAllPendingRecordings
  };
}