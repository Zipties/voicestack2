'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Play, Pause, Volume2, Users, FileText } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
    speaker: {
      id: string
      name?: string
    }
  }>
}

interface Speaker {
  id: string
  name?: string
  is_trusted?: boolean
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
      
      // If job is completed, fetch transcript
      if (data.status === 'SUCCEEDED' && data.transcript) {
        fetchTranscript(data.transcript.id)
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
              
              {job.transcript?.title && (
                <div className="mb-4">
                  <h3 className="font-medium text-gray-900">{job.transcript.title}</h3>
                </div>
              )}
              
              {job.transcript?.summary && (
                <div className="mb-4">
                  <p className="text-gray-600">{job.transcript.summary}</p>
                </div>
              )}
              
              {/* Audio Player */}
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
              
              {/* Current Segment Highlight */}
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
            
            {/* Speakers Section */}
            <div className="mt-6">
              <h2 className="text-2xl font-bold tracking-tight">Speakers</h2>
              <div className="mt-4 space-y-3">
                {uniqueSpeakers.map(speaker => (
                  <SpeakerEditor key={speaker.id} speaker={speaker} onUpdate={fetchJobDetail} />
                ))}
              </div>
            </div>
            
            {/* Transcript View Component */}
            {job.transcript && <TranscriptView transcript={job.transcript} />}
            
            {/* Segments List */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Segments</h3>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {transcript.segments?.map((segment: Segment, index: number) => (
                  <div
                    key={segment.id}
                    className={`p-3 rounded-md border cursor-pointer transition-colors ${
                      currentSegment?.id === segment.id
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                    onClick={() => handleSeek(segment.start)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4 text-gray-500" />
                        <span className="font-medium text-sm">
                          {segment.speaker_name}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {Math.round(segment.start)}s - {Math.round(segment.end)}s
                      </span>
                    </div>
                    <p className="text-sm">{segment.text}</p>
                  </div>
                ))}
              </div>
            </div>
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

const TranscriptView = ({ transcript }: { transcript: Transcript }) => {
  if (!transcript || !transcript.segments || transcript.segments.length === 0) {
    return <p className="mt-4 text-gray-500">No transcript is available for this job.</p>;
  }

  return (
    <div className="mt-6">
      <h2 className="text-2xl font-bold tracking-tight">Transcript</h2>
      <ul className="mt-4 space-y-4">
        {transcript.segments.map((segment) => (
          <li key={segment.id} className="p-4 bg-white rounded-lg shadow">
            <p className="font-semibold text-indigo-600">{segment.speaker?.name || `Speaker #${segment.speaker.id}`}</p>
            <p className="mt-1 text-gray-800">{segment.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

const SpeakerEditor = ({ speaker, onUpdate }: { speaker: Speaker; onUpdate: () => void }) => {
  const [name, setName] = useState(speaker.name || '');
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return; // Prevent saving empty names
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/speakers/${speaker.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim() }),
    });
    setIsEditing(false);
    onUpdate(); // Refresh job data to show the new name everywhere
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="px-2 py-1 border rounded-md"
        />
        <button onClick={handleSave} className="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600">Save</button>
        <button onClick={() => setIsEditing(false)} className="px-3 py-1 bg-gray-300 rounded-md hover:bg-gray-400">Cancel</button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="font-medium">{speaker.name || `Speaker #${speaker.id}`}</span>
      <button onClick={() => setIsEditing(true)} className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600">Edit</button>
      
      <details className="mt-2">
        <summary className="cursor-pointer text-sm text-gray-500">View Embedding (Debug)</summary>
        <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
          {JSON.stringify(speaker.embedding, null, 2)}
        </pre>
      </details>
    </div>
  );
}; 