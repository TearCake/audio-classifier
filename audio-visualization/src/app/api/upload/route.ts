import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const audio_data = body?.audio_data

    if (!audio_data) {
      return NextResponse.json({ error: 'No audio_data provided' }, { status: 400 })
    }

    // TODO: replace mock response with real model inference backend
    const mockResponse = {
      predictions: [
        { class: 'dog', confidence: 0.85 },
        { class: 'rain', confidence: 0.1 },
        { class: 'car_horn', confidence: 0.05 },
      ],
      visualizations: {},
      input_spectogram: { shape: [1, 128], values: [] },
      waveform: { values: [], sample_rate: 44100, duration: 0 },
    }

    return NextResponse.json(mockResponse)
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
