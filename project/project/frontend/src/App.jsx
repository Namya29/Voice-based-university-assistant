import { useCallback, useEffect, useRef, useState } from "react";
import VoiceOrb from "./components/VoiceOrb";
import ChatWindow from "./components/ChatWindow";
import ExampleQuestions from "./components/ExampleQuestions";
import UserHeader from "./components/UserHeader";
import AuthModal from "./components/AuthModal";
import { useVoiceRecognizer } from "./hooks/useVoiceRecognizer";
import { askAssistant, getCurrentUser, setStoredToken, speak } from "./api/assistantApi";
import "./App.css";

const ALL_AZURE_LANGUAGES = [
  { code: "pa-IN", label: "ਪੰਜਾਬੀ (Punjabi)", flag: "🌾", region: "India" },
  { code: "hi-IN", label: "हिन्दी (Hindi)", flag: "🇮🇳", region: "India" },
  { code: "en-US", label: "English (US / Global)", flag: "🇬🇧", region: "Global" },
  { code: "en-IN", label: "English (India)", flag: "🇮🇳", region: "India" },
  { code: "es-ES", label: "Español (Spanish)", flag: "🇪🇸", region: "Spain" },
  { code: "fr-FR", label: "Français (French)", flag: "🇫🇷", region: "France" },
  { code: "de-DE", label: "Deutsch (German)", flag: "🇩🇪", region: "Germany" },
  { code: "ar-SA", label: "العربية (Arabic)", flag: "🇸🇦", region: "Saudi Arabia" },
  { code: "zh-CN", label: "中文 (Mandarin Chinese)", flag: "🇨🇳", region: "China" },
  { code: "ja-JP", label: "日本語 (Japanese)", flag: "🇯🇵", region: "Japan" },
  { code: "ko-KR", label: "한국어 (Korean)", flag: "🇰🇷", region: "Korea" },
  { code: "ru-RU", label: "Русский (Russian)", flag: "🇷🇺", region: "Russia" },
  { code: "it-IT", label: "Italiano (Italian)", flag: "🇮🇹", region: "Italy" },
  { code: "pt-BR", label: "Português (Portuguese)", flag: "🇧🇷", region: "Brazil" },
  { code: "gu-IN", label: "ગુજરાતી (Gujarati)", flag: "🇮🇳", region: "India" },
  { code: "mr-IN", label: "मराठी (Marathi)", flag: "🇮🇳", region: "India" },
  { code: "ta-IN", label: "தமிழ் (Tamil)", flag: "🇮🇳", region: "India" },
  { code: "te-IN", label: "తెలుగు (Telugu)", flag: "🇮🇳", region: "India" },
  { code: "kn-IN", label: "ಕನ್ನಡ (Kannada)", flag: "🇮🇳", region: "India" },
  { code: "bn-IN", label: "বাংলা (Bengali)", flag: "🇮🇳", region: "India" },
  { code: "ur-IN", label: "اردو (Urdu)", flag: "🇮🇳", region: "India" },
  { code: "auto", label: "🌐 Auto Detect Language", flag: "🌐", region: "Universal" },
];

export default function App() {
  const { start, stop, status, transcript, error } = useVoiceRecognizer();
  const [selectedLang, setSelectedLang] = useState("pa-IN");
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [user, setUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const conversationId = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => {
    getCurrentUser().then((u) => {
      if (u) setUser(u);
    }).catch(() => null);
  }, []);

  const handleLogout = () => {
    setStoredToken(null);
    setUser(null);
  };

  const speakWithBrowser = useCallback((text, lang) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      if (lang) utterance.lang = lang;
      window.speechSynthesis.speak(utterance);
    }
  }, []);

  const handleAsk = useCallback(async (query, language) => {
    if (!query || !query.trim()) return;
    const effectiveQueryLang = language || selectedLang || "pa-IN";
    setBusy(true);
    setApiError(null);

    try {
      const result = await askAssistant(query.trim(), effectiveQueryLang, conversationId.current);
      conversationId.current = result.conversation_id;

      // Add user message with PII redaction indicator if PII was detected
      const userMessageText = result.clean_query || query;
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "user",
          text: userMessageText,
          piiDetected: result.pii_detected,
          piiTypes: result.pii_types,
        },
      ]);

      let audioUrl = null;
      try {
        audioUrl = await speak(result.answer, result.language || effectiveQueryLang);
      } catch (err) {
        console.warn("Azure TTS synthesis notice, using browser speech fallback:", err);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: result.answer,
          language: result.language || effectiveQueryLang,
          verified: result.verified,
          sources: result.sources,
          audioUrl,
        },
      ]);

      if (audioUrl && audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play().catch(() => {
          speakWithBrowser(result.answer, result.language || effectiveQueryLang);
        });
      } else {
        speakWithBrowser(result.answer, result.language || effectiveQueryLang);
      }
    } catch (err) {
      setApiError(err.message || "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }, [selectedLang, speakWithBrowser]);

  const handleMicClick = () => {
    if (status === "listening") {
      stop();
      return;
    }
    if (busy) return;
    start((finalText, lang) => {
      handleAsk(finalText, lang || selectedLang);
    }, selectedLang);
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!textInput.trim() || busy) return;
    handleAsk(textInput, selectedLang);
    setTextInput("");
  };

  const handleReplay = (audioUrl, text, language) => {
    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(() => speakWithBrowser(text, language));
    } else {
      speakWithBrowser(text, language);
    }
  };

  const activeLangObj = ALL_AZURE_LANGUAGES.find((l) => l.code === selectedLang) || ALL_AZURE_LANGUAGES[0];

  return (
    <div className="app">
      <header className="hero">
        <UserHeader
          user={user}
          onOpenAuth={() => setIsAuthModalOpen(true)}
          onLogout={handleLogout}
        />

        <div className="hero__content">
          <h1>Chitkara University Voice Assistant</h1>
          <p>Official voice portal for campus rules, library, exams, fees & hostel guidelines in 21+ languages.</p>
        </div>
      </header>

      <main className="main-grid">
        <section className="voice-panel">
          <div className="voice-panel__header">
            <h3>Voice Input</h3>
            <span className={`live-status-tag ${status === "listening" ? "live-status-tag--recording" : ""}`}>
              {status === "listening" ? "🔴 Recording" : busy ? "⏳ Searching" : "🟢 Ready"}
            </span>
          </div>

          {/* Full Language Dropdown */}
          <div className="language-dropdown-wrapper">
            <label htmlFor="lang-select" className="dropdown-label">
              <span>🗣️ Selected Voice & Response Language:</span>
            </label>
            <div className="custom-select-container">
              <span className="select-flag">{activeLangObj.flag}</span>
              <select
                id="lang-select"
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="language-select"
              >
                {ALL_AZURE_LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.flag} {l.label} ({l.region})
                  </option>
                ))}
              </select>
            </div>
            <p className="lang-hint">
              Speak in <strong>{activeLangObj.label}</strong> — question, answer & audio speech will strictly match this language.
            </p>
          </div>

          <VoiceOrb status={busy ? "processing" : status} onClick={handleMicClick} />
          
          <div className="live-transcript-box">
            {status === "listening" ? (
              <p className="live-transcript live-transcript--active">
                {transcript || `Listening in ${activeLangObj.label}... speak now`}
              </p>
            ) : busy ? (
              <p className="live-transcript">Searching official Chitkara University documents...</p>
            ) : (
              <p className="live-transcript live-transcript--idle">
                Click the microphone orb to speak in {activeLangObj.label}, and click again to send
              </p>
            )}
          </div>

          {error && <p className="error-text">⚠️ {error}</p>}
          {apiError && <p className="error-text">⚠️ {apiError}</p>}

          <form className="text-fallback" onSubmit={handleTextSubmit}>
            <input
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={`Type your question in ${activeLangObj.label.split(" ")[0]}...`}
              aria-label="Type your question"
            />
            <button type="submit" disabled={busy || !textInput.trim()} className="send-btn">
              <span>Send</span>
              <svg viewBox="0 0 24 24" className="send-icon">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </form>

          <ExampleQuestions onPick={(q) => handleAsk(q, selectedLang)} currentLang={selectedLang} />

          <div className="campus-quick-widget">
            <div className="widget-header">
              <span>Official Indexed Regulations (5 PDFs)</span>
            </div>
            <div className="widget-items">
              <div className="widget-item">
                <span className="item-title">📖 Central Library Rules</span>
                <span className="item-status item-status--open">Mon–Sat 8 AM–10 PM</span>
              </div>
              <div className="widget-item">
                <span className="item-title">📋 Academic Rules 2025</span>
                <span className="item-status item-status--open">75% Min Attendance</span>
              </div>
              <div className="widget-item">
                <span className="item-title">🏢 Hostel Guidelines</span>
                <span className="item-status item-status--open">In-time 8:30 / 9:30 PM</span>
              </div>
              <div className="widget-item">
                <span className="item-title">💳 Fee Circular (Even Sem)</span>
                <span className="item-status item-status--open">Due Date 15 Jan</span>
              </div>
              <div className="widget-item">
                <span className="item-title">📝 Exam Regulations</span>
                <span className="item-status item-status--open">Passing Min 40%</span>
              </div>
            </div>
          </div>
        </section>

        <ChatWindow
          messages={messages}
          onReplay={handleReplay}
          onClear={() => setMessages([])}
        />
      </main>

      <footer className="app-footer">
        <p>© 2026 Chitkara University • Grounded RAG Voice Assistant with Azure Neural Speech</p>
      </footer>

      <audio ref={audioRef} hidden />

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={(u) => setUser(u)}
      />
    </div>
  );
}
