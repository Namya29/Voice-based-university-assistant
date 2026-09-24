from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .config import get_settings
from .schemas import AskRequest, AskResponse, SpeakRequest
from .rag import answer_question
from .azure_clients import issue_speech_token, synthesize_speech
from .auth import auth_router, get_current_user
from .partner_finder import partner_router

settings = get_settings()

app = FastAPI(title="University Voice Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(partner_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/api/config/languages")
def supported_languages():
    return {"languages": settings.supported_language_list}


@app.get("/api/speech/token")
async def speech_token():
    try:
        return await issue_speech_token()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Speech token error: {exc}")


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest, current_user: dict = Depends(get_current_user)):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = answer_question(payload.query, payload.language, payload.conversation_id)
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {exc}")


@app.post("/api/speak")
async def speak(payload: SpeakRequest, current_user: dict = Depends(get_current_user)):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        audio_bytes = await synthesize_speech(payload.text, payload.language)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"TTS error: {exc}")
