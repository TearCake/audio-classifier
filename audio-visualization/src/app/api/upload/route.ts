import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const audio_data = body?.audio_data

    if (!audio_data) {
      return NextResponse.json({ error: 'No audio_data provided' }, { status: 400 })
    }

    const pythonApiUrl = process.env.PYTHON_API_URL ?? 'http://127.0.0.1:8000'
    const response = await fetch(`${pythonApiUrl}/inference`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ audio_data }),
    })

    if (!response.ok) {
      const detail = await response.text()
      return NextResponse.json(
        { error: `Python inference failed: ${detail}` },
        { status: response.status },
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
