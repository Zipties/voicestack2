import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.API_URL || 'http://api:8000'
const API_TOKEN = process.env.API_TOKEN || 'changeme'

// Force this route to be completely dynamic
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(request: NextRequest) {
  console.log('FRESH JOBS ROUTE - Called at:', new Date().toISOString())
  
  try {
    const response = await fetch(`${API_URL}/jobs`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      console.log('API response not OK:', response.status)
      return NextResponse.json(
        { error: 'Failed to fetch jobs' },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('FRESH JOBS ROUTE - Got', data.length, 'jobs, latest:', data[0]?.id)
    
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    })
  } catch (error) {
    console.error('Fresh jobs route error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}