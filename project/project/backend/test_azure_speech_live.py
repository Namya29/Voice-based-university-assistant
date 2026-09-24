"""Direct testing script for Azure Speech Service multi-language synthesis.
Run with: python test_azure_speech_live.py
"""
import asyncio
from app.config import get_settings
from app.azure_clients import synthesize_speech, issue_speech_token

TEST_CASES = [
    ("en-US", "Welcome to Greenfield University Voice Assistant."),
    ("hi-IN", "नमस्ते! ग्रीनफील्ड यूनिवर्सिटी में आपका स्वागत है।"),
    ("pa-IN", "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਗ੍ਰੀਨਫੀਲਡ ਯੂਨੀਵਰਸਿਟੀ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ।"),
    ("es-ES", "¡Hola! Bienvenido al asistente de voz de Greenfield University."),
    ("fr-FR", "Bonjour! Bienvenue à l'assistant vocal de Greenfield University."),
    ("de-DE", "Hallo! Willkommen beim Sprachassistenten der Greenfield University."),
    ("ar-SA", "مرحبًا بكم في المساعد الصوتي لجامعة جرينفيلد."),
    ("zh-CN", "您好！欢迎使用格林菲尔德大学语音助手。"),
]


async def run_direct_tests():
    settings = get_settings()
    print(f"=== Azure Speech Testing ===")
    print(f"Region: {settings.azure_speech_region}")
    key_masked = settings.azure_speech_key[:4] + "..." + settings.azure_speech_key[-4:] if len(settings.azure_speech_key) > 8 else settings.azure_speech_key
    print(f"Key: {key_masked}")
    print()

    # 1. Test token issuance
    try:
        print("[1/2] Testing Speech Token issuance...")
        token_info = await issue_speech_token()
        print(f"  SUCCESS! Token issued. Region: {token_info['region']}, Expires in: {token_info['expires_at']}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        return False

    print()
    print("[2/2] Testing Multi-Language Neural Voice Synthesis...")
    all_success = True
    for lang, sample_text in TEST_CASES:
        try:
            audio_bytes = await synthesize_speech(sample_text, lang)
            print(f"  [SUCCESS] [{lang}] Synthesized {len(audio_bytes)} bytes MP3 audio.")
        except Exception as exc:
            print(f"  [FAILED]  [{lang}] Failed: {exc}")
            all_success = False

    print()
    if all_success:
        print("=== ALL LANGUAGES TESTED AND WORKING PERFECTLY! ===")
    else:
        print("=== Some languages failed synthesis. ===")
    return all_success


if __name__ == "__main__":
    asyncio.run(run_direct_tests())
