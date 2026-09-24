import { useState } from "react";
import PartnerCard from "./PartnerCard";
import { sendCollaborationRequest } from "../api/assistantApi";
import "./PartnerMatchesBubble.css";

export default function PartnerMatchesBubble({ partnerData }) {
  const matches = partnerData?.matches || [];
  const projectType = partnerData?.project_type || "Hackathon Project";

  const [viewingProfile, setViewingProfile] = useState(null);
  const [invitingProfile, setInvitingProfile] = useState(null);
  const [customNote, setCustomNote] = useState("");
  const [sentStatuses, setSentStatuses] = useState({});
  const [statusMessage, setStatusMessage] = useState(null);
  const [sendingInvite, setSendingInvite] = useState(false);

  const openInviteConfirmation = (profile) => {
    setInvitingProfile(profile);
    setCustomNote(
      `Hi ${profile.name}! I saw your profile on Greenfield University Partner Finder and noticed your skills match our ${projectType} project requirements. Would love to collaborate together!`
    );
  };

  const handleConfirmSendInvite = async () => {
    if (!invitingProfile) return;
    setSendingInvite(true);
    try {
      await sendCollaborationRequest({
        target_student_id: invitingProfile.id,
        project_type: projectType,
        note: customNote,
        user_skills: partnerData.user_skills || [],
        required_skills: partnerData.required_skills || [],
      });

      setSentStatuses((prev) => ({ ...prev, [invitingProfile.id]: "Pending" }));
      setStatusMessage(`📧 Collaboration invitation sent to ${invitingProfile.name} (${invitingProfile.email})!`);
      setInvitingProfile(null);
      setViewingProfile(null);
    } catch (err) {
      alert("Failed to send invitation: " + err.message);
    } finally {
      setSendingInvite(false);
    }
  };

  if (!matches || matches.length === 0) return null;

  return (
    <div className="partner-matches-bubble">
      <div className="partner-matches-bubble__header">
        <h4 className="partner-matches-bubble__title">
          🤝 Potential Project Partners for {projectType}
        </h4>
        <span className="live-status-tag">⚡ {matches.length} Candidates Matched</span>
      </div>

      <div className="partner-matches-bubble__grid">
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

      {statusMessage && (
        <div style={{ color: "#34d399", fontSize: "0.85rem", fontWeight: "600", marginTop: "8px" }}>
          {statusMessage}
        </div>
      )}

      {/* VIEW PROFILE MODAL OVERLAY */}
      {viewingProfile && (
        <div className="collab-confirm-overlay" onClick={() => setViewingProfile(null)}>
          <div className="collab-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="collab-confirm-modal__title">
              🔍 Student Profile: {viewingProfile.name}
            </h3>
            <p style={{ color: "#38bdf8", fontSize: "0.85rem", margin: "0 0 12px 0" }}>
              {viewingProfile.department} • {viewingProfile.year} &mdash; 📧 {viewingProfile.email}
            </p>

            <div style={{ color: "#cbd5e1", fontSize: "0.88rem", lineHeight: "1.5" }}>
              <p><strong>Bio:</strong> {viewingProfile.bio}</p>
              <p><strong>Skills:</strong> {viewingProfile.my_skills?.join(", ")}</p>
              <p><strong>Looking For:</strong> {viewingProfile.looking_for_skills?.join(", ")}</p>
              <p><strong>Availability:</strong> {viewingProfile.availability}</p>
            </div>

            <div className="collab-confirm-modal__buttons" style={{ marginTop: "16px" }}>
              <button className="collab-confirm-modal__cancel-btn" onClick={() => setViewingProfile(null)}>
                Close
              </button>
              <button
                className="collab-confirm-modal__confirm-btn"
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

      {/* CONFIRMATION POPUP OVERLAY */}
      {invitingProfile && (
        <div className="collab-confirm-overlay" onClick={() => setInvitingProfile(null)}>
          <div className="collab-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="collab-confirm-modal__title" style={{ color: "#34d399" }}>
              🤝 Confirm Project Collaboration Invitation
            </h3>
            <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "0 0 12px 0" }}>
              An email invitation will be dispatched to <strong>{invitingProfile.name}</strong> ({invitingProfile.email}) explaining that their skills match your project needs.
            </p>

            <textarea
              className="collab-confirm-modal__note"
              value={customNote}
              onChange={(e) => setCustomNote(e.target.value)}
              placeholder="Add an optional personal message to recipient..."
            />

            <div className="collab-confirm-modal__buttons">
              <button
                className="collab-confirm-modal__cancel-btn"
                onClick={() => setInvitingProfile(null)}
                disabled={sendingInvite}
              >
                Cancel
              </button>
              <button
                className="collab-confirm-modal__confirm-btn"
                onClick={handleConfirmSendInvite}
                disabled={sendingInvite}
              >
                {sendingInvite ? "Sending..." : "🤝 Confirm & Send Invitation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
