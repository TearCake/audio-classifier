# Audio Classifier & Visualizer

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/next.js-15.x-black)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

Professional demo project that runs a PyTorch audio classifier (ESC-50 style) and a Next.js visualizer UI. The Next frontend uploads WAV files, the Python FastAPI backend runs inference and returns predictions, feature maps and an input spectrogram which the UI renders.

--

## Features
- Single-file upload UI with spectrogram and feature-map visualizations
- PyTorch `AudioCNN` model with feature-map extraction
- FastAPI inference endpoint (serves `input_spectrogram`, `visualization`, `predictions`, `waveform`)
- Local-first dev flow: run Python server + Next dev server

## Repository layout
- `main.py` — FastAPI inference server (loads `models/checkpoints/best_model.pth`)
- `model.py` — `AudioCNN` model and Residual blocks
- `train.py` — training loop for ESC-50 dataset (writes best checkpoint)
- `requirements.txt` — Python dependencies
- `audio-visualization/` — Next.js app (UI + proxy route for `/api/upload`)

## Quick start (development)

Prerequisites
- Python 3.10+ and a virtualenv (recommended)
- Node.js 18+ / npm
- (Optional GPU) CUDA drivers and compatible PyTorch

Install Python deps

Run: python -m venv .venv
Then: source .venv/bin/activate   # Windows: ./.venv/Scripts/activate
Then: pip install -r requirements.txt

Start the Python inference server (FastAPI + Uvicorn)

Run: python main.py

Start the Next.js frontend

Run: cd "audio-visualization"
Run: npm install
Run: npm run dev

Open http://localhost:3000 and upload a .wav file. The frontend will POST to /api/upload, which proxies to the Python service (default: http://127.0.0.1:8000/inference).

If your Python API is on a different host or port, set the PYTHON_API_URL environment variable in the Next app before starting (audio-visualization/.env or export in shell).

## API contract

POST /inference (Python service)
- Request JSON: { "audio_data": "<base64-wav-bytes>" }
- Success response (JSON):

Example response:

{
  "predictions": [{"class":"dog","confidence":0.85}],
  "visualization": {"layer_name": {"shape": [h,w], "values": [[...]]}},
  "input_spectrogram": {"shape": [h,w], "values": [[...]]},
  "waveform": {"values": [...], "sample_rate": 22050, "duration": 3.2}
}

Notes:
- The frontend expects `input_spectrogram` and `visualization` keys. The Next `/api/upload` route proxies the body to the Python `/inference` endpoint and returns its JSON.
- Spectrogram shape: `[n_mels, time_frames]` — the UI draws a heatmap from this 2D array.

## Development notes
- The project resamples audio to 22050 Hz during inference to match training transforms.
- Model checkpoint: `models/checkpoints/best_model.pth` (must exist for the server to load the trained model).
- If you want to bypass the Python service for frontend work, the Next API route used to return synthetic data — you can re-enable that for quick UI dev (see `audio-visualization/src/app/api/upload/route.ts`).

## Troubleshooting
- HTTP error! Not Found — ensure the Next app includes the `/api/upload` route and that it can reach the Python server (`PYTHON_API_URL`).
- Model not found — confirm `models/checkpoints/best_model.pth` exists and contains `model_state_dict` and `classes` keys.
- Large audio files — consider cropping or sending a short clip; the inference code may sample/reduce waveform length for the waveform return.

## Contributing
- Open an issue or submit a PR. Keep changes focused and include tests where possible.

## License
This project is provided under the MIT License. See LICENSE for details.
