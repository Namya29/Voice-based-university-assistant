from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_languages():
    res = client.get("/api/config/languages")
    assert res.status_code == 200
    assert "en-US" in res.json()["languages"]


def test_ask_empty_query_rejected():
    res = client.post("/api/ask", json={"query": "", "language": "en-US"})
    assert res.status_code == 400


@patch("app.rag.vector_search", return_value=[])
def test_ask_no_sources_returns_unverified(mock_search):
    res = client.post("/api/ask", json={"query": "Random unrelated question", "language": "en-US"})
    assert res.status_code == 200
    body = res.json()
    assert body["verified"] is False
    assert body["sources"] == []


@patch("app.rag.chat_complete", return_value="The fall semester begins August 25.")
@patch(
    "app.rag.vector_search",
    return_value=[{"title": "Academic Calendar", "url": None, "page": 1, "content": "Fall semester starts August 25.", "score": 0.9}],
)
def test_ask_with_sources_is_verified(mock_search, mock_chat):
    res = client.post("/api/ask", json={"query": "When does fall semester start?", "language": "en-US"})
    body = res.json()
    assert body["verified"] is True
    assert len(body["sources"]) == 1
    assert "August" in body["answer"]


@patch("app.rag.vector_search", return_value=[])
def test_ask_hindi_auto_detection(mock_search):
    res = client.post("/api/ask", json={"query": "पुस्तकालय कब खुलता है?", "language": "auto"})
    assert res.status_code == 200
    body = res.json()
    assert body["language"] == "hi-IN"


@patch("app.rag.vector_search", return_value=[])
def test_ask_spanish_auto_detection(mock_search):
    res = client.post("/api/ask", json={"query": "¿Cuáles son los requisitos de admisión?", "language": "auto"})
    assert res.status_code == 200
    body = res.json()
    assert body["language"] == "es-ES"


@patch("app.rag.vector_search", return_value=[])
def test_ask_punjabi_auto_detection(mock_search):
    res = client.post("/api/ask", json={"query": "ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ?", "language": "auto"})
    assert res.status_code == 200
    body = res.json()
    assert body["language"] == "pa-IN"


def test_pii_scrubbing():
    from app.pii_protection import scrub_pii
    res = scrub_pii("Call me at 9876543210 or email test@gmail.com")
    assert res["pii_detected"] is True
    assert "[REDACTED_PHONE]" in res["clean_text"]
    assert "[REDACTED_EMAIL]" in res["clean_text"]


def test_auth_login_and_me():
    res = client.post("/api/auth/login", json={"email": "student@greenfield.edu", "password": "student123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token is not None

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user = me_res.json()["user"]
    assert user["email"] == "student@greenfield.edu"
    assert user["role"] == "student"


def test_university_pdf_hinglish_query():
    query = "Library timings kya hai aur kab tak khulta hai?"
    res = client.post("/api/ask", json={"query": query, "language": "auto"})
    assert res.status_code == 200
    body = res.json()
    assert body["verified"] is True
    assert len(body["sources"]) > 0
    assert "Central Library" in body["sources"][0]["title"]


def test_partner_profiles_api():
    res = client.get("/api/partners/profiles")
    assert res.status_code == 200
    assert len(res.json()["profiles"]) >= 5


def test_partner_search_api():
    payload = {
        "user_skills": ["AI/ML", "React"],
        "required_skills": ["UI/UX", "Backend"],
        "project_type": "Hackathon",
    }
    res = client.post("/api/partners/search", json=payload)
    assert res.status_code == 200
    matches = res.json()["matches"]
    assert len(matches) > 0
    assert matches[0]["match_score"] > 60


def test_collaboration_request_api():
    payload = {
        "target_student_id": "std-101",
        "project_type": "Hackathon Project",
        "note": "Let's work together!",
        "user_skills": ["AI/ML", "React"],
        "required_skills": ["UI/UX"],
    }
    res = client.post("/api/partners/request", json=payload)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["request"]["target_student_name"] == "Namya Jain"


def test_collaboration_email_request_to_sonal_and_isha():
    # Test request to Sonal Garg (sonal2112g@gmail.com)
    res_sonal = client.post("/api/partners/request", json={
        "target_student_id": "std-201",
        "project_type": "Hackathon Project",
        "note": "Hi Sonal! Let's build an AI Hackathon project together.",
        "user_skills": ["AI/ML", "React"],
        "required_skills": ["UI/UX"],
    })
    assert res_sonal.status_code == 200
    body_sonal = res_sonal.json()
    assert body_sonal["success"] is True
    assert "sonal2112g@gmail.com" in body_sonal["message"]
    assert "email_status" in body_sonal

    # Test request to Isha Kashyap (ishakashyap17@gmail.com)
    res_isha = client.post("/api/partners/request", json={
        "target_student_id": "std-202",
        "project_type": "Hackathon Project",
        "note": "Hi Isha! Need your UI/UX expertise for our Hackathon team.",
        "user_skills": ["AI/ML", "React"],
        "required_skills": ["UI/UX"],
    })
    assert res_isha.status_code == 200
    body_isha = res_isha.json()
    assert body_isha["success"] is True
    assert "ishakashyap17@gmail.com" in body_isha["message"]
    assert "email_status" in body_isha


