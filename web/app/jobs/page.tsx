'use client'

import React, { useEffect, useState } from 'react'
import { Clock, CheckCircle, XCircle, AlertCircle, Play, Home, Upload, Wifi, WifiOff } from 'lucide-react'

const API_URL = '/api' // Use Next.js API routes

interface Job {
  id: string
  status: string
  progress: number
  created_at: string
  updated_at: string
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isOnline, setIsOnline] = useState(true)
  const [debugInfo, setDebugInfo] = useState<string>('')
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    // Network status detection
    const handleOnline = () => {
      setIsOnline(true)
      setDebugInfo(prev => prev + '\n[NETWORK] Back online')
    }
    const handleOffline = () => {
      setIsOnline(false)
      setDebugInfo(prev => prev + '\n[NETWORK] Gone offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    // Initial network status
    setIsOnline(navigator.onLine)
    
    // iOS Safari specific debugging
    const userAgent = navigator.userAgent
    const isIOS = /iPad|iPhone|iPod/.test(userAgent)
    const isSafari = /Safari/.test(userAgent) && !/Chrome/.test(userAgent)
    
    setDebugInfo(`[INIT] UA: ${userAgent.substring(0, 50)}...\n[INIT] iOS: ${isIOS}, Safari: ${isSafari}, Online: ${navigator.onLine}`)
    
    fetchJobs()
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const fetchJobs = async (retry = false) => {
    const startTime = Date.now()
    
    try {
      setDebugInfo(prev => prev + `\n[FETCH] Starting API call to ${API_URL}/jobs`)
      
      // Enhanced fetch with timeout and headers
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10s timeout
      
      const response = await fetch(`${API_URL}/jobs?_t=${Date.now()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      const duration = Date.now() - startTime
      
      setDebugInfo(prev => prev + `\n[FETCH] Response: ${response.status} in ${duration}ms`)
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`)
      }
      
      const data = await response.json()
      setJobs(data)
      setError(null)
      setRetryCount(0)
      
      setDebugInfo(prev => prev + `\n[SUCCESS] Loaded ${data.length} jobs`)
      
    } catch (err) {
      const duration = Date.now() - startTime
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      
      setDebugInfo(prev => prev + `\n[ERROR] ${errorMsg} (${duration}ms)`)
      
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out. Please check your connection.')
      } else if (!isOnline) {
        setError('No internet connection. Please check your network.')
      } else if (retryCount < 2 && !retry) {
        setDebugInfo(prev => prev + `\n[RETRY] Attempting retry ${retryCount + 1}`)
        setRetryCount(prev => prev + 1)
        setTimeout(() => fetchJobs(true), 1000)
        return
      } else {
        setError(`Failed to load jobs: ${errorMsg}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <Play className="w-4 h-4 text-blue-600" />
      case 'SUCCEEDED':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-600" />
      case 'CANCELLED':
        return <AlertCircle className="w-4 h-4 text-yellow-600" />
      default:
        return <Clock className="w-4 h-4 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'text-blue-600'
      case 'SUCCEEDED':
        return 'text-green-600'
      case 'FAILED':
        return 'text-red-600'
      case 'CANCELLED':
        return 'text-yellow-600'
      default:
        return 'text-gray-600'
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold">Jobs</h1>
            <a
              href="/"
              className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              <Home className="w-4 h-4 mr-2" />
              Back to Home
            </a>
          </div>
          <div className="text-center">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Navigation Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center space-x-4">
            <h1 className="text-3xl font-bold">Jobs</h1>
            {/* Network Status Indicator */}
            <div className={`flex items-center px-2 py-1 rounded-full text-xs ${
              isOnline ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {isOnline ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
              {isOnline ? 'Online' : 'Offline'}
            </div>
          </div>
          <a
            href="/"
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            <Home className="w-4 h-4 mr-2" />
            Back to Home
          </a>
        </div>
        
        {/* Debug Info Panel */}
        {debugInfo && (
          <details className="mb-6 bg-gray-50 border border-gray-200 rounded-md">
            <summary className="cursor-pointer p-3 text-sm font-medium text-gray-700 hover:bg-gray-100">
              🔍 Debug Information (Tap to view)
            </summary>
            <pre className="p-3 text-xs text-gray-600 whitespace-pre-wrap overflow-x-auto border-t border-gray-200">
              {debugInfo}
            </pre>
          </details>
        )}
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="text-red-800">{error}</div>
              <button
                onClick={() => {
                  setError(null)
                  setLoading(true)
                  setRetryCount(0)
                  fetchJobs()
                }}
                className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        )}
        
        {jobs.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs yet</h3>
            <p className="text-gray-600 mb-4">Upload a file to get started</p>
            <a
              href="/"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload File
            </a>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Recent Jobs</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {jobs.map((job) => (
                <div key={job.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className={`font-medium ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                          {job.status === 'RUNNING' && (
                            <span className="text-sm text-gray-500">
                              {job.progress}%
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(job.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <a
                        href={`/jobs/${job.id}`}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View Details →
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 