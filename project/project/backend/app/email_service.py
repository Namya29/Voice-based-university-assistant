"""Email Notification Service for Greenfield University Partner Finder.
Sends real HTML collaboration invite emails via SMTP (e.g. Gmail) or logs formatted emails.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .config import get_settings

RUNTIME_SMTP_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SMTP_USER", ""),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "smtp_from_email": os.getenv("SMTP_FROM_EMAIL", ""),
}


def save_smtp_to_env(
    smtp_user: str,
    smtp_pass: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
):
    """Persist SMTP configuration directly into backend/.env file."""
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        new_lines = []
        keys_written = set()
        smtp_updates = {
            "SMTP_HOST": smtp_host,
            "SMTP_PORT": str(smtp_port),
            "SMTP_USER": smtp_user,
            "SMTP_PASSWORD": smtp_pass,
            "SMTP_FROM_EMAIL": smtp_user,
        }

        for line in lines:
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                if key in smtp_updates:
                    new_lines.append(f"{key}={smtp_updates[key]}\n")
                    keys_written.add(key)
                    continue
            new_lines.append(line)

        for k, v in smtp_updates.items():
            if k not in keys_written:
                new_lines.append(f"{k}={v}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as exc:
        print(f"⚠️ Warning: Could not persist SMTP settings to .env file: {exc}")


def set_runtime_smtp_config(
    smtp_user: str,
    smtp_password: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
):
    """Dynamically set SMTP credentials at runtime and persist to .env."""
    RUNTIME_SMTP_CONFIG["smtp_user"] = smtp_user
    RUNTIME_SMTP_CONFIG["smtp_password"] = smtp_password
    RUNTIME_SMTP_CONFIG["smtp_host"] = smtp_host
    RUNTIME_SMTP_CONFIG["smtp_port"] = smtp_port
    RUNTIME_SMTP_CONFIG["smtp_from_email"] = smtp_user

    os.environ["SMTP_USER"] = smtp_user
    os.environ["SMTP_PASSWORD"] = smtp_password
    os.environ["SMTP_HOST"] = smtp_host
    os.environ["SMTP_PORT"] = str(smtp_port)
    os.environ["SMTP_FROM_EMAIL"] = smtp_user

    save_smtp_to_env(smtp_user, smtp_password, smtp_host, smtp_port)


def test_smtp_connection(to_email: str | None = None) -> dict[str, Any]:
    """Test SMTP connection credentials and send a test email to verify live delivery."""
    settings = get_settings()
    smtp_host = RUNTIME_SMTP_CONFIG.get("smtp_host") or getattr(
        settings, "smtp_host", os.getenv("SMTP_HOST", "smtp.gmail.com")
    )
    smtp_port = int(
        RUNTIME_SMTP_CONFIG.get("smtp_port")
        or getattr(settings, "smtp_port", os.getenv("SMTP_PORT", "587"))
    )
    smtp_user = RUNTIME_SMTP_CONFIG.get("smtp_user") or getattr(
        settings, "smtp_user", os.getenv("SMTP_USER", "")
    )
    smtp_pass = RUNTIME_SMTP_CONFIG.get("smtp_password") or getattr(
        settings, "smtp_password", os.getenv("SMTP_PASSWORD", "")
    )
    from_email = RUNTIME_SMTP_CONFIG.get("smtp_from_email") or getattr(
        settings,
        "smtp_from_email",
        os.getenv("SMTP_FROM_EMAIL", smtp_user),
    )

    if not smtp_user or not smtp_pass:
        return {
            "success": False,
            "message": "⚠️ No SMTP credentials configured. Enter your Gmail address and 16-character App Password.",
        }

    target = to_email or smtp_user

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🤝 Project Collaboration Email Service Test - Greenfield University"
        msg["From"] = f"Greenfield University Partner Finder <{from_email}>"
        msg["To"] = target

        test_html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
          <div style="max-width: 550px; margin: 0 auto; background: #1e293b; padding: 26px; border-radius: 16px; border: 1px solid #10b981; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
            <h2 style="color: #34d399; font-size: 22px; margin-top: 0;">🤝 Project Collaboration Email Service Ready!</h2>
            <p style="font-size: 15px; line-height: 1.6; color: #f8fafc;">
              Your Gmail SMTP integration for <strong>{smtp_user}</strong> is verified and ready to deliver real student project collaboration invitations across Greenfield University.
            </p>
            <div style="background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10b981; padding: 14px; border-radius: 8px; margin: 18px 0; color: #a7f3d0; font-weight: 600;">
              ✨ Status: Live SMTP Connection Verified
            </div>
            <p style="font-size: 12px; color: #94a3b8; margin-top: 20px; text-align: center;">Sent from Greenfield University AI Labs • Partner Finder System</p>
          </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(test_html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [target], msg.as_string())

        print(f"✅ Live SMTP test email successfully sent to {target}")
        return {
            "success": True,
            "message": f"🤝 Collaboration test email successfully delivered to {target} via Gmail SMTP!",
            "smtp_user": smtp_user,
        }
    except Exception as exc:
        err_str = str(exc)
        if (
            "535" in err_str
            or "Authentication" in err_str
            or "Username and Password not accepted" in err_str
        ):
            detail = (
                "Gmail authentication failed (Error 535). "
                "Google requires a 16-character App Password. "
                "Please generate one at https://myaccount.google.com/apppasswords and try again."
            )
        else:
            detail = f"SMTP connection error: {err_str}"

        print(f"❌ SMTP connection test failed: {detail}")
        return {
            "success": False,
            "message": detail,
            "raw_error": err_str,
        }


def send_collaboration_email(
    sender_name: str,
    sender_email: str,
    target_name: str,
    target_email: str,
    project_type: str,
    user_skills: list[str],
    required_skills: list[str],
    note: str,
) -> dict[str, Any]:
    """Construct and dispatch a collaboration invite email to a candidate student."""
    settings = get_settings()

    user_skills_str = ", ".join(user_skills) if user_skills else "AI/ML, Web Development"
    required_skills_str = ", ".join(required_skills) if required_skills else "UI/UX, Backend"

    subject = f"🤝 Project Collaboration Invitation from {sender_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background: #1e293b; border: 1px solid #4f46e5; border-radius: 16px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .header {{ text-align: center; border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 20px; }}
        .badge {{ background: linear-gradient(135deg, #6366f1, #9333ea); color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .title {{ color: #ffffff; font-size: 22px; font-weight: 700; margin-top: 10px; }}
        .content {{ line-height: 1.6; font-size: 15px; color: #cbd5e1; }}
        .sender-box {{ background: rgba(99, 102, 241, 0.15); border-left: 4px solid #6366f1; padding: 16px; border-radius: 8px; margin: 20px 0; }}
        .detail-row {{ margin-bottom: 8px; font-size: 14px; }}
        .detail-label {{ font-weight: 600; color: #94a3b8; }}
        .note-box {{ background: #0f172a; border: 1px dashed #6366f1; padding: 14px; border-radius: 8px; color: #a7f3d0; font-style: italic; margin-top: 15px; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #334155; font-size: 12px; color: #64748b; }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="header">
          <span class="badge">🎓 Greenfield University AI Partner Finder</span>
          <div class="title">🤝 Project Collaboration Invitation</div>
        </div>
        
        <div class="content">
          <p>Hello <strong>{target_name}</strong>,</p>
          <p><strong>{sender_name}</strong> (<a href="mailto:{sender_email}" style="color: #818cf8;">{sender_email}</a>) is organizing a <strong>{project_type}</strong> project and noticed that your skills appear to closely match the project requirements!</p>
          <p>You are invited to connect and collaborate on this project.</p>
          
          <div class="sender-box">
            <div class="detail-row"><span class="detail-label">Project Lead / Peer:</span> <strong>{sender_name}</strong></div>
            <div class="detail-row"><span class="detail-label">Project Type:</span> <strong>{project_type}</strong></div>
            <div class="detail-row"><span class="detail-label">Sender's Skills:</span> {user_skills_str}</div>
            <div class="detail-row"><span class="detail-label">Matching Skills Needed:</span> {required_skills_str}</div>
          </div>
          
          <div class="detail-label">Message from {sender_name}:</div>
          <div class="note-box">"{note}"</div>
          
          <p style="margin-top: 25px;">If you are interested in teaming up, you can reply directly to <strong>{sender_name}</strong> at <a href="mailto:{sender_email}" style="color: #38bdf8;">{sender_email}</a> to start working together on {project_type}.</p>
        </div>
        
        <div class="footer">
          <p>© 2026 Greenfield University AI Labs • Student Project Collaboration System</p>
        </div>
      </div>
    </body>
    </html>
    """

    # Resolve SMTP settings (check runtime dictionary first, then pydantic settings, then env)
    smtp_host = RUNTIME_SMTP_CONFIG.get("smtp_host") or getattr(
        settings, "smtp_host", os.getenv("SMTP_HOST", "smtp.gmail.com")
    )
    smtp_port = int(
        RUNTIME_SMTP_CONFIG.get("smtp_port")
        or getattr(settings, "smtp_port", os.getenv("SMTP_PORT", "587"))
    )
    smtp_user = RUNTIME_SMTP_CONFIG.get("smtp_user") or getattr(
        settings, "smtp_user", os.getenv("SMTP_USER", "")
    )
    smtp_pass = RUNTIME_SMTP_CONFIG.get("smtp_password") or getattr(
        settings, "smtp_password", os.getenv("SMTP_PASSWORD", "")
    )
    from_email = RUNTIME_SMTP_CONFIG.get("smtp_from_email") or getattr(
        settings,
        "smtp_from_email",
        os.getenv("SMTP_FROM_EMAIL", smtp_user or "notifications@greenfield.edu"),
    )

    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Greenfield University Partner Finder <{from_email}>"
            msg["To"] = target_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [target_email], msg.as_string())

            print(f"✅ Real email successfully delivered via SMTP to {target_email}")
            return {
                "sent": True,
                "real_smtp": True,
                "recipient": target_email,
                "message": f"Real email notification successfully sent to {target_email}",
            }
        except Exception as exc:
            err_msg = str(exc)
            print(f"⚠️ SMTP error while sending to {target_email}: {err_msg}")
            return {
                "sent": False,
                "real_smtp": False,
                "recipient": target_email,
                "message": f"SMTP delivery error: {err_msg}",
                "error": err_msg,
            }

    # Logged delivery fallback (if SMTP credentials are not configured)
    print("=" * 60)
    print(f"📧 [EMAIL DISPATCHED] To: {target_email}")
    print(f"Subject: {subject}")
    print(f"From: {sender_name} <{sender_email}>")
    print(f"Target: {target_name}")
    print(f"Note: {note}")
    print("=" * 60)

    return {
        "sent": True,
        "real_smtp": False,
        "recipient": target_email,
        "message": f"Email request logged (simulated delivery to {target_email}). Configure Gmail SMTP credentials to deliver real emails.",
        "simulated": True,
    }


