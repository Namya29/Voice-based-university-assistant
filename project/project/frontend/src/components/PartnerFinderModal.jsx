import { useEffect, useState } from "react";
import PartnerCard from "./PartnerCard";
import {
  getCollaborationRequests,
  getStudentProfiles,
  searchPartners,
  sendCollaborationRequest,
  updateSmtpConfig,
  testSmtpConnection,
  updateRequestStatus,
} from "../api/assistantApi";
import "./PartnerFinderModal.css";

export default function PartnerFinderModal({ isOpen, onClose, initialQuery, partnerData }) {
  const [activeTab, setActiveTab] = useState("search"); // 'search', 'directory', 'requests', 'smtp'
  const [userSkillsInput, setUserSkillsInput] = useState("AI/ML, React");
  const [requiredSkillsInput, setRequiredSkillsInput] = useState("UI/UX, Backend");
  const [projectType, setProjectType] = useState("Hackathon");
  const [matches, setMatches] = useState([]);
  const [allProfiles, setAllProfiles] = useState([]);
  const [collaborationRequests, setCollaborationRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sentStatuses, setSentStatuses] = useState({});

  // View Profile Modal State
  const [viewingProfile, setViewingProfile] = useState(null);

  // Send Invitation Confirmation Popup State (Step 5 Flow)
  const [invitingProfile, setInvitingProfile] = useState(null);
  const [customNote, setCustomNote] = useState("");
  const [sendingInvite, setSendingInvite] = useState(false);

  // Sent Invitations Filter State
  const [statusFilter, setStatusFilter] = useState("All");

  // SMTP Live Email Settings State
  const [smtpUser, setSmtpUser] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [smtpHost, setSmtpHost] = useState("smtp.gmail.com");
  const [smtpPort, setSmtpPort] = useState(587);
  const [smtpStatusMsg, setSmtpStatusMsg] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadInitialData();
    }
  }, [isOpen]);

  useEffect(() => {
    if (partnerData?.target_student) {
      openInviteConfirmation(partnerData.target_student);
    }
  }, [partnerData]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [profilesRes, requestsRes, searchRes] = await Promise.all([
        getStudentProfiles().catch(() => ({ profiles: [] })),
        getCollaborationRequests().catch(() => ({ requests: [] })),
        searchPartners(["AI/ML", "React"], ["UI/UX", "Backend"], "Hackathon").catch(() => ({ matches: [] })),
      ]);

      setAllProfiles(profilesRes.profiles || []);
      setCollaborationRequests(requestsRes.requests || []);
      setMatches(searchRes.matches || []);
    } catch (err) {
      console.error("Error loading partner finder data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const userSkills = userSkillsInput.split(",").map((s) => s.trim()).filter(Boolean);
      const reqSkills = requiredSkillsInput.split(",").map((s) => s.trim()).filter(Boolean);

      const res = await searchPartners(userSkills, reqSkills, projectType);
      setMatches(res.matches || []);
    } catch (err) {
      alert("Search failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const openInviteConfirmation = (profile) => {
    setInvitingProfile(profile);
    setCustomNote(
      `Hi ${profile.name}! I saw your profile on Greenfield University Partner Finder and noticed your skills match our ${projectType} project requirements. Would love to collaborate together!`
    );
  };

  const handleConfirmSendInvitation = async () => {
    if (!invitingProfile) return;
    setSendingInvite(true);
    try {
      const result = await sendCollaborationRequest({
        target_student_id: invitingProfile.id,
        project_type: projectType,
        note: customNote,
        user_skills: userSkillsInput.split(",").map((s) => s.trim()).filter(Boolean),
        required_skills: requiredSkillsInput.split(",").map((s) => s.trim()).filter(Boolean),
      });

      setSentStatuses((prev) => ({ ...prev, [invitingProfile.id]: "Pending" }));
      alert(`✅ ${result.message}\n\n${result.email_status || ""}`);

      setInvitingProfile(null);
      setViewingProfile(null);

      // Refresh sent invitations list
      const reqRes = await getCollaborationRequests().catch(() => null);
      if (reqRes?.requests) setCollaborationRequests(reqRes.requests);
      setActiveTab("requests");
    } catch (err) {
      alert("Failed to send collaboration invitation: " + err.message);
    } finally {
      setSendingInvite(false);
    }
  };

  const handleUpdateStatus = async (requestId, newStatus) => {
    try {
      await updateRequestStatus(requestId, newStatus);
      setCollaborationRequests((prev) =>
        prev.map((r) => (r.id === requestId ? { ...r, status: newStatus } : r))
      );
    } catch (err) {
      alert("Could not update status: " + err.message);
    }
  };

  const handleSaveSmtp = async (e) => {
    e?.preventDefault();
    setSmtpStatusMsg("⏳ Connecting & verifying SMTP credentials...");
    try {
      const res = await updateSmtpConfig(smtpUser, smtpPassword, smtpHost, Number(smtpPort));
      if (res.success) {
        setSmtpStatusMsg(`✅ ${res.message}`);
      } else {
        setSmtpStatusMsg(`❌ ${res.message}`);
      }
    } catch (err) {
      setSmtpStatusMsg("❌ Failed to configure SMTP: " + err.message);
    }
  };

  const handleTestSmtp = async () => {
    setSmtpStatusMsg("⏳ Sending collaboration invitation email test...");
    try {
      const res = await testSmtpConnection(smtpUser);
      if (res.success) {
        setSmtpStatusMsg(`✅ ${res.message}`);
      } else {
        setSmtpStatusMsg(`❌ ${res.message}`);
      }
    } catch (err) {
      setSmtpStatusMsg("❌ Invitation email failed: " + err.message);
    }
  };

  const filteredRequests = collaborationRequests.filter((r) => {
    if (statusFilter === "All") return true;
    return r.status?.toLowerCase().includes(statusFilter.toLowerCase());
  });

  if (!isOpen) return null;

  return (
    <div className="partner-modal-overlay" onClick={onClose}>
      <div className="partner-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="partner-modal__header">
          <div className="partner-modal__title-group">
            <span style={{ fontSize: "1.6rem" }}>🤝</span>
            <div>
              <h3 className="partner-modal__title">AI Student Project Partner Finder</h3>
              <p style={{ color: "#94a3b8", fontSize: "0.82rem", margin: 0 }}>
                Match student skills, review candidate profiles &amp; send project collaboration invitations
              </p>
            </div>
          </div>
          <button className="partner-modal__close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Tabs Navigation */}
        <div className="partner-modal__tabs">
          <button
            className={`partner-modal__tab-btn ${activeTab === "search" ? "partner-modal__tab-btn--active" : ""}`}
            onClick={() => setActiveTab("search")}
          >
            ✨ Skill Matcher ({matches.length})
          </button>
          <button
            className={`partner-modal__tab-btn ${activeTab === "directory" ? "partner-modal__tab-btn--active" : ""}`}
            onClick={() => setActiveTab("directory")}
          >
            📚 Student Directory ({allProfiles.length})
          </button>
          <button
            className={`partner-modal__tab-btn ${activeTab === "requests" ? "partner-modal__tab-btn--active" : ""}`}
            onClick={() => setActiveTab("requests")}
          >
            📩 Sent Invitations ({collaborationRequests.length})
          </button>
          <button
            className={`partner-modal__tab-btn ${activeTab === "smtp" ? "partner-modal__tab-btn--active" : ""}`}
            onClick={() => setActiveTab("smtp")}
          >
            ⚙️ Email Config
          </button>
        </div>

        {/* Modal Body */}
        <div className="partner-modal__body">
          {/* TAB 1: SKILL MATCHER */}
          {activeTab === "search" && (
            <>
              <form className="partner-search-box" onSubmit={handleSearchSubmit}>
                <div className="partner-search-box__row">
                  <div className="partner-search-box__field">
                    <label className="partner-search-box__label">My Skills</label>
                    <input
                      className="partner-search-box__input"
                      value={userSkillsInput}
                      onChange={(e) => setUserSkillsInput(e.target.value)}
                      placeholder="e.g., AI/ML, React, Python"
                    />
                  </div>
                  <div className="partner-search-box__field">
                    <label className="partner-search-box__label">Skills I Need in a Partner</label>
                    <input
                      className="partner-search-box__input"
                      value={requiredSkillsInput}
                      onChange={(e) => setRequiredSkillsInput(e.target.value)}
                      placeholder="e.g., UI/UX, Backend, FastAPI"
                    />
                  </div>
                  <div className="partner-search-box__field" style={{ maxWidth: "180px" }}>
                    <label className="partner-search-box__label">Project Type</label>
                    <select
                      className="partner-search-box__input"
                      value={projectType}
                      onChange={(e) => setProjectType(e.target.value)}
                    >
                      <option value="Hackathon">Hackathon</option>
                      <option value="AI/ML Project">AI/ML Project</option>
                      <option value="Web Application">Web Application</option>
                      <option value="Mobile App">Mobile App</option>
                      <option value="Capstone">Capstone</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                  <button type="submit" className="partner-search-box__btn" disabled={loading}>
                    {loading ? "Matching..." : "🔍 Find Potential Partners"}
                  </button>
                  {matches.length > 0 && (
                    <button
                      type="button"
                      className="partner-search-box__btn"
                      style={{ background: "linear-gradient(135deg, #10b981, #059669)", width: "auto" }}
                      onClick={() => {
                        const topProfile = matches[0]?.profile || matches[0];
                        if (topProfile) openInviteConfirmation(topProfile);
                      }}
                    >
                      🤝 Send Collaboration Invitation
                    </button>
                  )}
                </div>
              </form>

              {loading ? (
                <p style={{ color: "#94a3b8", textAlign: "center", padding: "20px" }}>
                  Matching student profiles based on skills...
                </p>
              ) : (
                <div className="partner-results-grid">
                  {matches.map((item) => {
                    const profile = item.profile || item;
                    return (
                      <PartnerCard
                        key={profile.id}
                        matchItem={item}
                        onViewProfile={(p) => setViewingProfile(p)}
                        onSendInvitation={(p) => openInviteConfirmation(p)}
                        requestStatus={sentStatuses[profile.id]}
                      />
                    );
                  })}
                </div>
              )}
            </>
          )}

          {/* TAB 2: STUDENT DIRECTORY */}
          {activeTab === "directory" && (
            <div className="partner-results-grid">
              {allProfiles.map((profile) => (
                <PartnerCard
                  key={profile.id}
                  matchItem={{ profile, match_score: 92, match_reasons: ["Registered Greenfield Student Profile"] }}
                  onViewProfile={(p) => setViewingProfile(p)}
                  onSendInvitation={(p) => openInviteConfirmation(p)}
                  requestStatus={sentStatuses[profile.id]}
                />
              ))}
            </div>
          )}

          {/* TAB 3: SENT INVITATIONS (Pending, Accepted, Declined) */}
          {activeTab === "requests" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h4 style={{ color: "#f8fafc", margin: 0 }}>📩 Sent Collaboration Invitations</h4>
                <div style={{ display: "flex", gap: "6px" }}>
                  {["All", "Pending", "Accepted", "Declined"].map((filter) => (
                    <button
                      key={filter}
                      type="button"
                      className={`partner-modal__tab-btn ${statusFilter === filter ? "partner-modal__tab-btn--active" : ""}`}
                      style={{ padding: "4px 10px", fontSize: "0.78rem" }}
                      onClick={() => setStatusFilter(filter)}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>

              {filteredRequests.length === 0 ? (
                <p style={{ color: "#94a3b8", textAlign: "center", padding: "30px 0" }}>
                  No invitations found for status &quot;{statusFilter}&quot;. Find potential partners and click Send Collaboration Invitation!
                </p>
              ) : (
                <table className="requests-table">
                  <thead>
                    <tr>
                      <th>Recipient Student</th>
                      <th>Project Type</th>
                      <th>Sent Date</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRequests.map((req) => (
                      <tr key={req.id}>
                        <td>
                          <strong>{req.target_student_name}</strong>
                          <div style={{ fontSize: "0.78rem", color: "#38bdf8" }}>📧 {req.target_student_email}</div>
                        </td>
                        <td>{req.project_type}</td>
                        <td>{req.timestamp}</td>
                        <td>
                          <span
                            className="request-status-badge"
                            style={{
                              background:
                                req.status === "Accepted"
                                  ? "rgba(16, 185, 129, 0.2)"
                                  : req.status === "Declined"
                                  ? "rgba(239, 68, 68, 0.2)"
                                  : "rgba(245, 158, 11, 0.2)",
                              color:
                                req.status === "Accepted"
                                  ? "#34d399"
                                  : req.status === "Declined"
                                  ? "#f87171"
                                  : "#fbbf24",
                              border: `1px solid ${
                                req.status === "Accepted"
                                  ? "#10b981"
                                  : req.status === "Declined"
                                  ? "#ef4444"
                                  : "#f59e0b"
                              }`,
                            }}
                          >
                            {req.status === "Accepted" ? "✓ Accepted" : req.status === "Declined" ? "✕ Declined" : "⏳ Pending"}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: "4px" }}>
                            {req.status !== "Accepted" && (
                              <button
                                type="button"
                                style={{
                                  padding: "3px 8px",
                                  fontSize: "0.72rem",
                                  borderRadius: "4px",
                                  background: "#059669",
                                  color: "white",
                                  border: "none",
                                  cursor: "pointer",
                                }}
                                onClick={() => handleUpdateStatus(req.id, "Accepted")}
                              >
                                Mark Accepted
                              </button>
                            )}
                            {req.status !== "Declined" && (
                              <button
                                type="button"
                                style={{
                                  padding: "3px 8px",
                                  fontSize: "0.72rem",
                                  borderRadius: "4px",
                                  background: "#dc2626",
                                  color: "white",
                                  border: "none",
                                  cursor: "pointer",
                                }}
                                onClick={() => handleUpdateStatus(req.id, "Declined")}
                              >
                                Mark Declined
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 4: EMAIL CONFIG */}
          {activeTab === "smtp" && (
            <form className="partner-search-box" onSubmit={handleSaveSmtp} style={{ maxWidth: "600px", margin: "0 auto" }}>
              <h4 style={{ color: "#818cf8", margin: 0 }}>⚙️ Configure Gmail / SMTP Email Delivery</h4>
              <p style={{ color: "#cbd5e1", fontSize: "0.85rem", margin: 0 }}>
                Enter your Gmail sender credentials to deliver real project collaboration invitations to students&apos; Gmail inboxes:
              </p>

              <div className="partner-search-box__field">
                <label className="partner-search-box__label">Sender Gmail Address</label>
                <input
                  className="partner-search-box__input"
                  value={smtpUser}
                  onChange={(e) => setSmtpUser(e.target.value)}
                  placeholder="yourname@gmail.com"
                  required
                />
              </div>

              <div className="partner-search-box__field">
                <label className="partner-search-box__label">Gmail App Password (16-characters)</label>
                <input
                  type="password"
                  className="partner-search-box__input"
                  value={smtpPassword}
                  onChange={(e) => setSmtpPassword(e.target.value)}
                  placeholder="xxxx xxxx xxxx xxxx"
                  required
                />
                <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                  💡 Generate a 16-char Gmail App Password at <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" style={{ color: "#38bdf8" }}>myaccount.google.com/apppasswords</a>
                </span>
              </div>

              <div className="partner-search-box__row">
                <div className="partner-search-box__field">
                  <label className="partner-search-box__label">SMTP Server Host</label>
                  <input
                    className="partner-search-box__input"
                    value={smtpHost}
                    onChange={(e) => setSmtpHost(e.target.value)}
                  />
                </div>
                <div className="partner-search-box__field">
                  <label className="partner-search-box__label">Port</label>
                  <input
                    type="number"
                    className="partner-search-box__input"
                    value={smtpPort}
                    onChange={(e) => setSmtpPort(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
                <button type="submit" className="partner-search-box__btn">
                  💾 Save &amp; Connect SMTP
                </button>
                <button
                  type="button"
                  className="partner-search-box__btn"
                  style={{ background: "rgba(16, 185, 129, 0.2)", border: "1px solid #10b981", color: "#6ee7b7" }}
                  onClick={handleTestSmtp}
                >
                  🤝 Send Test Collaboration Email
                </button>
              </div>

              {smtpStatusMsg && (
                <div
                  style={{
                    color: smtpStatusMsg.startsWith("❌") ? "#f87171" : "#34d399",
                    fontWeight: "600",
                    fontSize: "0.88rem",
                    marginTop: "10px",
                    padding: "10px 14px",
                    background: smtpStatusMsg.startsWith("❌") ? "rgba(239, 68, 68, 0.1)" : "rgba(16, 185, 129, 0.1)",
                    border: `1px solid ${smtpStatusMsg.startsWith("❌") ? "#ef4444" : "#10b981"}`,
                    borderRadius: "8px",
                  }}
                >
                  {smtpStatusMsg}
                </div>
              )}
            </form>
          )}
        </div>
      </div>

      {/* VIEW PROFILE MODAL OVERLAY (STEP 3) */}
      {viewingProfile && (
        <div className="partner-modal-overlay" style={{ zIndex: 1100 }} onClick={() => setViewingProfile(null)}>
          <div
            className="partner-modal"
            style={{ maxWidth: "560px", padding: "24px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div
                  className="partner-card__avatar"
                  style={{ backgroundColor: viewingProfile.avatar_color || "#4f46e5", width: "46px", height: "46px", fontSize: "1.2rem" }}
                >
                  {viewingProfile.avatar_initials || viewingProfile.name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 style={{ margin: 0, color: "#ffffff", fontSize: "1.2rem" }}>{viewingProfile.name}</h3>
                  <p style={{ margin: 0, color: "#38bdf8", fontSize: "0.85rem" }}>{viewingProfile.department} • {viewingProfile.year}</p>
                </div>
              </div>
              <button
                className="partner-modal__close-btn"
                onClick={() => setViewingProfile(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", color: "#cbd5e1", fontSize: "0.9rem" }}>
              <div><strong>Email:</strong> {viewingProfile.email}</div>
              <div><strong>Bio:</strong> {viewingProfile.bio}</div>
              <div>
                <strong>Skills &amp; Expertise:</strong>
                <div className="partner-card__skills-list" style={{ marginTop: "6px" }}>
                  {viewingProfile.my_skills?.map((s) => (
                    <span key={s} className="partner-card__skill-tag partner-card__skill-tag--matched">{s}</span>
                  ))}
                </div>
              </div>
              <div>
                <strong>Looking for Partner Skills:</strong>
                <div className="partner-card__skills-list" style={{ marginTop: "6px" }}>
                  {viewingProfile.looking_for_skills?.map((s) => (
                    <span key={s} className="partner-card__skill-tag" style={{ background: "rgba(99, 102, 241, 0.2)", border: "1px solid #6366f1", color: "#c7d2fe" }}>{s}</span>
                  ))}
                </div>
              </div>
              <div><strong>Project Interests:</strong> {viewingProfile.project_interests?.join(", ")}</div>
              <div><strong>Availability:</strong> {viewingProfile.availability}</div>
              <div><strong>Languages:</strong> {viewingProfile.languages?.join(", ")}</div>
              <div><strong>Rating:</strong> ⭐ {viewingProfile.rating} ({viewingProfile.projects_completed} projects completed)</div>
            </div>

            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button
                type="button"
                className="partner-search-box__btn"
                style={{ background: "#334155" }}
                onClick={() => setViewingProfile(null)}
              >
                Close
              </button>
              <button
                type="button"
                className="partner-search-box__btn"
                style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
                onClick={() => {
                  const target = viewingProfile;
                  setViewingProfile(null);
                  openInviteConfirmation(target);
                }}
              >
                🤝 Send Collaboration Invitation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONFIRMATION POPUP (STEP 5 FLOW) */}
      {invitingProfile && (
        <div className="partner-modal-overlay" style={{ zIndex: 1200 }} onClick={() => setInvitingProfile(null)}>
          <div
            className="partner-modal"
            style={{ maxWidth: "520px", padding: "24px", border: "1px solid #10b981" }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ color: "#34d399", margin: "0 0 8px 0" }}>🤝 Confirm Project Collaboration Invitation</h3>
            <p style={{ color: "#cbd5e1", fontSize: "0.88rem", margin: "0 0 16px 0", lineHeight: "1.5" }}>
              Confirm your project collaboration invitation details below. An email invitation will be sent to <strong>{invitingProfile.name}</strong> stating that their skills match your project needs.
            </p>

            <div style={{ background: "#0f172a", padding: "14px", borderRadius: "8px", border: "1px solid #334155", marginBottom: "14px" }}>
              <div style={{ marginBottom: "6px", fontSize: "0.85rem" }}>
                <strong style={{ color: "#94a3b8" }}>Recipient:</strong> <span style={{ color: "#f8fafc" }}>{invitingProfile.name} ({invitingProfile.email})</span>
              </div>
              <div style={{ marginBottom: "6px", fontSize: "0.85rem" }}>
                <strong style={{ color: "#94a3b8" }}>Project Type:</strong> <span style={{ color: "#f8fafc" }}>{projectType}</span>
              </div>
              <div style={{ fontSize: "0.85rem" }}>
                <strong style={{ color: "#94a3b8" }}>Recipient Skills:</strong> <span style={{ color: "#38bdf8" }}>{invitingProfile.my_skills?.join(", ")}</span>
              </div>
            </div>

            <div className="partner-search-box__field" style={{ marginBottom: "16px" }}>
              <label className="partner-search-box__label">Optional Personal Message to {invitingProfile.name}</label>
              <textarea
                className="partner-search-box__input"
                style={{ height: "80px", resize: "none" }}
                value={customNote}
                onChange={(e) => setCustomNote(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                type="button"
                className="partner-search-box__btn"
                style={{ background: "#334155" }}
                onClick={() => setInvitingProfile(null)}
                disabled={sendingInvite}
              >
                Cancel
              </button>
              <button
                type="button"
                className="partner-search-box__btn"
                style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
                onClick={handleConfirmSendInvitation}
                disabled={sendingInvite}
              >
                {sendingInvite ? "Sending Invitation..." : "🤝 Confirm & Send Invitation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
