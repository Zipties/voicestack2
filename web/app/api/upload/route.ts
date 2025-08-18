import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.API_URL || 'http://api:8000'
const API_TOKEN = process.env.API_TOKEN || 'changeme'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    
    // Debug logging
    console.log('Upload proxy received request')
    const file = formData.get('file') as File
    if (file) {
      console.log(`File details: name=${file.name}, type=${file.type}, size=${file.size}`)
    }
    
    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: errorText || 'Upload failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Upload proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}