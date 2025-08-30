import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json()
    
    // Forward the request to the FastAPI backend
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/analyze-task-business-value`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    })
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to proxy request to backend', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}