import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect

from backend.app.controllers.voice_controller import process_audio_turn, process_text_turn
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import build_rate_limit_key, rate_limiter
from backend.app.schemas.voice import AssistantResult, TextTurnRequest, TranscriptionResult
from backend.app.services.voice_service import voice_service


router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/text-turn", response_model=AssistantResult)
async def text_turn(payload: TextTurnRequest, request: Request):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "voice-text"),
        settings.voice_rate_limit_count,
        settings.voice_rate_limit_window_seconds,
    )
    return await asyncio.to_thread(process_text_turn, payload.text)


@router.post("/audio-turn", response_model=AssistantResult)
async def audio_turn(request: Request, audio: UploadFile = File(...)):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "voice-audio"),
        settings.voice_rate_limit_count,
        settings.voice_rate_limit_window_seconds,
    )
    suffix = Path(audio.filename or "input.webm").suffix or ".webm"
    content = await audio.read()
    return await asyncio.to_thread(process_audio_turn, suffix=suffix, content=content)


@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(request: Request, audio: UploadFile = File(...)):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "voice-transcribe"),
        settings.voice_rate_limit_count,
        settings.voice_rate_limit_window_seconds,
    )
    suffix = Path(audio.filename or "input.webm").suffix or ".webm"
    content = await audio.read()
    transcript = await asyncio.to_thread(voice_service.transcribe_audio, suffix=suffix, content=content)
    return TranscriptionResult(transcript=transcript)


@router.websocket("/stream")
async def voice_stream(ws: WebSocket):
    settings = get_settings()
    client_host = ws.client.host if ws.client else "anonymous"
    try:
        rate_limiter.enforce(
            f"voice-ws:{client_host}",
            settings.voice_rate_limit_count,
            settings.voice_rate_limit_window_seconds,
        )
    except HTTPException:
        await ws.close(code=1008, reason="Too many requests")
        return

    await ws.accept()
    try:
        while True:
            payload = await ws.receive_text()
            data = json.loads(payload)
            if data.get("type") != "user_text":
                continue

            user_text = (data.get("text") or "").strip()
            if not user_text:
                await ws.send_json({"type": "error", "message": "Empty text"})
                continue

            intent, token_stream = await asyncio.to_thread(voice_service.stream_response, user_text)
            final_text = ""
            for token in token_stream:
                final_text += token
                await ws.send_json({"type": "assistant_token", "token": token})

            final_text = final_text.strip()
            await ws.send_json({
                "type": "assistant_done",
                "intent": intent,
                "response_text": final_text,
                "transcript": user_text,
            })

            audio_chunks = await asyncio.to_thread(voice_service.synthesize_audio_chunks, final_text)
            if audio_chunks:
                for index, chunk in enumerate(audio_chunks):
                    await ws.send_json({
                        "type": "audio_chunk",
                        "index": index,
                        "data": chunk,
                    })
            await ws.send_json({"type": "audio_done"})
    except WebSocketDisconnect:
        return
