"""AI Project Partner Finder module.
Handles registered student profiles, partner intent extraction, candidate matching, and collaboration requests.
"""
import re
import uuid
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user

from .email_service import (
    send_collaboration_email,
    set_runtime_smtp_config,
    test_smtp_connection,
)

partner_router = APIRouter(prefix="/api/partners", tags=["Partner Finder"])

# Registered Greenfield University Student Profiles Database
STUDENT_PROFILES_DB: list[dict[str, Any]] = [
    {
        "id": "std-201",
        "name": "Sonal Gupta",
        "email": "sonal2112g@gmail.com",
        "department": "Computer Science & AI",
        "year": "3rd Year",
        "avatar_initials": "SG",
        "avatar_color": "#ec4899",
        "my_skills": ["AI/ML", "Python", "PyTorch", "React", "NLP", "FastAPI"],
        "looking_for_skills": ["UI/UX", "Backend", "Mobile Dev"],
        "project_interests": ["Hackathon", "AI/ML Project", "Web Application"],
        "availability": "Weekend Hackathon (24-48 hrs)",
        "languages": ["Hinglish", "Hindi", "English"],
        "bio": "AI/ML developer passionate about NLP & web apps. Looking for Hackathon team members!",
        "projects_completed": 7,
        "rating": 4.95,
    },
    {
        "id": "std-202",
        "name": "Isha Kashyap",
        "email": "ishakashyap17@gmail.com",
        "department": "Software Engineering & UX",
        "year": "3rd Year",
        "avatar_initials": "IK",
        "avatar_color": "#8b5cf6",
        "my_skills": ["UI/UX", "Figma", "React", "Frontend", "User Research", "Tailwind"],
        "looking_for_skills": ["AI/ML", "Python", "Backend"],
        "project_interests": ["Hackathon", "Web Application", "Mobile App"],
        "availability": "15-20 hrs/week",
        "languages": ["English", "Hindi", "Hinglish"],
        "bio": "Creative UI/UX designer & frontend engineer. Passionate about sleek micro-interactions.",
        "projects_completed": 6,
        "rating": 4.9,
    },
    {
        "id": "std-101",
        "name": "Namya Jain",
        "email": "namyaajain29@gmail.com",
        "department": "Computer Science & Engineering",
        "year": "3rd Year",
        "avatar_initials": "NJ",
        "avatar_color": "#4f46e5",
        "my_skills": ["UI/UX Design", "Figma", "React", "CSS3", "Tailwind"],
        "looking_for_skills": ["AI/ML", "Python", "Backend", "FastAPI"],
        "project_interests": ["Hackathon", "AI/ML Project", "Web Application"],
        "availability": "Weekend Hackathon (24-48 hrs)",
        "languages": ["Hinglish", "Hindi", "English"],
        "bio": "Passionate UI/UX designer & frontend engineer. Built 4 hackathon award-winning designs.",
        "projects_completed": 6,
        "rating": 4.9,
    },
    {
        "id": "std-102",
        "name": "Priya Patel",
        "email": "priya.patel@gmail.com",
        "department": "Software Engineering",
        "year": "4th Year",
        "avatar_initials": "PP",
        "avatar_color": "#059669",
        "my_skills": ["Backend", "Python", "FastAPI", "PostgreSQL", "Docker", "Node.js"],
        "looking_for_skills": ["React", "UI/UX", "AI/ML", "Frontend"],
        "project_interests": ["Hackathon", "Web Application", "Capstone"],
        "availability": "15-20 hrs/week",
        "languages": ["English", "Hindi", "Gujarati"],
        "bio": "Backend system architect interested in high-scale APIs and database optimization.",
        "projects_completed": 8,
        "rating": 4.8,
    },
    {
        "id": "std-103",
        "name": "Aarav Gupta",
        "email": "aarav.gupta@gmail.com",
        "department": "Data Science & AI",
        "year": "3rd Year",
        "avatar_initials": "AG",
        "avatar_color": "#d97706",
        "my_skills": ["AI/ML", "PyTorch", "Python", "Scikit-Learn", "Computer Vision", "NLP"],
        "looking_for_skills": ["React", "UI/UX", "Mobile Dev", "Node.js"],
        "project_interests": ["Hackathon", "AI/ML Project", "Research"],
        "availability": "Weekend Hackathon (24-48 hrs)",
        "languages": ["Hinglish", "English", "Hindi"],
        "bio": "AI developer focusing on LLMs and computer vision applications.",
        "projects_completed": 5,
        "rating": 4.9,
    },
    {
        "id": "std-104",
        "name": "Ananya Verma",
        "email": "ananya.verma@greenfield.edu",
        "department": "Design & Interactive Media",
        "year": "2nd Year",
        "avatar_initials": "AV",
        "avatar_color": "#ec4899",
        "my_skills": ["UI/UX", "Figma", "User Research", "Prototyping", "Adobe XD"],
        "looking_for_skills": ["React", "AI/ML", "Python", "Web Development"],
        "project_interests": ["Hackathon", "Web Application", "Mobile App"],
        "availability": "10-15 hrs/week",
        "languages": ["Hindi", "English", "Hinglish"],
        "bio": "Creative designer specializing in intuitive micro-interactions and sleek web themes.",
        "projects_completed": 4,
        "rating": 4.7,
    },
    {
        "id": "std-105",
        "name": "Devansh Joshi",
        "email": "devansh.joshi@greenfield.edu",
        "department": "Computer Science & Engineering",
        "year": "4th Year",
        "avatar_initials": "DJ",
        "avatar_color": "#2563eb",
        "my_skills": ["Fullstack", "React", "Node.js", "MongoDB", "Express", "TypeScript"],
        "looking_for_skills": ["AI/ML", "Python", "UI/UX"],
        "project_interests": ["Hackathon", "Web Application"],
        "availability": "Weekend Hackathon (24-48 hrs)",
        "languages": ["Hinglish", "Hindi", "English"],
        "bio": "MERN stack developer eager to integrate AI models into web platforms.",
        "projects_completed": 7,
        "rating": 4.85,
    },
    {
        "id": "std-106",
        "name": "Sophia Chen",
        "email": "sophia.chen@greenfield.edu",
        "department": "Mobile Application Engineering",
        "year": "3rd Year",
        "avatar_initials": "SC",
        "avatar_color": "#8b5cf6",
        "my_skills": ["Mobile Dev", "Flutter", "Dart", "iOS", "Android", "Firebase"],
        "looking_for_skills": ["UI/UX", "Backend", "AI/ML"],
        "project_interests": ["Hackathon", "Mobile App"],
        "availability": "15 hrs/week",
        "languages": ["English", "Mandarin"],
        "bio": "Cross-platform mobile developer passionate about smooth animations and sleek UX.",
        "projects_completed": 5,
        "rating": 4.9,
    },
    {
        "id": "std-107",
        "name": "Karan Singh",
        "email": "karan.singh@greenfield.edu",
        "department": "Cybersecurity & Networks",
        "year": "3rd Year",
        "avatar_initials": "KS",
        "avatar_color": "#06b6d4",
        "my_skills": ["Cybersecurity", "Python", "Linux", "Ethical Hacking", "DevOps"],
        "looking_for_skills": ["React", "UI/UX", "AI/ML"],
        "project_interests": ["Hackathon", "Research", "Security Audit"],
        "availability": "Weekend Hackathon (24-48 hrs)",
        "languages": ["Punjabi", "Hindi", "English"],
        "bio": "Security enthusiast looking to build secure AI and web applications.",
        "projects_completed": 4,
        "rating": 4.8,
    },
]

# In-memory Collaboration Requests Database with Pending, Accepted, and Declined statuses
COLLABORATION_REQUESTS_DB: list[dict[str, Any]] = [
    {
        "id": "req-demo-01",
        "sender_name": "Sonal Gupta",
        "sender_email": "sonal2112g@gmail.com",
        "target_student_id": "std-101",
        "target_student_name": "Namya Jain",
        "target_student_email": "namyaajain29@gmail.com",
        "project_type": "Hackathon Project",
        "user_skills": ["AI/ML", "React"],
        "required_skills": ["UI/UX", "Figma"],
        "note": "Hi Namya! Saw your UI/UX portfolio, would love to collaborate for the upcoming Hackathon!",
        "status": "Accepted",
        "timestamp": "2026-09-23 14:30",
    },
    {
        "id": "req-demo-02",
        "sender_name": "Sonal Gupta",
        "sender_email": "sonal2112g@gmail.com",
        "target_student_id": "std-202",
        "target_student_name": "Isha Kashyap",
        "target_student_email": "ishakashyap17@gmail.com",
        "project_type": "Web Application",
        "user_skills": ["React", "FastAPI"],
        "required_skills": ["Frontend", "UI/UX"],
        "note": "Hey Isha! Interested in collaborating on a web app project together?",
        "status": "Pending",
        "timestamp": "2026-09-23 16:15",
    },
    {
        "id": "req-demo-03",
        "sender_name": "Sonal Gupta",
        "sender_email": "sonal2112g@gmail.com",
        "target_student_id": "std-102",
        "target_student_name": "Priya Patel",
        "target_student_email": "priya.patel@gmail.com",
        "project_type": "Capstone",
        "user_skills": ["Python", "PyTorch"],
        "required_skills": ["Backend", "PostgreSQL"],
        "note": "Hi Priya! Are you available for capstone project collaboration?",
        "status": "Declined",
        "timestamp": "2026-09-22 11:20",
    },
]

PARTNER_INTENT_KEYWORDS = [
    "partner", "partners", "team", "teammate", "teammates", "member", "members",
    "hackathon", "project partner", "need members", "looking for members", "group",
    "chahiye", "aata hai", "mujhe", "chahiye 2", "chahiye 1", "hackathon project",
    "collab", "collaboration", "find student", "find partner", "team search",
    "invite", "send invitation", "invitation to", "send invite",
    "ਕੋਈ", "ਸਾਥੀ", "ਟੀਮ"
]


def extract_partner_intent(query: str, language: str = "auto") -> dict[str, Any]:
    """Analyze text/speech to extract partner search parameters and slot completion status."""
    clean_q = query.lower()
    is_partner_query = any(kw in clean_q for kw in PARTNER_INTENT_KEYWORDS)

    if not is_partner_query:
        return {"is_partner_intent": False}

    # Check for direct invite command (e.g. "Send an invitation to Priya" or "Invite Namya to project")
    target_student_match = None
    if any(k in clean_q for k in ["send an invitation", "send invitation", "invite", "bhejo"]):
        for student in STUDENT_PROFILES_DB:
            first_name = student["name"].split()[0].lower()
            if first_name in clean_q or student["name"].lower() in clean_q:
                target_student_match = student
                break

    # Extract user's own skills (offer)
    user_skills = []
    skill_patterns = {
        "AI/ML": r"\b(ai|ml|machine learning|deep learning|pytorch|tensorflow|nlp)\b",
        "React": r"\b(react|reactjs|frontend|nextjs|web)\b",
        "Python": r"\b(python|py)\b",
        "FastAPI": r"\b(fastapi)\b",
        "Backend": r"\b(backend|node|nodejs|express|django|flask)\b",
        "UI/UX": r"\b(ui|ux|ui/ux|figma|design|designer)\b",
        "Mobile Dev": r"\b(mobile|flutter|dart|android|ios)\b",
        "Data Science": r"\b(data science|data analyst|pandas)\b",
        "Cybersecurity": r"\b(cybersecurity|security|hacking)\b",
    }

    for skill, pattern in skill_patterns.items():
        if re.search(pattern, clean_q):
            user_skills.append(skill)

    # Extract number of members requested
    member_count = None
    count_match = re.search(r"(\d+)\s*(members?|partners?|teammates?|log|bande)", clean_q)
    if count_match:
        member_count = int(count_match.group(1))
    elif " 2 " in clean_q or "do members" in clean_q or "two members" in clean_q:
        member_count = 2
    elif " 1 " in clean_q or "ek member" in clean_q or "one member" in clean_q or "a member" in clean_q:
        member_count = 1

    # Extract project type
    project_type = "Project"
    if "hackathon" in clean_q:
        project_type = "Hackathon"
    elif "research" in clean_q:
        project_type = "Research"
    elif "capstone" in clean_q:
        project_type = "Capstone"
    elif "mobile" in clean_q:
        project_type = "Mobile App"
    elif "web" in clean_q:
        project_type = "Web Application"

    # Extract required partner skills if mentioned
    required_skills = []
    if any(w in clean_q for w in ["looking for", "chahiye", "need", "requires", "partner", "find"]):
        if re.search(r"\b(ui|ux|figma|designer|design)\b", clean_q) and "UI/UX" not in user_skills:
            required_skills.append("UI/UX")
        if re.search(r"\b(backend|fastapi|node|python|database)\b", clean_q) and "Backend" not in user_skills:
            required_skills.append("Backend")
        if re.search(r"\b(frontend|react|web)\b", clean_q) and "React" not in user_skills:
            required_skills.append("React")
        if re.search(r"\b(mobile|flutter)\b", clean_q) and "Mobile Dev" not in user_skills:
            required_skills.append("Mobile Dev")

    if not required_skills:
        if "AI/ML" in user_skills or "React" in user_skills:
            required_skills = ["UI/UX", "Backend", "Mobile Dev"]
        else:
            required_skills = ["React", "UI/UX", "AI/ML"]

    missing_fields = []
    if not member_count:
        missing_fields.append("number_of_members")
    if not user_skills:
        missing_fields.append("your_skills")

    return {
        "is_partner_intent": True,
        "user_skills": user_skills or ["AI/ML", "React"],
        "required_skills": required_skills,
        "project_type": project_type,
        "member_count": member_count or 2,
        "missing_fields": missing_fields,
        "target_student_match": target_student_match,
        "raw_query": query,
    }


def match_students(user_skills: list[str], required_skills: list[str], project_type: str = "Hackathon", limit: int = 4) -> list[dict[str, Any]]:
    """Match registered students based on complementary skills, project type, and availability."""
    matches = []

    user_skills_set = {s.lower() for s in user_skills}
    required_skills_set = {s.lower() for s in required_skills}

    for student in STUDENT_PROFILES_DB:
        score = 60  # Base compatibility score
        reasons = []

        student_skills_lower = [s.lower() for s in student["my_skills"]]
        student_looking_lower = [s.lower() for s in student["looking_for_skills"]]

        # 1. Match student's skills to requested skills
        direct_matches = []
        for req in required_skills:
            if any(req.lower() in sk for sk in student_skills_lower):
                score += 15
                direct_matches.append(req)

        if direct_matches:
            reasons.append(f"Possesses requested skills: {', '.join(direct_matches)}")

        # 2. Check if student is looking for skills the user offers (Mutual benefit match!)
        mutual_matches = []
        for offer in user_skills:
            if any(offer.lower() in lk for lk in student_looking_lower):
                score += 12
                mutual_matches.append(offer)

        if mutual_matches:
            reasons.append(f"Looking for partners with your skills ({', '.join(mutual_matches)})")

        # 3. Project type interest match
        if any(project_type.lower() in interest.lower() for interest in student["project_interests"]):
            score += 10
            reasons.append(f"Interested in {project_type} projects")

        # 4. Availability boost
        if project_type.lower() == "hackathon" and "hackathon" in student["availability"].lower():
            score += 5
            reasons.append("Ready for weekend hackathon sprint")

        # Cap score at 98% max
        final_score = min(score, 98)

        matches.append({
            "profile": student,
            "match_score": final_score,
            "match_reasons": reasons or ["Solid overall skills & availability match"],
        })

    # Sort matches by compatibility score descending
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches[:limit]


# API Router Endpoints

@partner_router.get("/profiles")
def get_profiles():
    """Retrieve all registered student profiles."""
    return {"profiles": STUDENT_PROFILES_DB}


@partner_router.post("/search")
def search_partners(payload: dict):
    """Search & match registered students based on custom skills & project parameters."""
    user_skills = payload.get("user_skills", ["AI/ML", "React"])
    required_skills = payload.get("required_skills", ["UI/UX", "Backend"])
    project_type = payload.get("project_type", "Hackathon")
    limit = payload.get("limit", 4)

    matches = match_students(user_skills, required_skills, project_type, limit)
    return {
        "user_skills": user_skills,
        "required_skills": required_skills,
        "project_type": project_type,
        "matches": matches,
    }


@partner_router.post("/request")
def create_collaboration_request(payload: dict, current_user: dict = Depends(get_current_user)):
    """Create one or more collaboration requests with email notifications after user confirmation."""
    target_ids = payload.get("target_student_ids")
    single_id = payload.get("target_student_id")

    if not target_ids and single_id:
        target_ids = [single_id]

    if not target_ids:
        raise HTTPException(status_code=400, detail="target_student_id or target_student_ids is required")

    project_type = payload.get("project_type", "Hackathon Project")
    note = payload.get("note", "Hey! Let's team up for the project.")
    user_skills = payload.get("user_skills", [])
    required_skills = payload.get("required_skills", [])

    sender_name = current_user.get("full_name", "Alex Morgan")
    sender_email = current_user.get("email", "student@greenfield.edu")

    sent_requests = []
    sent_emails = []

    for target_id in target_ids:
        target_student = next((s for s in STUDENT_PROFILES_DB if s["id"] == target_id), None)
        if not target_student:
            continue

        email_notification = send_collaboration_email(
            sender_name=sender_name,
            sender_email=sender_email,
            target_name=target_student["name"],
            target_email=target_student["email"],
            project_type=project_type,
            user_skills=user_skills,
            required_skills=required_skills,
            note=note,
        )

        request_item = {
            "id": f"req-{uuid.uuid4().hex[:8]}",
            "sender_name": sender_name,
            "sender_email": sender_email,
            "target_student_id": target_id,
            "target_student_name": target_student["name"],
            "target_student_email": target_student["email"],
            "project_type": project_type,
            "user_skills": user_skills,
            "required_skills": required_skills,
            "note": note,
            "status": "Pending",
            "email_notification": email_notification,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        COLLABORATION_REQUESTS_DB.append(request_item)
        sent_requests.append(request_item)
        sent_emails.append(f"{target_student['name']} ({target_student['email']})")

    if not sent_requests:
        raise HTTPException(status_code=404, detail="No matching student profiles found")

    recipients_str = ", ".join(sent_emails)
    return {
        "success": True,
        "message": f"Project Collaboration Invitation sent to {recipients_str}!",
        "email_status": f"📧 Email invitations dispatched to {recipients_str}",
        "requests": sent_requests,
        "request": sent_requests[0],
    }


@partner_router.post("/requests/{request_id}/status")
def update_request_status(request_id: str, payload: dict):
    """Update status of a sent collaboration invitation (Pending, Accepted, Declined)."""
    new_status = payload.get("status", "Pending")
    for req in COLLABORATION_REQUESTS_DB:
        if req["id"] == request_id:
            req["status"] = new_status
            return {"success": True, "request": req}
    raise HTTPException(status_code=404, detail="Collaboration invitation not found")


@partner_router.get("/requests")
def get_collaboration_requests(current_user: dict = Depends(get_current_user)):
    """Get all sent collaboration requests."""
    user_email = current_user.get("email", "student@greenfield.edu")
    user_requests = [r for r in COLLABORATION_REQUESTS_DB if r["sender_email"] == user_email or current_user.get("is_guest")]
    return {"requests": user_requests or COLLABORATION_REQUESTS_DB}


@partner_router.post("/smtp-config")
def update_smtp_config(payload: dict):
    """Configure real SMTP sender credentials for live email delivery and test connection."""
    smtp_user = payload.get("smtp_user", "").strip()
    smtp_password = payload.get("smtp_password", "").strip()
    smtp_host = payload.get("smtp_host", "smtp.gmail.com").strip()
    smtp_port = int(payload.get("smtp_port", 587))

    if not smtp_user or not smtp_password:
        raise HTTPException(status_code=400, detail="smtp_user and smtp_password are required")

    set_runtime_smtp_config(smtp_user, smtp_password, smtp_host, smtp_port)

    # Automatically test the SMTP connection upon saving
    test_res = test_smtp_connection(to_email=smtp_user)

    return {
        "success": test_res.get("success", False),
        "message": test_res.get("message"),
        "smtp_user": smtp_user,
        "test_result": test_res,
    }


@partner_router.post("/test-smtp")
def test_smtp_endpoint(payload: dict):
    """Test live SMTP connection and send a verification test email."""
    to_email = payload.get("to_email")
    res = test_smtp_connection(to_email)
    return res
