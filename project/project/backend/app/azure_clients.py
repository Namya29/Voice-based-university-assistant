"""Thin wrappers around Azure/Foundry SDKs. Every secret is read from Settings only."""
import time
import httpx
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from .config import get_settings

settings = get_settings()


def _is_placeholder(val: str | None) -> bool:
    if not val:
        return True
    val_lower = val.lower()
    return (
        "replace_with" in val_lower
        or "<your-" in val_lower
        or "example.com" in val_lower
        or "your-search-service" in val_lower
    )


def get_foundry_client() -> AzureOpenAI | None:
    if _is_placeholder(settings.foundry_project_endpoint) or _is_placeholder(settings.foundry_api_key):
        return None
    try:
        return AzureOpenAI(
            azure_endpoint=settings.foundry_project_endpoint,
            api_key=settings.foundry_api_key,
            api_version=settings.foundry_api_version,
        )
    except Exception:
        return None


def get_search_client() -> SearchClient | None:
    if _is_placeholder(settings.azure_search_endpoint) or _is_placeholder(settings.azure_search_key):
        return None
    try:
        return SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index,
            credential=AzureKeyCredential(settings.azure_search_key),
        )
    except Exception:
        return None


def embed_text(text: str) -> list[float]:
    client = get_foundry_client()
    if not client:
        raise ValueError("Azure OpenAI client is not configured with valid credentials.")
    resp = client.embeddings.create(
        model=settings.foundry_embedding_deployment,
        input=text,
    )
    return resp.data[0].embedding


def vector_search(query: str, top_k: int | None = None):
    s_client = get_search_client()
    if not s_client:
        raise ValueError("Azure Search client is not configured with valid credentials.")
    vector = embed_text(query)
    vq = VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=top_k or settings.azure_search_top_k,
        fields="content_vector",
    )
    results = s_client.search(
        search_text=None,
        vector_queries=[vq],
        select=["id", "title", "url", "page", "content"],
        top=top_k or settings.azure_search_top_k,
    )
    hits = []
    for r in results:
        score = r.get("@search.score", 0.0)
        if score >= settings.azure_search_min_score:
            hits.append(
                {
                    "id": r["id"],
                    "title": r.get("title", "Untitled document"),
                    "url": r.get("url"),
                    "page": r.get("page"),
                    "content": r["content"],
                    "score": score,
                }
            )
    return hits


def chat_complete(system_prompt: str, user_prompt: str) -> str:
    client = get_foundry_client()
    if not client:
        raise ValueError("Azure OpenAI client is not configured with valid credentials.")
    resp = client.chat.completions.create(
        model=settings.foundry_chat_deployment,
        temperature=0.2,
        max_tokens=600,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content.strip()


async def issue_speech_token() -> dict:
    if _is_placeholder(settings.azure_speech_key) or _is_placeholder(settings.azure_speech_region):
        raise ValueError("Azure Speech API key is not configured.")
    url = f"https://{settings.azure_speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url, headers={"Ocp-Apim-Subscription-Key": settings.azure_speech_key}
        )
        resp.raise_for_status()
        return {
            "token": resp.text,
            "region": settings.azure_speech_region,
            "expires_at": int(time.time()) + settings.azure_speech_token_ttl_seconds,
        }


VOICE_MAP = {
    "en-US": "en-US-JennyNeural",
    "en-IN": "en-IN-NeerjaNeural",
    "hi-IN": "hi-IN-SwaraNeural",
    "pa-IN": "pa-IN-VaaniNeural",
    "es-ES": "es-ES-ElviraNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "de-DE": "de-DE-KatjaNeural",
    "ar-SA": "ar-SA-ZariyahNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "ja-JP": "ja-JP-NanamiNeural",
    "ko-KR": "ko-KR-SunHiNeural",
    "ru-RU": "ru-RU-SvetlanaNeural",
    "it-IT": "it-IT-ElsaNeural",
    "pt-BR": "pt-BR-FranciscaNeural",
    "gu-IN": "gu-IN-DhwaniNeural",
    "mr-IN": "mr-IN-AarohiNeural",
    "ta-IN": "ta-IN-PallaviNeural",
    "te-IN": "te-IN-ShrutiNeural",
    "kn-IN": "kn-IN-SapnaNeural",
    "bn-IN": "bn-IN-TanishaaNeural",
    "ur-IN": "ur-IN-GulNeural",
}


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


async def synthesize_speech(text: str, language: str = "en-US") -> bytes:
    if _is_placeholder(settings.azure_speech_key) or _is_placeholder(settings.azure_speech_region):
        raise ValueError("Azure Speech API key is not configured.")

    # Determine best matching voice and locale
    target_lang = language or "en-US"
    if target_lang == "auto":
        from .rag import detect_text_language
        target_lang = detect_text_language(text, "auto")

    voice = VOICE_MAP.get(target_lang)
    if not voice:
        lang_prefix = target_lang.split("-")[0].lower() if "-" in target_lang else target_lang.lower()
        for key, vname in VOICE_MAP.items():
            if key.lower().startswith(lang_prefix):
                voice = vname
                break
    if not voice:
        voice = VOICE_MAP["en-US"]

    # Extract valid BCP-47 locale from voice name (e.g., 'hi-IN' from 'hi-IN-SwaraNeural')
    voice_parts = voice.split("-")
    voice_locale = f"{voice_parts[0]}-{voice_parts[1]}" if len(voice_parts) >= 2 else "en-US"

    ssml = (
        f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{voice_locale}'>"
        f"<voice name='{voice}'>{_xml_escape(text)}</voice>"
        f"</speak>"
    )

    url = f"https://{settings.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "university-assistant",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, content=ssml.encode("utf-8"), headers=headers)
        resp.raise_for_status()
        return resp.content

