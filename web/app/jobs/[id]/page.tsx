'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Play, Pause, Volume2, Users, FileText } from 'lucide-react'

const API_URL = '/api' // Use Next.js API routes

interface JobDetail {
  id: string
  status: string
  progress: number
  created_at: string
  updated_at: string
  log_path?: string
  asset?: {
    id: string
    input_path: string
    duration: number
  }
  transcript?: {
    id: string
    title: string
    summary: string
    raw_text: string
    segments?: any[]
  }
  artifacts?: {
    transcript_json: string
    transcript_txt: string
    transcript_srt: string
    transcript_vtt: string
    aligned_words: string
  }
}

interface Segment {
  id: string
  start: number
  end: number
  text: string
  speaker_name: string
  word_timings: any[]
}

interface Transcript {
  id: string
  title?: string
  summary?: string
  raw_text?: string
  segments?: Array<{
    id: string
    start: number
    end: number
    text: string
    original_speaker_label?: string
    speaker: {
      id: string
      name?: string
      original_label?: string
      match_confidence?: number
    }
  }>
}

interface Speaker {
  id: string
  name?: string
  is_trusted?: boolean
  original_label?: string
  match_confidence?: number
  embedding?: number[]
}

export default function JobDetailPage() {
  const params = useParams()
  const jobId = params.id as string
  
  const [job, setJob] = useState<JobDetail | null>(null)
  const [transcript, setTranscript] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null)

  useEffect(() => {
    fetchJobDetail()
  }, [jobId])

  const fetchJobDetail = async () => {
    try {
      const response = await fetch(`${API_URL}/jobs/${jobId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch job details')
      }
      const data = await response.json()
      setJob(data)
      
      // If job is completed and has transcript data, use it directly
      if (data.status === 'SUCCEEDED' && data.transcript) {
        setTranscript(data.transcript)
      } else if (data.status === 'SUCCEEDED') {
        // Fallback: try to fetch transcript using job ID if not included in job data
        fetchTranscript(jobId)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job details')
    } finally {
      setLoading(false)
    }
  }

  const fetchTranscript = async (transcriptId: string) => {
    try {
      const response = await fetch(`${API_URL}/transcripts/${transcriptId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch transcript')
      }
      const data = await response.json()
      setTranscript(data)
    } catch (err) {
      console.error('Failed to fetch transcript:', err)
    }
  }

  const handlePlayPause = () => {
    if (!audioElement) return
    
    if (isPlaying) {
      audioElement.pause()
    } else {
      audioElement.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleTimeUpdate = () => {
    if (audioElement) {
      setCurrentTime(audioElement.currentTime)
    }
  }

  const handleSeek = (time: number) => {
    if (audioElement) {
      audioElement.currentTime = time
      setCurrentTime(time)
    }
  }

  const getCurrentSegment = () => {
    if (!transcript?.segments) return null
    
    return transcript.segments.find((segment: Segment) => 
      currentTime >= segment.start && currentTime <= segment.end
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">Loading...</div>
        </div>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">{error || 'Job not found'}</div>
          </div>
        </div>
      </div>
    )
  }

  const currentSegment = getCurrentSegment()

  // Extract unique speakers from transcript
  const uniqueSpeakers = job.transcript?.segments
    ? Array.from(new Map(job.transcript.segments.map(seg => [seg.speaker.id, seg.speaker])).values())
    : [];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <a href="/jobs" className="text-blue-600 hover:text-blue-800">
            ← Back to Jobs
          </a>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-2xl font-bold mb-4">Job {job.id}</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <span className="text-sm text-gray-500">Status</span>
              <div className="font-medium">{job.status}</div>
            </div>
            <div>
              <span className="text-sm text-gray-500">Progress</span>
              <div className="font-medium">{job.progress}%</div>
            </div>
            <div>
              <span className="text-sm text-gray-500">Created</span>
              <div className="font-medium">
                {new Date(job.created_at).toLocaleString()}
              </div>
            </div>
          </div>
          
          {job.asset && (
            <div className="border-t pt-4">
              <h3 className="font-medium mb-2">Asset Info</h3>
              <div className="text-sm text-gray-600">
                Duration: {job.asset.duration ? `${Math.round(job.asset.duration)}s` : 'Unknown'}
              </div>
            </div>
          )}
        </div>
        
        {job.status === 'SUCCEEDED' && transcript && (
          <>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Transcript
              </h2>
              
              {/* Display the raw transcript text */}
              {transcript.raw_text && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                  <div className="whitespace-pre-wrap text-gray-800">{transcript.raw_text}</div>
                </div>
              )}
              
              {/* Audio Player - only show if we have an asset */}
              {job.asset && (
                <div className="mb-6">
                  <audio
                    ref={(el) => setAudioElement(el)}
                    onTimeUpdate={handleTimeUpdate}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    className="w-full"
                    controls
                  >
                    <source src={`${API_URL}/assets/${job.asset?.id}/audio`} type="audio/wav" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
              
              {/* Current Segment Highlight - only show if we have segments */}
              {currentSegment && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Users className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-blue-900">
                      {currentSegment.speaker_name}
                    </span>
                  </div>
                  <p className="text-blue-800">{currentSegment.text}</p>
                </div>
              )}
            </div>
            
            {/* Speakers Section - only show if we have segments with speakers */}
            {transcript.segments && transcript.segments.length > 0 && (
              <div className="mt-6">
                <h2 className="text-2xl font-bold tracking-tight">Speakers</h2>
                <div className="mt-4 space-y-3">
                  {uniqueSpeakers.map(speaker => (
                    <SpeakerEditor key={speaker.id} speaker={speaker} uniqueSpeakers={uniqueSpeakers} onUpdate={fetchJobDetail} />
                  ))}
                </div>
              </div>
            )}
            
            {/* Segments List - only show if we have segments */}
            {transcript.segments && transcript.segments.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">Segments</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {transcript.segments.map((segment: any, index: number) => (
                    <SegmentItem 
                      key={segment.id}
                      segment={segment}
                      uniqueSpeakers={uniqueSpeakers}
                      currentSegment={currentSegment}
                      onSeek={handleSeek}
                      onReassign={fetchJobDetail}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        
        {job.status === 'FAILED' && job.log_path && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <h3 className="font-medium text-red-900 mb-2">Error</h3>
            <p className="text-red-800 text-sm">{job.log_path}</p>
          </div>
        )}
      </div>
    </div>
  )
}

const SegmentItem = ({ 
  segment, 
  uniqueSpeakers, 
  currentSegment, 
  onSeek, 
  onReassign 
}: { 
  segment: any;
  uniqueSpeakers: Speaker[];
  currentSegment: any;
  onSeek: (time: number) => void;
  onReassign: () => void;
}) => {
  const [isReassigning, setIsReassigning] = useState(false);
  const [selectedSpeakerId, setSelectedSpeakerId] = useState(segment.speaker?.id || '');

  const handleReassignSpeaker = async (newSpeakerId: string) => {
    if (!newSpeakerId || newSpeakerId === segment.speaker?.id) return;

    setIsReassigning(true);
    try {
      const response = await fetch(`/api/transcripts/segments/${segment.id}/speaker`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speaker_id: newSpeakerId }),
      });

      if (!response.ok) {
        throw new Error('Failed to reassign segment speaker');
      }

      onReassign(); // Refresh the data
    } catch (error) {
      console.error('Failed to reassign speaker:', error);
      alert('Failed to reassign speaker. Please try again.');
    } finally {
      setIsReassigning(false);
    }
  };

  return (
    <div
      className={`p-3 rounded-md border transition-colors ${
        currentSegment?.id === segment.id
          ? 'bg-blue-50 border-blue-200'
          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={() => onSeek(segment.start)}>
          <Users className="w-4 h-4 text-gray-500" />
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm">
                {segment.speaker?.name || 'Unknown'}
              </span>
              {segment.original_speaker_label && (
                <span className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded font-mono">
                  {segment.original_speaker_label}
                </span>
              )}
            </div>
            {segment.speaker?.match_confidence !== null && segment.speaker?.match_confidence !== undefined && (
              <div className="text-xs text-gray-500">
                {segment.speaker.match_confidence > 0 ? 
                  `Matched (${(segment.speaker.match_confidence * 100).toFixed(1)}%)` : 
                  'New speaker'
                }
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={selectedSpeakerId}
            onChange={(e) => {
              setSelectedSpeakerId(e.target.value);
              handleReassignSpeaker(e.target.value);
            }}
            disabled={isReassigning}
            className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
          >
            <option value="">Reassign to...</option>
            {uniqueSpeakers.map((speaker) => (
              <option key={speaker.id} value={speaker.id}>
                {speaker.name || `Speaker #${speaker.id}`}
              </option>
            ))}
          </select>
          <span className="text-xs text-gray-500">
            {Math.round(segment.start)}s - {Math.round(segment.end)}s
          </span>
        </div>
      </div>
      <p className="text-sm cursor-pointer" onClick={() => onSeek(segment.start)}>{segment.text}</p>
    </div>
  );
};

const TranscriptView = ({ transcript }: { transcript: Transcript }) => {
  if (!transcript || !transcript.segments || transcript.segments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold tracking-tight mb-4">Transcript</h2>
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500 text-lg">No transcript is available for this job.</p>
          <p className="text-gray-400 text-sm mt-1">The transcript will appear here once processing is complete.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold tracking-tight mb-4">Transcript</h2>
      
      {/* Transcript Summary - only show title if it's reasonably short (not full transcript) */}
      {((transcript.title && transcript.title.length < 100) || transcript.summary) && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          {transcript.title && transcript.title.length < 100 && (
            <h3 className="text-lg font-semibold text-blue-900 mb-2">{transcript.title}</h3>
          )}
          {transcript.summary && (
            <p className="text-blue-800">{transcript.summary}</p>
          )}
        </div>
      )}
      
      {/* Transcript Segments */}
      <div className="space-y-4">
        {transcript.segments.map((segment, index) => (
          <div key={segment.id} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
            <div className="flex items-start gap-3">
              {/* Speaker Avatar */}
              <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Users className="w-4 h-4 text-indigo-600" />
              </div>
              
              {/* Segment Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-indigo-600">
                    {segment.speaker?.name || `Speaker #${segment.speaker?.id || 'Unknown'}`}
                  </span>
                  <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full">
                    {Math.round(segment.start)}s - {Math.round(segment.end)}s
                  </span>
                </div>
                <p className="text-gray-800 leading-relaxed">{segment.text}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Transcript Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Total segments: {transcript.segments.length}</span>
          <span>Duration: {transcript.segments.length > 0 ? 
            `${Math.round(transcript.segments[transcript.segments.length - 1].end)}s` : '0s'
          }</span>
        </div>
      </div>
    </div>
  );
};

const SpeakerMergeButton = ({ speaker, uniqueSpeakers, onUpdate }: { speaker: Speaker; uniqueSpeakers: Speaker[]; onUpdate: () => void }) => {
  const [isConfirming, setIsConfirming] = useState(false);
  const [selectedTargetId, setSelectedTargetId] = useState('');
  const [isMerging, setIsMerging] = useState(false);

  const handleMerge = async () => {
    if (!selectedTargetId) return;

    setIsMerging(true);
    try {
      const response = await fetch('/api/speakers/merge', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer changeme' // TODO: Use proper auth
        },
        body: JSON.stringify({
          source_speaker_id: speaker.id,
          target_speaker_id: selectedTargetId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to merge speakers');
      }

      setIsConfirming(false);
      setSelectedTargetId('');
      onUpdate(); // Refresh the data
    } catch (error) {
      console.error('Failed to merge speakers:', error);
      alert('Failed to merge speakers. Please try again.');
    } finally {
      setIsMerging(false);
    }
  };

  // Only show merge button if there are other speakers to merge with
  const otherSpeakers = uniqueSpeakers.filter(s => s.id !== speaker.id);
  if (otherSpeakers.length === 0) return null;

  if (isConfirming) {
    return (
      <div className="flex items-center gap-2">
        <select
          value={selectedTargetId}
          onChange={(e) => setSelectedTargetId(e.target.value)}
          className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        >
          <option value="">Merge with...</option>
          {otherSpeakers.map((targetSpeaker) => (
            <option key={targetSpeaker.id} value={targetSpeaker.id}>
              {targetSpeaker.name || `Speaker #${targetSpeaker.id}`}
            </option>
          ))}
        </select>
        <button 
          onClick={handleMerge}
          disabled={!selectedTargetId || isMerging}
          className="px-2 py-1 bg-orange-500 text-white rounded text-xs hover:bg-orange-600 disabled:opacity-50"
        >
          {isMerging ? 'Merging...' : 'Confirm'}
        </button>
        <button 
          onClick={() => {
            setIsConfirming(false);
            setSelectedTargetId('');
          }}
          className="px-2 py-1 bg-gray-300 text-gray-700 rounded text-xs hover:bg-gray-400"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button 
      onClick={() => setIsConfirming(true)} 
      className="px-3 py-1 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors text-sm"
    >
      Merge
    </button>
  );
};

const SpeakerEditor = ({ speaker, uniqueSpeakers, onUpdate }: { speaker: Speaker; uniqueSpeakers: Speaker[]; onUpdate: () => void }) => {
  const [name, setName] = useState(speaker.name || '');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return; // Prevent saving empty names
    
    setIsSaving(true);
    try {
      const response = await fetch(`/api/speakers/${speaker.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update speaker name');
      }
      
      setIsEditing(false);
      onUpdate(); // Refresh job data to show the new name everywhere
    } catch (error) {
      console.error('Failed to update speaker:', error);
      alert('Failed to update speaker name. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setName(speaker.name || ''); // Reset to original name
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 border border-blue-200">
        <div className="flex items-center gap-3 mb-3">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter speaker name"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') handleCancel();
            }}
            autoFocus
          />
          <button 
            onClick={handleSave} 
            disabled={isSaving || !name.trim()}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button 
            onClick={handleCancel}
            disabled={isSaving}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900">
                {speaker.name || `Speaker #${speaker.id}`}
              </span>
              {speaker.original_label && (
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full font-mono">
                  {speaker.original_label}
                </span>
              )}
              {speaker.is_trusted && (
                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                  Trusted
                </span>
              )}
            </div>
            {speaker.match_confidence !== null && speaker.match_confidence !== undefined && (
              <div className="text-xs text-gray-500 mt-1">
                {speaker.match_confidence > 0 ? (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    Matched ({(speaker.match_confidence * 100).toFixed(1)}% confidence)
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                    New speaker
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setIsEditing(true)} 
            className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
          >
            Edit Name
          </button>
          <SpeakerMergeButton speaker={speaker} uniqueSpeakers={uniqueSpeakers} onUpdate={onUpdate} />
        </div>
      </div>
      
      {/* Embedding Debug View */}
      {speaker.embedding && (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 transition-colors">
            🔍 View Voice Embedding (Debug)
          </summary>
          <div className="mt-2 p-3 bg-gray-50 rounded-md">
            <div className="text-xs text-gray-600 mb-2">
              Vector dimensions: {speaker.embedding.length}
            </div>
            <pre className="text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(speaker.embedding.slice(0, 10), null, 2)}
              {speaker.embedding.length > 10 && `\n... and ${speaker.embedding.length - 10} more dimensions`}
            </pre>
          </div>
        </details>
      )}
    </div>
  );
}; 