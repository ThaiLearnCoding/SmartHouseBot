# Smart Home Dashboard

`SmartHouseBot` is now structured as a full-stack smart home dashboard with:

- a React 19 + Vite frontend in `frontend/`
- a modular FastAPI backend in `backend/`
- local speech-to-text with `faster-whisper`
- local speech synthesis with `piper-tts`
- CoreIoT RPC and telemetry integration

The app provides a production-oriented baseline for a smart home dashboard that supports live telemetry, device controls, and a browser-based voice assistant.

## Architecture

### Frontend

- React 19 via Vite
- TailwindCSS + daisyUI
- Zustand for dashboard and voice assistant state
- Axios for API access
- Recharts for telemetry visualization

### Backend

- FastAPI application in `backend/app`
- Routers split by feature area:
  - `backend/app/routers/health.py`
  - `backend/app/routers/devices.py`
  - `backend/app/routers/telemetry.py`
  - `backend/app/routers/voice.py`
- Service layer for:
  - CoreIoT access
  - voice orchestration
  - Whisper transcription
  - Piper TTS synthesis
  - intent parsing

## Folder Layout

```text
SmartHouseBot/
  backend/
    app/
      clients/
      controllers/
      core/
      middleware/
      routers/
      schemas/
      services/
      main.py
  frontend/
    src/
      components/
      lib/
      pages/
      services/
      store/
  package.json
  requirements.txt
  .env.example
  web_voice_server.py
```

`web_voice_server.py` is kept as a compatibility entrypoint and now re-exports the new FastAPI app.

## API Endpoints

### Health

- `GET /api/health`

### Devices

- `GET /api/devices/status`
- `POST /api/devices/led`
- `POST /api/devices/servo`

### Telemetry

- `GET /api/telemetry/latest`
- `GET /api/telemetry/history?range_hours=24`

### Voice

- `POST /api/voice/text-turn`
- `POST /api/voice/audio-turn`

## Environment Variables

Copy `.env.example` to `.env` and fill in at least:

```bash
cp .env.example .env
```

Required values:

- `COREIOT_EMAIL`
- `COREIOT_PASSWORD`
- `COREIOT_DEVICE_ID`
- `PIPER_MODEL`

Common optional values:

- `CLIENT_URL`
- `CORS_ORIGINS`
- `WHISPER_MODEL_SIZE`
- `WHISPER_DEVICE`
- `WHISPER_LANGUAGE`
- `LLM_ENABLED`
- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `VOICE_RATE_LIMIT_COUNT`
- `DEVICE_RATE_LIMIT_COUNT`
- `TELEMETRY_LIMIT_POINTS`

## Local Development

### 1. Python dependencies

Create or activate your virtual environment, then install backend requirements:

```bash
pip install -r requirements.txt
```

### 2. Root tooling

Install the root development dependency for concurrent running:

```bash
npm install
```

### 3. Frontend dependencies

Install the React app dependencies:

```bash
cd frontend
npm install
cd ..
```

### 4. Run both apps together

From the project root:

```bash
npm run dev
```

This starts:

- FastAPI on `http://localhost:8000`
- Vite on `http://localhost:5173`

### 5. Run backend only

```bash
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Compatibility entrypoint:

```bash
python3 -m uvicorn web_voice_server:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Run frontend only

```bash
cd frontend
npm run dev
```

## Production Build

Build the frontend bundle:

```bash
npm run build
```

The Vite output is generated in `frontend/dist`. The FastAPI app automatically serves that built SPA when the directory exists.

## Production Serving

### Uvicorn

```bash
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Gunicorn + Uvicorn workers

```bash
gunicorn backend.app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```