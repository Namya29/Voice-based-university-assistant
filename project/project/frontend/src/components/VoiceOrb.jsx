import "./VoiceOrb.css";

export default function VoiceOrb({ status, onClick }) {
  const label =
    status === "listening" ? "Tap to Stop & Send" :
    status === "processing" ? "Thinking..." :
    status === "error" ? "Tap to Retry" :
    "Tap to Speak";

  return (
    <div className="voice-orb-container">
      <button
        className={`voice-orb voice-orb--${status}`}
        onClick={onClick}
        aria-label={label}
        aria-pressed={status === "listening"}
      >
        <div className="voice-orb__aura" />
        <div className="voice-orb__pulse" />
        <div className="voice-orb__pulse voice-orb__pulse--delay" />
        
        {status === "listening" ? (
          <div className="sound-wave" aria-hidden="true">
            <span className="wave-bar bar-1"></span>
            <span className="wave-bar bar-2"></span>
            <span className="wave-bar bar-3"></span>
            <span className="wave-bar bar-4"></span>
            <span className="wave-bar bar-5"></span>
          </div>
        ) : (
          <svg viewBox="0 0 24 24" className="voice-orb__icon" aria-hidden="true">
            <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm5-3a1 1 0 1 0-2 0 3 3 0 0 1-6 0 1 1 0 1 0-2 0 5 5 0 0 0 4 4.9V19h-2a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-3.1A5 5 0 0 0 17 11Z" />
          </svg>
        )}

        <span className="voice-orb__label">{label}</span>
      </button>
    </div>
  );
}

