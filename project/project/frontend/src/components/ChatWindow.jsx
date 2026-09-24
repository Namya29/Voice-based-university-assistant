import MessageBubble from "./MessageBubble";
import SourceCard from "./SourceCard";
import LanguageIndicator from "./LanguageIndicator";

export default function ChatWindow({ messages, onReplay, onClear }) {
  return (
    <section className="chat-window" aria-live="polite" aria-label="Conversation">
      <header className="chat-window__header">
        <div className="chat-window__title-group">
          <h2>Live Assistant Thread</h2>
          <span className="chat-window__badge">{messages.length} messages</span>
        </div>
        {messages.length > 0 && (
          <button onClick={onClear} className="chat-window__clear">
            🗑️ Clear chat
          </button>
        )}
      </header>

      <div className="chat-window__list">
        {messages.length === 0 && (
          <div className="chat-window__empty-state">
            <div className="empty-icon">✨</div>
            <h3>How can I assist you today?</h3>
            <p>Tap the mic orb on the left or type your query to ask about campus, admissions, library timings, and official university policies.</p>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`chat-row chat-row--${m.role}`}>
            <MessageBubble
              role={m.role}
              text={m.text}
              piiDetected={m.piiDetected}
              piiTypes={m.piiTypes}
              partnerData={m.partnerData}
            />
            {m.role === "assistant" && (
              <div className="chat-row__meta">
                {m.language && (
                  <LanguageIndicator language={m.language} verified={m.verified} />
                )}
                <button
                  className="chat-row__replay"
                  onClick={() => onReplay(m.audioUrl, m.text, m.language)}
                >
                  🔊 Read Aloud
                </button>
              </div>
            )}
            {m.sources?.length > 0 && (
              <div className="chat-row__sources">
                <span className="sources-label">Grounded Sources:</span>
                <div className="sources-grid">
                  {m.sources.map((s, i) => (
                    <SourceCard key={i} source={s} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

