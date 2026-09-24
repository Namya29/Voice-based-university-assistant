"""Document store and retriever for Chitkara University Official PDF Regulations.
Loads and indexes:
1. Academic_Rules_2025.pdf
2. Central_Library_Rules.pdf
3. Exam_Regulations.pdf
4. Fee_Circular_Even_Sem.pdf
5. Hostel_Guidelines.pdf
"""
import json
import os
import re

CHUNKS_FILE = os.path.join(os.path.dirname(__file__), "chitkara_chunks.json")

def load_chunks() -> list[dict]:
    if os.path.exists(CHUNKS_FILE):
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

UNIVERSITY_CHUNKS = load_chunks()

STOP_WORDS = {
    "is", "to", "in", "the", "a", "an", "and", "or", "of", "for", "on", "at", "by",
    "from", "with", "as", "into", "if", "han", "ji", "ki", "ka", "ke", "ko", "se",
    "me", "hai", "hain", "kya", "tu", "tum", "aap", "da", "di", "de", "nu", "si",
    "ho", "tha", "thi", "are", "you", "my", "your", "this", "that", "it", "so"
}

TOPIC_KEYWORDS = {
    "attendance": [
        "attendance", "75%", "present", "absent", "detained", "dt grade", "exemption",
        "medical", "duty leave", "form aa-04", "form aa-07", "65%", "हाजिरी", "अटेंडेंस",
        "हाज़िरी", "ਛੁੱਟੀ", "ਹਾਜ਼ਰੀ", "shortage", "shortfall"
    ],
    "grading": [
        "grade", "grading", "cgpa", "sgpa", "relative grading", "o grade", "a+ grade",
        "pass", "fail", "backlog", "reappear", "10-point", "marks", "पॉइंटर", "नंबर", "रिजल्ट",
        "ਗ੍ਰੇਡ", "ਅੰਕ", "re-evaluation", "rechecking"
    ],
    "branch_change": [
        "branch change", "specialisation change", "8.50 cgpa", "form aa-11", "change of branch",
        "ब्रांच", "ब्रांच चेंज", "ਬ੍ਰਾਂਚ ਬਦਲਣਾ"
    ],
    "library": [
        "library", "timings", "reading room", "borrow", "books", "fine", "overdue", "8 am",
        "10 pm", "issuance", "librarian", "लाइब्रेरी", "पुस्तकालय", "किताब", "किताबें", "ਕਿਤਾਬ", "ਲਾਇਬ੍ਰੇਰੀ"
    ],
    "exam": [
        "exam", "examination", "admit card", "hall ticket", "passing", "35%", "40%", "umc",
        "unfair means", "cia", "ese", "mid term", "end semester", "seating", "परीक्षा", "एग्जाम", "ਇਮਤਿਹਾਨ"
    ],
    "fee": [
        "fee", "tuition fee", "deadline", "late fee", "penalty", "due date", "15 january",
        "refund", "scholarship", "fees", "फीस", "चालान", "स्कॉलरशिप", "ਫੀਸ", "ਵਜ਼ੀਫ਼ਾ"
    ],
    "hostel": [
        "hostel", "curfew", "in-time", "in time", "mess", "breakfast", "lunch", "dinner",
        "night out", "ragging", "anti-ragging", "visitor", "8:30 pm", "9:30 pm", "हॉस्टल",
        "मेस", "खाना", "होस्टल", "ਹੋਸਟਲ", "ਮੈੱਸ"
    ]
}

GREETING_WORDS = [
    "hi", "hello", "hey", "hola", "bonjour", "namaste", "namaskar", "sat sri akal",
    "sasriakal", "pranam", "ram ram", "kem cho", "vanakkam", "ciao", "hallo", "marhaba",
    "ni hao", "konnichiwa", "annyeong", "good morning", "good afternoon", "good evening",
    "how are you", "how r u", "kaise ho", "kya haal", "kya hal", "ki haal", "ki hal",
    "ki halat", "kiven ho", "kiven o", "kiddan", "kive ho", "whats up", "what's up",
    "who are you", "tum kaun ho", "who made you", "sonio", "soniyo", "han ji", "hanji",
    "sab badhiya", "theek ho", "thik ho"
]

def is_greeting_query(query: str) -> bool:
    clean_q = re.sub(r'[^\w\s]', ' ', query.strip().lower())
    clean_q = re.sub(r'\s+', ' ', clean_q).strip()
    
    # Check exact or contained greeting phrase
    for phrase in GREETING_WORDS:
        if phrase in clean_q:
            return True
            
    # Check starts with greeting
    tokens = clean_q.split()
    if tokens and tokens[0] in ["hi", "hello", "hey", "hola", "bonjour", "namaste", "hallo", "ciao"]:
        return True
        
    return False

def search_university_documents(query: str, top_k: int = 2) -> list[dict]:
    """Retrieve grounded chunks from Chitkara University official rulebooks."""
    if not UNIVERSITY_CHUNKS:
        return []
    
    clean_q = re.sub(r'["\'«»“”‘’?,.!:]', ' ', query).lower().strip()
    raw_tokens = [w.strip() for w in clean_q.split() if len(w) > 1]
    # Filter out weak stopwords
    meaningful_tokens = [t for t in raw_tokens if t not in STOP_WORDS and len(t) > 2]
    
    if not meaningful_tokens:
        return []
    
    scored_chunks = []
    
    for chunk in UNIVERSITY_CHUNKS:
        content_lower = chunk["content"].lower()
        title_lower = chunk["title"].lower()
        header_lower = chunk.get("section_header", "").lower()
        
        score = 0.0
        
        # Token match in content and headers
        for t in meaningful_tokens:
            if t in header_lower:
                score += 6.0
            if t in title_lower:
                score += 4.0
            if t in content_lower:
                count = content_lower.count(t)
                score += min(count * 2.0, 8.0)
        
        # Topic category boost (weighted by keyword matches and section headers)
        for topic, kws in TOPIC_KEYWORDS.items():
            topic_matched = any(kw in clean_q for kw in kws)
            if topic_matched:
                matched_kws = [kw for kw in kws if kw in content_lower]
                if matched_kws:
                    score += 10.0 + len(matched_kws) * 2.0
                if any(kw in header_lower for kw in kws):
                    score += 12.0

        # Require strong relevance threshold
        if score >= 8.0:
            scored_chunks.append((score, chunk))
            
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for s, chunk in scored_chunks[:top_k]:
        results.append({
            "id": chunk["id"],
            "title": f"Chitkara University – {chunk['title']}",
            "doc_name": chunk["doc_name"],
            "page": chunk["page"],
            "section": chunk.get("section_header", ""),
            "content": chunk["content"],
            "score": s,
            "url": None
        })
        
    return results
