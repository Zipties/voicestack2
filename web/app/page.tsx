'use client'

import React, { useState } from 'react'
import { Upload, FileAudio, Users, Clock, AlertCircle, CheckCircle, List } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_TOKEN = 'changeme' // In production, this should be secure

// File size limit: 100MB
const MAX_FILE_SIZE = 100 * 1024 * 1024

// Supported file types
const SUPPORTED_TYPES = [
  'audio/mpeg',
  'audio/mp4',
  'audio/wav',
  'audio/ogg',
  'audio/webm',
  'video/mp4',
  'video/webm',
  'video/ogg',
  'video/quicktime'
]

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size must be less than ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)}MB`
    }

    // Check file type
    if (!SUPPORTED_TYPES.includes(file.type)) {
      return 'Unsupported file type. Please upload audio or video files.'
    }

    return null
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      const validationError = validateFile(selectedFile)
      if (validationError) {
        setError(validationError)
        setFile(null)
        // Reset the input
        e.target.value = ''
        return
      }
      
      setFile(selectedFile)
      setError(null)
      setSuccess(false)
      setJobId(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)
    setSuccess(false)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('params', JSON.stringify({
      whisper_model: 'base'
    }))

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_TOKEN}`
        },
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Upload failed: ${response.status} ${response.statusText}${errorText ? ` - ${errorText}` : ''}`)
      }

      const result = await response.json()
      
      if (!result.job_id) {
        throw new Error('No job ID received from server')
      }

      setJobId(result.job_id)
      setSuccess(true)
      setFile(null) // Clear the file input
      
      // Reset the file input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      if (fileInput) {
        fileInput.value = ''
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setSuccess(false)
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Navigation Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">
            VoiceStack2
          </h1>
          <div className="flex space-x-4">
            <a
              href="/jobs"
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <List className="w-4 h-4 mr-2" />
              View All Jobs
            </a>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            <Upload className="w-6 h-6 mr-2" />
            Upload Audio/Video
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File
              </label>
              <input
                type="file"
                accept="audio/*,video/*"
                onChange={handleFileChange}
                disabled={uploading}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">
                Supported formats: MP3, MP4, WAV, OGG, WebM. Max size: 100MB
              </p>
            </div>
            
            {file && (
              <div className="flex items-center space-x-2 text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                <FileAudio className="w-4 h-4" />
                <span className="font-medium">{file.name}</span>
                <span className="text-gray-500">({formatFileSize(file.size)})</span>
              </div>
            )}
            
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
            >
              {uploading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Uploading...
                </div>
              ) : (
                'Upload & Process'
              )}
            </button>
            
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <span className="text-red-800 font-medium">Error</span>
                </div>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            )}
            
            {success && jobId && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-green-800 font-medium">Upload Successful!</span>
                </div>
                <p className="text-green-700 text-sm mt-1">Job ID: {jobId}</p>
                <div className="mt-3 space-y-2">
                  <a
                    href={`/jobs/${jobId}`}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium inline-block"
                  >
                    View Job Details →
                  </a>
                  <br />
                  <a
                    href="/jobs"
                    className="text-gray-600 hover:text-gray-800 text-sm inline-block"
                  >
                    View All Jobs →
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
        
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
  )
} 