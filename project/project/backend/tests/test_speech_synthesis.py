"""Tests for multi-language speech synthesis and voice mapping."""
import pytest
from app.azure_clients import VOICE_MAP, _xml_escape, synthesize_speech
from app.rag import detect_text_language


def test_voice_map_contains_target_languages():
    required_langs = [
        "en-US", "en-IN", "hi-IN", "pa-IN", "es-ES", "fr-FR", "de-DE",
        "ar-SA", "zh-CN", "ja-JP", "ko-KR", "ru-RU", "it-IT", "pt-BR",
        "gu-IN", "mr-IN", "ta-IN", "te-IN", "kn-IN", "bn-IN", "ur-IN"
    ]
    for lang in required_langs:
        assert lang in VOICE_MAP, f"Missing voice mapping for {lang}"
        assert VOICE_MAP[lang].endswith("Neural"), f"Voice for {lang} should be a Neural voice"


def test_xml_escaping():
    raw_text = 'Hello <world> & "friends" and \'all\''
    escaped = _xml_escape(raw_text)
    assert "&lt;" in escaped
    assert "&gt;" in escaped
    assert "&amp;" in escaped
    assert "&quot;" in escaped
    assert "&apos;" in escaped


def test_language_detection_multilingual():
    assert detect_text_language("पुस्तकालय कब खुलता है?") == "hi-IN"
    assert detect_text_language("ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ?") == "pa-IN"
    assert detect_text_language("¿Cuándo abre la biblioteca?") == "es-ES"
    assert detect_text_language("Quand ouvre la bibliothèque?") == "fr-FR"
    assert detect_text_language("Wann öffnet die Bibliothek?") == "de-DE"
    assert detect_text_language("متى تفتح المكتبة؟") == "ar-SA"
    assert detect_text_language("图书馆什么时候开门？") == "zh-CN"
    assert detect_text_language("When does the library open?") == "en-US"
    assert detect_text_language("Library kab khulta hai?") == "hi-IN"
