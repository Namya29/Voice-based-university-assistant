import { useState } from "react";
import { loginUser, registerUser } from "../api/assistantApi";

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [tab, setTab] = useState("quick"); // quick | login | register
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleQuickLogin = async (demoEmail, demoPassword) => {
    setError(null);
    setLoading(true);
    try {
      const res = await loginUser(demoEmail, demoPassword);
      onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await loginUser(email, password);
      onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await registerUser(email, password, fullName, role);
      onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h3>Authentication & Account Access</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </header>

        <div className="modal-tabs">
          <button
            className={`tab-btn ${tab === "quick" ? "active" : ""}`}
            onClick={() => { setTab("quick"); setError(null); }}
          >
            ⚡ Quick Demo
          </button>
          <button
            className={`tab-btn ${tab === "login" ? "active" : ""}`}
            onClick={() => { setTab("login"); setError(null); }}
          >
            🔑 Log In
          </button>
          <button
            className={`tab-btn ${tab === "register" ? "active" : ""}`}
            onClick={() => { setTab("register"); setError(null); }}
          >
            📝 Register
          </button>
        </div>

        {error && <div className="modal-error">⚠️ {error}</div>}

        {tab === "quick" && (
          <div className="quick-demo-section">
            <p className="demo-intro">Select a pre-configured demo account to test role-based authentication instantly:</p>
            <button
              disabled={loading}
              className="demo-btn demo-btn--student"
              onClick={() => handleQuickLogin("student@greenfield.edu", "student123")}
            >
              <span className="demo-icon">🎓</span>
              <div className="demo-details">
                <strong>Login as Student Demo</strong>
                <small>student@greenfield.edu • Access Campus Voice Assistant</small>
              </div>
            </button>

            <button
              disabled={loading}
              className="demo-btn demo-btn--admin"
              onClick={() => handleQuickLogin("admin@greenfield.edu", "admin123")}
            >
              <span className="demo-icon">🛡️</span>
              <div className="demo-details">
                <strong>Login as Admin Demo</strong>
                <small>admin@greenfield.edu • Full Administrative Authorization</small>
              </div>
            </button>
          </div>
        )}

        {tab === "login" && (
          <form onSubmit={handleLoginSubmit} className="auth-form">
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@greenfield.edu"
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <button type="submit" disabled={loading} className="auth-submit-btn">
              {loading ? "Authenticating..." : "Log In"}
            </button>
          </form>
        )}

        {tab === "register" && (
          <form onSubmit={handleRegisterSubmit} className="auth-form">
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Morgan"
              />
            </div>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@greenfield.edu"
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <div className="form-group">
              <label>Role</label>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="student">Student</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
            <button type="submit" disabled={loading} className="auth-submit-btn">
              {loading ? "Creating Account..." : "Create Account"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
