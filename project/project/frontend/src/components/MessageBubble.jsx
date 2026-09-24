import { useState } from "react";
import PartnerMatchesBubble from "./PartnerMatchesBubble";

export default function MessageBubble({ role, text, piiDetected, piiTypes, partnerData }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`bubble-container bubble-container--${role}`}>
      <div className="bubble__avatar" aria-hidden="true">
        {role === "assistant" ? "🤖" : "👤"}
      </div>
      <div className={`bubble bubble--${role}`}>
        {piiDetected && (
          <div className="pii-protection-badge" title={`Scrubbed: ${piiTypes?.join(", ")}`}>
            🛡️ Privacy Shield: Sensitive PII ({piiTypes?.join(", ")}) was redacted before processing
          </div>
        )}
        <p className="bubble__text">{text}</p>

        {role === "assistant" && partnerData && (
          <PartnerMatchesBubble partnerData={partnerData} />
        )}

        {role === "assistant" && (
          <button className="bubble__copy" onClick={handleCopy} title="Copy response">
            {copied ? "✓ Copied" : "Copy"}
          </button>
        )}
      </div>
    </div>
  );
}

