import "./PartnerCard.css";

export default function PartnerCard({ matchItem, onViewProfile, onSendInvitation, requestStatus }) {
  const profile = matchItem?.profile || matchItem || {};
  const matchScore = matchItem?.match_score || 88;
  const matchReasons = matchItem?.match_reasons || [];

  return (
    <div className="partner-card">
      <div className="partner-card__header">
        <div className="partner-card__user-info">
          <div
            className="partner-card__avatar"
            style={{ backgroundColor: profile.avatar_color || "#4f46e5" }}
          >
            {profile.avatar_initials || profile.name?.slice(0, 2).toUpperCase() || "ST"}
          </div>
          <div className="partner-card__details">
            <h4 className="partner-card__name">{profile.name}</h4>
            <span className="partner-card__dept">
              {profile.department} • {profile.year}
            </span>
            <span style={{ fontSize: "0.76rem", color: "#38bdf8", marginTop: "2px" }}>
              📧 {profile.email}
            </span>
          </div>
        </div>

        <div className="partner-card__match-badge">
          ✨ {matchScore}% Skill Match
        </div>
      </div>

      <p className="partner-card__bio">{profile.bio}</p>

      <div className="partner-card__skills-section">
        <span className="partner-card__skills-label">My Skills</span>
        <div className="partner-card__skills-list">
          {profile.my_skills?.map((skill) => (
            <span key={skill} className="partner-card__skill-tag partner-card__skill-tag--matched">
              {skill}
            </span>
          ))}
        </div>
      </div>

      {matchReasons.length > 0 && (
        <div className="partner-card__reasons">
          {matchReasons.map((reason, idx) => (
            <div key={idx} className="partner-card__reason-item">
              <span>🎯</span>
              <span>{reason}</span>
            </div>
          ))}
        </div>
      )}

      <div className="partner-card__footer">
        <div className="partner-card__meta">
          <span>📅 {profile.availability}</span>
          <span>⭐ {profile.rating}</span>
        </div>

        <div style={{ display: "flex", gap: "8px", width: "100%", marginTop: "8px" }}>
          <button
            type="button"
            className="partner-card__collab-btn"
            style={{ background: "rgba(99, 102, 241, 0.2)", border: "1px solid #6366f1", color: "#c7d2fe", flex: "1" }}
            onClick={() => onViewProfile && onViewProfile(profile)}
          >
            🔍 View Profile
          </button>

          {requestStatus ? (
            <button
              type="button"
              className="partner-card__collab-btn partner-card__collab-btn--sent"
              style={{ flex: "1.2" }}
              disabled
            >
              ✓ Invitation Sent
            </button>
          ) : (
            <button
              type="button"
              className="partner-card__collab-btn"
              style={{ background: "linear-gradient(135deg, #10b981, #059669)", color: "#ffffff", flex: "1.2" }}
              onClick={() => onSendInvitation && onSendInvitation(profile)}
            >
              🤝 Send Collaboration Invitation
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
