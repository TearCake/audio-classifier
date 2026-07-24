import { NextResponse } from "next/server";

type UploadBody = {
  audio_data?: unknown;
};

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as UploadBody;
    const audioData = body.audio_data;

    if (typeof audioData !== "string" || !audioData) {
      return NextResponse.json(
        { error: "No audio_data provided" },
        { status: 400 },
      );
    }

    const pythonApiUrl = process.env.PYTHON_API_URL ?? "http://127.0.0.1:8000";
    const response = await fetch(`${pythonApiUrl}/inference`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ audio_data: audioData }),
    });

    if (!response.ok) {
      const detail = await response.text();
      return NextResponse.json(
        { error: `Python inference failed: ${detail}` },
        { status: response.status },
      );
    }

    const data = (await response.json()) as unknown;
    return NextResponse.json(data);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}