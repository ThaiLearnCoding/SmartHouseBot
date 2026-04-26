# Smart Home Voice Assistant (Local AI + CoreIoT)

## 1. Project Overview

This project builds a **smart home voice assistant** that allows users to control IoT devices and check home environment conditions using natural language voice commands.

The system is designed with a **privacy-first local AI approach**:

- Voice is captured from a web interface.
- Speech-to-text is processed locally using Faster-Whisper.
- Command understanding and routing happen in the local backend.
- Device control is sent to CoreIoT through secure backend API calls.
- Voice responses are generated locally using Piper TTS.

This architecture reduces cloud dependency for AI processing while still using CoreIoT as the IoT control platform.

---

## 2. Problem Statement

Traditional smart home systems usually require users to interact through buttons, sliders, or dashboards. This can be less natural than spoken interaction.

This project addresses that by enabling users to:

1. Speak commands naturally.
2. Control smart home devices through voice.
3. Ask for current home status (temperature/humidity).
4. Receive spoken responses and simple recommendations.

Example:

> User: "Tell me the condition of the house today"
>
> Assistant: "It is 38 degrees Celsius with 32 percent humidity now. It feels hot. Drink more water, wear cool clothes, and avoid going outside unless needed."

---

## 3. System Architecture

### 3.1 IoT Layer

- ESP32-based device connected to CoreIoT
- Sensors: temperature and humidity
- Actuators: LED, servo (and optional fan)

### 3.2 Cloud / Platform Layer

- CoreIoT handles telemetry storage and RPC device control
- Dashboard configuration is available in `esp32.json`

### 3.3 Local AI Web Layer

- Web frontend captures microphone input
- Backend transcribes voice and maps to intents
- Backend executes CoreIoT actions and generates responses
- Piper TTS returns audio response to browser

---

## 4. Main Features

1. Voice command from browser
2. Local speech-to-text with Faster-Whisper
3. Smart home command parsing (LED, servo, sensor read)
4. Out-of-domain fallback (for unrelated questions)
5. House condition summary with practical advice
6. Optional local SLM response rewriting for natural and varied responses (Ollama)
7. Local text-to-speech response with Piper
8. Text fallback mode when microphone is unavailable

---

## 5. Project Structure

- `coreiot_rpc_controller.py`: CoreIoT login, RPC send, telemetry read
- `local_voice_assistant.py`: local terminal assistant (voice/text)
- `web_voice_server.py`: FastAPI backend for web voice pipeline
- `static/index.html`: web interface (mic + text + response audio)
- `esp32.json`: CoreIoT dashboard configuration
- `.env.example`: environment configuration template
- `requirements.txt`: Python dependencies
- `scripts/load_env.ps1`: load environment variables from `.env`
- `scripts/start_web.ps1`: start local web server quickly

---

## 6. Voice Pipeline

1. User presses record on website
2. Browser sends audio to backend
3. Faster-Whisper transcribes audio to text
4. Intent router classifies request:
   - In-domain action (control device)
   - In-domain information (read/summarize environment)
   - Out-of-domain (unexpected command)
5. Backend calls CoreIoT API when needed
6. Backend builds response text
7. Piper generates voice output
8. Website plays response audio

---

## 7. Out-of-Domain Handling

The system safely handles unexpected requests that are unrelated to smart-home control.

Example:

- User: "Where is my phone?"
- Assistant behavior:
  - Does not send any CoreIoT command
  - Returns fallback message explaining supported features

This prevents wrong actions and improves robustness.

---

## 8. Setup and Run

### 8.1 Install dependencies

```powershell
pip install -r requirements.txt
```

### 8.2 Prepare environment file

```powershell
copy .env.example .env
```

Fill values in `.env`:

- `COREIOT_EMAIL`
- `COREIOT_PASSWORD`
- `COREIOT_DEVICE_ID`
- `PIPER_PATH`
- `PIPER_MODEL`
- Whisper settings (optional)
- Optional LLM settings (`LLM_ENABLED`, `OLLAMA_MODEL`, ...)

### 8.3 Run web server

```powershell
uvicorn web_voice_server:app --host 0.0.0.0 --port 8000 --reload
```

Open browser at:

- `http://localhost:8000`

---

## 9. Sample Commands

- "bat den"
- "tat den"
- "quay servo 90 do"
- "doc nhiet do va do am"
- "tell me the condition of the house today"

---

## 10. What Must Be Installed Manually

Some parts cannot be auto-installed by this project code:

1. **FFmpeg** (required by Faster-Whisper audio processing)
2. **Piper executable**
3. **Piper voice model (.onnx)**
4. Browser microphone permission
5. HTTPS if testing microphone on non-localhost domains/devices
6. **Ollama + one local model** (only if you enable `LLM_ENABLED=true`)

### Optional: Enable local SLM for natural diverse outputs

1. Install Ollama locally.
2. Pull a small model, for example:

```powershell
ollama pull qwen2.5:3b-instruct
```

1. Update `.env`:

```text
LLM_ENABLED=true
LLM_BACKEND=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b-instruct
LLM_TEMPERATURE=0.8
```

1. Restart the web server.

With this mode enabled, device intent routing remains rule-based for safety, while final spoken responses become more natural and varied.

---

## 11. Security and Privacy Notes

- CoreIoT credentials stay on backend only
- Frontend never stores or sends CoreIoT password directly
- Speech processing is local when Faster-Whisper and Piper are local
- You can disable audio retention/logging for stronger privacy

---

## 12. Current Status and Next Improvements

### Completed

- CoreIoT device control integration
- Local web voice interface
- Local STT + local TTS pipeline
- Out-of-domain fallback handling

### Suggested Next Steps

1. Add confidence scoring and clarification questions
2. Improve Vietnamese NLU patterns and synonyms
3. Add command logs and latency metrics for evaluation report
4. Add authentication for multi-user web access
5. Package with Docker for easier deployment

---

## 13. Academic Contribution

This project demonstrates practical integration of:

- IoT systems (sensing + actuation)
- Cloud IoT platform orchestration (CoreIoT)
- Local AI speech pipeline (STT + NLU + TTS)
- Human-friendly voice interaction for smart home management

It provides a reusable foundation for future work on personalized smart home assistants with stronger privacy guarantees.
