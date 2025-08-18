import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.API_URL || 'http://api:8000'
const API_TOKEN = process.env.API_TOKEN || 'changeme'

// Force this route to be dynamic
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const timestamp = searchParams.get('_t')
    console.log('Jobs API route called at:', new Date().toISOString(), 'with timestamp:', timestamp)
    console.log('Fetching from:', `${API_URL}/jobs`)
    
    const response = await fetch(`${API_URL}/jobs?_=${Date.now()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      cache: 'no-store', // Disable caching to get fresh data
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch jobs' },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('Jobs API response - count:', data.length, 'latest:', data[0]?.id, data[0]?.created_at)
    
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    })
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}