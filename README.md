## Audio Classifier & Visualizer

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-%5E2.0-red?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-stable-green?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.x-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/react-18.x-blue?logo=react&logoColor=white)](https://react.dev/)

I built this project as a small, local-first demo that stitches together a PyTorch audio classifier (ESC-50 style) with a Next.js visualizer UI. I followed a helpful YouTube tutorial to get started, then made several changes and improvements myself to fit my needs and learn the stack.

<img width="1920" height="1609" alt="image" src="https://github.com/user-attachments/assets/380e2285-1f83-416b-83f1-ca3bc4ba4c5c" />

## What it does
- Upload a WAV file from the browser and get back model predictions, an input spectrogram, and feature-map visualizations.
- Run inference with a PyTorch `AudioCNN` model and return structured JSON from a FastAPI endpoint.
- Render spectrograms and feature maps in the Next.js UI for quick inspection and debugging.

## Repo layout (at-a-glance)
- `main.py` — FastAPI inference server (loads `models/checkpoints/best_model.pth`)
- `model.py` — `AudioCNN` model and residual blocks
- `train.py` — training loop for ESC-50 style data (writes best checkpoint)
- `requirements.txt` — Python dependencies
- `audio-visualization/` — Next.js app (UI + proxy route for `/api/upload`)

## Quick start (development)

Prerequisites
- Python 3.10+ and a virtualenv (recommended)
- Node.js 18+ and npm
- Optional: CUDA drivers + GPU for faster PyTorch inference/training

Install Python deps

```bash
python -m venv .venv
# Windows: ./.venv/Scripts/activate
# macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Start the Python inference server (FastAPI + Uvicorn)

```bash
python main.py
```

Start the Next.js frontend

```bash
cd audio-visualization
npm install
npm run dev
```

Then open http://localhost:3000 and upload a .wav file. The frontend POSTs to `/api/upload`, which proxies to the Python service (default: http://127.0.0.1:8000/inference).

If your Python API is on a different host or port, set the `PYTHON_API_URL` environment variable for the Next app (audio-visualization/.env or export in shell).

## API contract

POST `/inference` (Python service)
- Request JSON: `{ "audio_data": "<base64-wav-bytes>" }`
- Success response (JSON) includes `predictions`, `visualization`, `input_spectrogram`, and `waveform`.

Example response:

```json
{
  "predictions": [{"class": "dog", "confidence": 0.85}],
  "visualization": {"layer_name": {"shape": [h,w], "values": [[...]]}},
  "input_spectrogram": {"shape": [h,w], "values": [[...]]},
  "waveform": {"values": [...], "sample_rate": 22050, "duration": 3.2}
}
```

Notes
- The frontend expects `input_spectrogram` and `visualization` keys; the Next `/api/upload` route proxies the body to the Python `/inference` endpoint and returns the JSON it receives.
- Spectrogram shape: `[n_mels, time_frames]` — the UI draws a heatmap from this 2D array.

## Development notes
- Audio is resampled to 22050 Hz during inference to match training transforms.
- Model checkpoint: `models/checkpoints/best_model.pth` (must exist for the server to load the trained model).
- For quick UI work you can temporarily return synthetic data from `audio-visualization/src/app/api/upload/route.ts`.

## Troubleshooting
- HTTP 404 / Not Found — check the Next `/api/upload` route and `PYTHON_API_URL`.
- Model not found — ensure `models/checkpoints/best_model.pth` exists and contains `model_state_dict` and `classes` keys.
- Large audio files — try cropping or sending a short clip; inference code may truncate/split audio.

## Acknowledgements
- This project started from a YouTube tutorial I followed; I adapted and extended the code to learn the stack and add the visualizer features.

## Contributing
- Open an issue or submit a PR. Keep changes focused and include tests where possible.

## License
This project is provided under the MIT License. See LICENSE for details.
