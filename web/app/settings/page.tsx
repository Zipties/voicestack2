'use client'

import React from 'react'
import { Settings, Home } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Navigation Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Settings
          </h1>
          <a
            href="/"
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            <Home className="w-4 h-4 mr-2" />
            Back to Home
          </a>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            <Settings className="w-6 h-6 mr-2" />
            Application Settings
          </h2>
          
          <div className="space-y-6">
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Audio Recording</h3>
              <p className="text-gray-600 text-sm">
                Recording settings and preferences are automatically detected based on your browser capabilities.
              </p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Speech Recognition</h3>
              <p className="text-gray-600 text-sm mb-2">
                Model: Faster-Whisper Base
              </p>
              <p className="text-gray-600 text-sm">
                Provides fast and accurate speech-to-text conversion with word-level timestamps.
              </p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Speaker Identification</h3>
              <p className="text-gray-600 text-sm">
                Automatic speaker diarization using ECAPA-TDNN embeddings for multi-speaker audio.
              </p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Data Storage</h3>
              <p className="text-gray-600 text-sm">
                Recordings are stored locally and processed on your system. Offline recordings are saved in browser storage until upload.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}