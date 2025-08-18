import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.API_URL || 'http://api:8000'
const API_TOKEN = process.env.API_TOKEN || 'changeme'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${API_URL}/assets/${params.id}/audio`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch audio' },
        { status: response.status }
      )
    }

    // Stream the audio response
    const audioStream = response.body
    const headers = new Headers()
    
    // Copy relevant headers from the API response
    if (response.headers.get('content-type')) {
      headers.set('content-type', response.headers.get('content-type')!)
    }
    if (response.headers.get('content-length')) {
      headers.set('content-length', response.headers.get('content-length')!)
    }
    
    return new NextResponse(audioStream, {
      status: 200,
      headers,
    })
  } catch (error) {
    console.error('Audio proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}