'use client'

import React from 'react'
import { FileAudio, Users, Clock } from 'lucide-react'
import dynamic from 'next/dynamic'

const RecordingInterface = dynamic(
  () => import('./components/SimpleRecordingInterface'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Loading recording interface...</p>
        </div>
      </div>
    )
  }
)
import HamburgerMenu from './components/HamburgerMenu'

export default function HomePage() {

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {/* Hamburger Menu */}
      <HamburgerMenu />
      
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              VoiceStack2
            </h1>
            <p className="text-gray-600">
              Record, transcribe, and analyze audio with AI-powered speech recognition
            </p>
          </div>
          
          {/* Main Recording Interface */}
          <div className="bg-white rounded-lg shadow-lg mb-8">
            <RecordingInterface />
          </div>
          
          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <FileAudio className="w-8 h-8 text-blue-600 mr-3" />
                <h3 className="text-lg font-semibold">Speech Recognition</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Advanced ASR with word-level timestamps using faster-whisper
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <Users className="w-8 h-8 text-green-600 mr-3" />
                <h3 className="text-lg font-semibold">Speaker Identification</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Diarization and speaker embeddings with ECAPA
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <Clock className="w-8 h-8 text-purple-600 mr-3" />
                <h3 className="text-lg font-semibold">Real-time Processing</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Queue-based processing with progress tracking
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 