export default function UserHeader({ user, onOpenAuth, onLogout }) {
  return (
    <div className="hero__top-bar">
      <div className="hero__brand">
        <span className="hero__crest" aria-hidden="true">
          CU
        </span>
        <div className="brand-text-block">
          <span className="hero__name">Chitkara University</span>
          <span className="hero__subname">Official Voice Assistant</span>
        </div>
      </div>

      <div className="hero__pills">
        <span className="status-pill status-pill--active">
          <span className="pill-dot"></span> 5 Official Regulations Indexed
        </span>
        <span className="status-pill status-pill--azure">
          🎙️ Azure Neural TTS & STT
        </span>
        <span className="status-pill status-pill--info">
          🛡️ PII Protection Active
        </span>
      </div>

      <div className="user-profile-widget">
        {user && !user.is_guest ? (
          <div className="user-logged-in">
            <span className="user-avatar">{user.role === "admin" ? "🛡️" : "🎓"}</span>
            <div className="user-info">
              <span className="user-name">{user.full_name}</span>
              <span className={`user-role-badge user-role-badge--${user.role}`}>
                {user.role.toUpperCase()}
              </span>
            </div>
            <button onClick={onLogout} className="auth-btn auth-btn--logout" title="Log out">
              Logout
            </button>
          </div>
        ) : (
          <button onClick={onOpenAuth} className="auth-btn auth-btn--login">
            🔑 Log In / Demo Accounts
          </button>
        )}
      </div>
    </div>
  );
}
