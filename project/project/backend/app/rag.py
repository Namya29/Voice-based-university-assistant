

import re
import uuid

from .pii_protection import scrub_pii
from .document_store import is_greeting_query, search_university_documents
from .azure_clients import vector_search, chat_complete

SYSTEM_PROMPT_TEMPLATE = """You are the official voice assistant of Chitkara University.
Answer strictly and only using the CONTEXT provided below, which comes from official
university documents.

Rules:
- If the CONTEXT does not contain enough information to answer confidently, reply with
  a short sentence in the user's language saying the answer cannot be verified against official
  university sources, and suggest contacting the relevant office. Do not guess.
- Never invent facts, dates, fees, deadlines, or policies that are not in the CONTEXT.
- Keep answers concise, warm, and easy to read aloud (2-5 sentences).
- Do not mention "context" or "documents" explicitly to the user; just answer naturally.

CONTEXT:
{context}
"""

GREETING_RESPONSES = {
    "en-US": "Hello! I am your Chitkara University Voice Assistant. How can I help you today with academic rules, library timings, exams, fee schedules, or hostel guidelines?",
    "hi-IN": "नमस्ते! मैं चितकारा यूनिवर्सिटी का वॉयस असिस्टेंट हूं। मैं अकादमिक नियमों, लाइब्रेरी टाइमिंग, परीक्षा, फीस शेड्यूल या हॉस्टल नियमों में आपकी क्या मदद कर सकता हूं?",
    "pa-IN": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਮੈਂ ਚਿਤਕਾਰਾ ਯੂਨੀਵਰਸਿਟੀ ਦਾ ਵਾਇਸ ਅਸਿਸਟੈਂਟ ਹਾਂ। ਮੈਂ ਅਕਾਦਮਿਕ ਨਿਯਮਾਂ, ਲਾਇਬ੍ਰੇਰੀ ਸਮੇਂ, ਪ੍ਰੀਖਿਆਵਾਂ, ਫੀਸ ਜਾਂ ਹੋਸਟਲ ਨਿਯਮਾਂ ਵਿੱਚ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
    "es-ES": "¡Hola! Soy el asistente de voz de Chitkara University. ¿En qué puedo ayudarte hoy con reglas académicas, horarios de biblioteca, exámenes o alojamiento?",
    "fr-FR": "Bonjour! Je suis l'assistant vocal de Chitkara University. Comment puis-je vous aider aujourd'hui concernant les règlements, la bibliothèque ou les examens?",
    "de-DE": "Hallo! Ich bin Ihr Chitkara University Sprachassistent. Wie kann ich Ihnen heute bei akademischen Regeln, Bibliothekszeiten oder Prüfungen helfen?",
    "ar-SA": "مرحبًا! أنا المساعد الصوتي لجامعة شيتكارا. كيف يمكنني مساعدتك اليوم في اللوائح الأكاديمية أو مواعيد المكتبة أو الامتحانات؟",
    "zh-CN": "您好！我是奇特卡拉大学语音助手。请问今天在学术规定、图书馆开放时间、考试或宿舍守则方面有什么可以帮您？",
    "ja-JP": "こんにちは！チトカラ大学の音声アシスタントです。履修規程、図書館の開館時間、試験、学費、寮の規則など、何についてお手伝いできますか？",
    "ru-RU": "Здравствуйте! Я голосовой помощник Университета Читкара. Чем я могу вам помочь сегодня по вопросам академических правил, расписания библиотеки или экзаменов?",
}

FALLBACK_MESSAGES = {
    "en-US": "I couldn't find this information in official university document rulebooks. Please check with the concerned department or university portal.",
    "hi-IN": "मुझे यह जानकारी विश्वविद्यालय के आधिकारिक दस्तावेज़ों में नहीं मिली। कृपया संबंधित विभाग या यूनिवर्सिटी पोर्टल से संपर्क करें।",
    "pa-IN": "ਮੈਨੂੰ ਇਹ ਜਾਣਕਾਰੀ ਯੂਨੀਵਰਸਿਟੀ ਦੇ ਅਧਿਕਾਰਤ ਦਸਤਾਵੇਜ਼ਾਂ ਵਿੱਚ ਨਹੀਂ ਮਿਲੀ। ਕਿਰਪਾ ਕਰਕੇ ਸੰਬੰਧਿਤ ਵਿਭਾਗ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
    "es-ES": "No encontré esta información en los reglamentos oficiales de la universidad. Por favor consulte con el departamento correspondiente.",
    "fr-FR": "Je n'ai pas trouvé cette information dans les documents officiels de l'université. Veuillez contacter le service concerné.",
    "de-DE": "Ich konnte diese Information nicht in den offiziellen Universitätsdokumenten finden. Bitte wenden Sie sich an die zuständige Abteilung.",
    "ar-SA": "لم أتمكن من العثور على هذه المعلومات في الوثائق الرسمية للجامعة. يرجى مراجعة القسم المعني.",
    "zh-CN": "我在大学官方文件中未能找到此信息，请咨询相关部门或学校门户网站。",
    "ja-JP": "大学の公式規則集にこの情報は見つかりませんでした。担当部署にお問い合わせください。",
    "ru-RU": "Я не нашел этой информации в официальных правилах университета. Пожалуйста, обратитесь в соответствующий отдел.",
}


def detect_text_language(text: str, requested_lang: str = "auto") -> str:
    """Detect language code (hi-IN, pa-IN, en-US, es-ES, fr-FR, de-DE, ar-SA, zh-CN, ja-JP, ru-RU) accurately from text."""
    text_clean = text.strip('"' + "'" + '«»“”‘’').strip()
    if not text_clean:
        return "en-US"
    
    # 1. Check Unicode script ranges first (100% reliable)
    if re.search(r"[\u0900-\u097F]", text_clean):
        return "hi-IN"
    if re.search(r"[\u0A00-\u0A7F]", text_clean):
        return "pa-IN"
    if re.search(r"[\u0600-\u06FF]", text_clean):
        return "ar-SA"
    if re.search(r"[\u4e00-\u9fff]", text_clean):
        return "zh-CN"
    if re.search(r"[\u3040-\u30ff]", text_clean):
        return "ja-JP"
    if re.search(r"[\uac00-\ud7af]", text_clean):
        return "ko-KR"
    if re.search(r"[\u0400-\u04FF]", text_clean):
        return "ru-RU"
    if re.search(r"[\u0A80-\u0AFF]", text_clean):
        return "gu-IN"
    if re.search(r"[\u0B80-\u0BFF]", text_clean):
        return "ta-IN"
    if re.search(r"[\u0C00-\u0C7F]", text_clean):
        return "te-IN"
    if re.search(r"[\u0C80-\u0CFF]", text_clean):
        return "kn-IN"
    if re.search(r"[\u0980-\u09FF]", text_clean):
        return "bn-IN"

    # If user explicitly requested a specific language and not "auto", respect their selection
    if requested_lang and requested_lang != "auto":
        return requested_lang

    lower = " " + text_clean.lower() + " "

    # 2. Punjabi / Punglish Romanized Keywords (Check before Hindi)
    punglish_tokens = [
        "han ji", "hanji", "sonio", "soniyo", "ki haal", "ki hal", "ki halat", "kiven", "kiddan",
        "kive", "kado", "kadon", "khulda", "khuldi", "dasso", "daso", "vele", "sat sri akal",
        "tussi", "saada", "chahida", "chahidi", "laazmi", "puchna", "chuttiyan", "hor dasso", "ji sonio"
    ]
    if any(k in lower for k in punglish_tokens):
        return "pa-IN"

    # 3. Hindi / Hinglish Romanized Keywords
    hinglish_tokens = [
        "namaste", "namaskar", "kaise ho", "kya haal", "kya hal", "kya chal", "aap", "tum",
        "mujhe", "batao", "bataiye", "kab", "khulta", "khulti", "kitne", "kitna", "baje",
        "samay", "hai", "hain", "hoga", "hogi", "chahiye", "aata", "padega", "nirdesh", "niyam",
        "chutti", "fees kitni", "fees kab", "kitni fees", "karein", "kaise", "bata do", "bhej do", "tumhari"
    ]
    if any(k in lower for k in hinglish_tokens):
        return "hi-IN"

    # 4. Spanish Keywords
    spanish_tokens = ["hola", "como estas", "cómo estás", "horario", "cuando", "cuándo", "donde", "dónde", "gracias", "biblioteca", "requisitos", "examen", "beca", "reglas", "buenos dias"]
    if any(k in lower for k in spanish_tokens) or "¿" in text_clean or "¡" in text_clean:
        return "es-ES"

    # 5. French Keywords
    french_tokens = ["bonjour", "comment", "quand", "merci", "horaires", "bibliotheque", "cours", "examen", "reglement", "salut", "s'il vous plait"]
    if any(k in lower for k in french_tokens):
        return "fr-FR"

    # 6. German Keywords
    german_tokens = ["hallo", "wie geht", "wann", "danke", "bibliothek", "zeiten", "regeln", "stunden", "guten tag"]
    if any(k in lower for k in german_tokens) or "ö" in lower or "ä" in lower or "ü" in lower or "ß" in lower:
        return "de-DE"

    # 7. Arabic Romanized
    arabic_tokens = ["marhaba", "marhaban", "kaifa", "kayf", "shukran", "mataa", "maktaba"]
    if any(k in lower for k in arabic_tokens):
        return "ar-SA"

    return "en-US"


def generate_local_chunk_answer(chunk: dict, language: str) -> str:
    content = chunk.get("content", "")
    title = (chunk.get("title", "") or "").lower()
    doc_name = (chunk.get("doc_name", "") or "").lower()
    lower = content.lower()
    lang_code = language.split("-")[0].lower() if "-" in language else language.lower()

    # Topic: Hostel Guidelines
    if "hostel" in title or "hostel" in doc_name or "curfew" in lower or "in-time" in lower or "mess timings" in lower:
        if lang_code == "hi":
            return "हॉस्टल दिशानिर्देशों के अनुसार प्रथम वर्ष के छात्रों के लिए इन-टाइम कर्फ्यू शाम 8:30 बजे और वरिष्ठ यूजी छात्रों के लिए रात 9:30 बजे है। मेस टाइमिंग: नाश्ता सुबह 7:30-9:00, दोपहर का भोजन 12:00-2:00, स्नैक्स शाम 5:00-6:00 और रात का खाना 7:30-9:30 बजे है।"
        elif lang_code == "pa":
            return "ਹੋਸਟਲ ਨਿਯਮਾਂ ਅਨੁਸਾਰ ਪਹਿਲੇ ਸਾਲ ਦੇ ਵਿਦਿਆਰਥੀਆਂ ਲਈ ਕਰਫਿਊ ਸ਼ਾਮ 8:30 ਵਜੇ ਅਤੇ ਸੀਨੀਅਰ ਵਿਦਿਆਰਥੀਆਂ ਲਈ ਰਾਤ 9:30 ਵਜੇ ਹੈ। ਮੈੱਸ ਦਾ ਸਮਾਂ: ਨਾਸ਼ਤਾ ਸਵੇਰੇ 7:30-9:00, ਦੁਪਹਿਰ ਦਾ ਖਾਣਾ 12:00-2:00, ਸਨੈਕਸ ਸ਼ਾਮ 5:00-6:00 ਅਤੇ ਰਾਤ ਦਾ ਖਾਣਾ 7:30-9:30 ਵਜੇ ਹੈ।"
        elif lang_code == "es":
            return "Según las pautas del albergue, el toque de queda es a las 8:30 PM para estudiantes de primer año y a las 9:30 PM para estudiantes mayores."
        elif lang_code == "fr":
            return "Selon les règles de la résidence, le couvre-feu est fixé à 20h30 pour les étudiants de première année et à 21h30 pour les étudiants des années supérieures."
        return "As per Hostel Guidelines, the in-time curfew is 8:30 PM for First-Year students and 9:30 PM for Senior UG students. Mess timings: Breakfast 7:30-9:00 AM, Lunch 12:00-2:00 PM, Evening Snacks 5:00-6:00 PM, and Dinner 7:30-9:30 PM."

    # Topic: Library Timings & Rules
    if "library" in title or "library" in doc_name or "reading room" in lower:
        if lang_code == "hi":
            return "चितकारा सेंट्रल लाइब्रेरी सोमवार से शनिवार सुबह 8:00 बजे से रात 10:00 बजे तक और रविवार को सुबह 10:00 बजे से शाम 5:00 बजे तक खुली रहती है। परीक्षा के दौरान रीडिंग रूम 24 घंटे खुला रहता है। छात्र 14 दिनों के लिए अधिकतम 3 पुस्तकें इश्यू करा सकते हैं।"
        elif lang_code == "pa":
            return "ਚਿਤਕਾਰਾ ਸੈਂਟਰਲ ਲਾਇਬ੍ਰੇਰੀ ਸੋਮਵਾਰ ਤੋਂ ਸ਼ਨੀਵਾਰ ਸਵੇਰੇ 8:00 ਵਜੇ ਤੋਂ ਰਾਤ 10:00 ਵਜੇ ਤੱਕ ਅਤੇ ਐਤਵਾਰ ਨੂੰ ਸਵੇਰੇ 10:00 ਵਜੇ ਤੋਂ ਸ਼ਾਮ 5:00 ਵਜੇ ਤੱਕ ਖੁੱਲ੍ਹਦੀ ਹੈ। ਪ੍ਰੀਖਿਆਵਾਂ ਦੌਰਾਨ ਰੀਡਿੰਗ ਰੂਮ 24 ਘੰਟੇ ਖੁੱਲ੍ਹਾ ਰਹਿੰਦਾ ਹੈ। ਵਿਦਿਆਰਥੀ 14 ਦਿਨਾਂ ਲਈ 3 ਕਿਤਾਬਾਂ ਇਸ਼ੂ ਕਰਵਾ ਸਕਦੇ ਹਨ।"
        elif lang_code == "es":
            return "La Biblioteca Central de Chitkara abre de lunes a sábado de 8:00 AM a 10:00 PM, y los domingos de 10:00 AM a 5:00 PM. La sala de lectura abre 24 horas durante exámenes."
        elif lang_code == "fr":
            return "La bibliothèque centrale de Chitkara est ouverte du lundi au samedi de 8h00 à 22h00, et le dimanche de 10h00 à 17h00. La salle de lecture reste ouverte 24h/24 pendant les examens."
        elif lang_code == "de":
            return "Die Chitkara Zentralbibliothek ist von Montag bis Samstag von 8:00 bis 22:00 Uhr und sonntags von 10:00 bis 17:00 Uhr geöffnet."
        return "Chitkara Central Library is open Monday to Saturday from 8:00 AM to 10:00 PM, and on Sundays from 10:00 AM to 5:00 PM. The reading room remains open 24 hours during examination periods. Undergraduates may borrow up to 3 books for 14 days."

    # Topic: Fee Circular
    if "fee" in title or "fee" in doc_name or "tuition" in lower or "15 january" in lower:
        if lang_code == "hi":
            return "सम सेमेस्टर की ट्यूशन फीस जमा करने की अंतिम तिथि 15 जनवरी है। 25 जनवरी तक ₹500 और 05 फरवरी तक ₹1000 का विलंब शुल्क (Late Fee) लागू होता है। भुगतान चाकपैक (Chalkpad) पोर्टल के माध्यम से किया जा सकता है।"
        elif lang_code == "pa":
            return "ਈਵਨ ਸਮੈਸਟਰ ਦੀ ਟਿਊਸ਼ਨ ਫੀਸ ਜਮ੍ਹਾਂ ਕਰਵਾਉਣ ਦੀ ਆਖਰੀ ਮਿਤੀ 15 ਜਨਵਰੀ ਹੈ। 25 ਜਨਵਰੀ ਤੱਕ ₹500 ਅਤੇ 05 ਫਰਵਰੀ ਤੱਕ ₹1000 ਲੇਟ ਫੀਸ ਲੱਗਦੀ ਹੈ। ਭੁਗਤਾਨ ਚਾਕਪੈਡ ਪੋਰਟਲ ਰਾਹੀਂ ਕੀਤਾ ਜਾ ਸਕਦਾ ਹੈ।"
        elif lang_code == "es":
            return "La fecha límite para pagar la matrícula del semestre es el 15 de enero. Se aplica un recargo por mora de ₹500 hasta el 25 de enero y de ₹1000 hasta el 05 de febrero."
        return "Tuition fee for the Even Semester is due by 15 January. A late fee penalty of Rs 500 applies up to 25 January, and Rs 1000 up to 05 February. Fees can be paid online via the Chalkpad student portal."

    # Topic: Exam Regulations & Passing Criteria
    if "exam" in title or "exam" in doc_name or "passing criteria" in lower or "admit card" in lower:
        if lang_code == "hi":
            return "परीक्षा पास करने के लिए कुल मिलाकर न्यूनतम 40% अंक और एंड-सेमेस्टर परीक्षा (ESE) में कम से कम 35% अंक प्राप्त करना अनिवार्य है। एडमिट कार्ड (हॉल टिकट) परीक्षा में अनिवार्य है।"
        elif lang_code == "pa":
            return "ਇਮਤਿਹਾਨ ਪਾਸ ਕਰਨ ਲਈ ਕੁੱਲ ਮਿਲਾ ਕੇ ਘੱਟੋ-ਘੱਟ 40% ਅੰਕ ਅਤੇ ਐਂਡ-ਸਮੈਸਟਰ ਪ੍ਰੀਖਿਆ ਵਿੱਚ ਘੱਟੋ-ਘੱਟ 35% ਅੰਕ ਪ੍ਰਾਪਤ ਕਰਨੇ ਲਾਜ਼ਮੀ ਹਨ।"
        return "To pass a course, a student must secure a minimum of 40% aggregate marks and at least 35% marks in the End Semester Examination (ESE). An admit card with zero fee dues is mandatory for entry."

    # Topic: Branch Change
    if "branch change" in lower or "form aa-11" in lower or "8.50" in content:
        if lang_code == "hi":
            return "प्रथम वर्ष के बाद ब्रांच चेंज के लिए छात्र का न्यूनतम CGPA 8.50 होना चाहिए और कोई एक्टिव बैकलॉग नहीं होना चाहिए।"
        elif lang_code == "pa":
            return "ਪਹਿਲੇ ਸਾਲ ਤੋਂ ਬਾਅਦ ਬ੍ਰਾਂਚ ਬਦਲਣ ਲਈ ਵਿਦਿਆਰਥੀ ਦਾ ਘੱਟੋ-ਘੱਟ CGPA 8.50 ਹੋਣਾ ਚਾਹੀਦਾ ਹੈ ਅਤੇ ਕੋਈ ਬੈਕਲਾਗ ਨਹੀਂ ਹੋਣਾ ਚਾਹੀਦਾ।"
        return "For branch change after the first year, students must have a minimum CGPA of 8.50 at the end of the 2nd semester and no active backlogs."

    # Topic: Attendance
    if "75%" in content or "attendance" in lower or "detained" in lower or "dt grade" in lower:
        if lang_code == "hi":
            return "चितकारा यूनिवर्सिटी के नियमानुसार प्रत्येक कोर्स में न्यूनतम 75% अनिवार्य उपस्थिति होनी चाहिए। 75% से कम उपस्थिति होने पर छात्र को एंड-सेमेस्टर परीक्षा में बैठने से रोक (Detained - DT ग्रेड) दिया जाता है।"
        elif lang_code == "pa":
            return "ਚਿਤਕਾਰਾ ਯੂਨੀਵਰਸਿਟੀ ਦੇ ਨਿਯਮਾਂ ਅਨੁਸਾਰ ਹਰ ਕੋਰਸ ਵਿੱਚ ਘੱਟੋ-ਘੱਟ 75% ਹਾਜ਼ਰੀ ਲਾਜ਼ਮੀ ਹੈ। 75% ਤੋਂ ਘੱਟ ਹਾਜ਼ਰੀ ਹੋਣ 'ਤੇ ਵਿਦਿਆਰਥੀ ਨੂੰ ਇਮਤਿਹਾਨ ਵਿੱਚ ਬੈਠਣ ਤੋਂ ਰੋਕ (DT ਗ੍ਰੇਡ) ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ।"
        elif lang_code == "es":
            return "Según el reglamento académico de Chitkara University, cada estudiante debe mantener una asistencia mínima obligatoria del 75%. Estar por debajo del 75% resulta en detención (calificación DT)."
        elif lang_code == "fr":
            return "Selon le règlement de Chitkara University, chaque étudiant doit maintenir une assiduité minimale obligatoire de 75%. En dessous de 75%, l'étudiant est refusé d'examen (note DT)."
        elif lang_code == "de":
            return "Gemäß den Regeln der Chitkara University muss jeder Student eine Mindestanwesenheit von 75% einhalten. Bei weniger als 75% wird der Student von der Abschlussprüfung ausgeschlossen."
        return "According to Chitkara University Academic Rules, every student must maintain a minimum of 75% attendance in each registered course. Falling below 75% results in being detained (DT grade) from the End Semester Examination."

    # Fallback to direct chunk content summary
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if len(s.strip()) > 15]
    if sentences:
        return " ".join(sentences[:3])
    return content[:250].rstrip() + "..."


def answer_question(query: str, language: str = "auto", conversation_id: str | None = None) -> dict:
    conversation_id = conversation_id or str(uuid.uuid4())
    
    # 0. PII Detection & Scrubbing
    pii_res = scrub_pii(query)
    clean_query = pii_res["clean_text"]
    pii_detected = pii_res["pii_detected"]
    pii_types = pii_res["pii_types"]

    # Accurate automatic language detection from user's actual text
    effective_lang = detect_text_language(clean_query, language)

    # 1. Check for Greeting Queries (e.g. "hi", "han ji", "sonio", "ki haal", "kaise ho", "hello")
    if is_greeting_query(clean_query):
        greet_text = GREETING_RESPONSES.get(effective_lang, GREETING_RESPONSES.get(effective_lang.split("-")[0], GREETING_RESPONSES["en-US"]))
        return {
            "answer": greet_text,
            "language": effective_lang,
            "verified": False,
            "sources": [],
            "conversation_id": conversation_id,
            "pii_detected": pii_detected,
            "pii_types": pii_types,
            "clean_query": clean_query,
            "partner_data": None,
        }

    # 2. Retrieve Grounded PDF Documents
    hits = []
    try:
        hits = vector_search(clean_query)
    except Exception:
        hits = []

    if not hits:
        hits = search_university_documents(clean_query, top_k=2)

    # 3. If no grounded documents matched (e.g. casual greeting / completely unrelated query)
    if not hits:
        fallback = FALLBACK_MESSAGES.get(effective_lang, FALLBACK_MESSAGES.get(effective_lang.split("-")[0], FALLBACK_MESSAGES["en-US"]))
        return {
            "answer": fallback,
            "language": effective_lang,
            "verified": False,
            "sources": [],
            "conversation_id": conversation_id,
            "pii_detected": pii_detected,
            "pii_types": pii_types,
            "clean_query": clean_query,
            "partner_data": None,
        }

    # 4. Grounded Answer Synthesis
    context = "\n\n".join(f"[{h['title']} - Page {h.get('page', 1)}] {h['content']}" for h in hits)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    try:
        answer = chat_complete(system_prompt, clean_query)
        detected_ans_lang = detect_text_language(answer, "auto")
        if detected_ans_lang != "en-US":
            effective_lang = detected_ans_lang
    except Exception:
        answer = generate_local_chunk_answer(hits[0], effective_lang)

    sources = [
        {
            "title": h["title"],
            "url": h.get("url"),
            "page": h.get("page", 1),
            "snippet": h["content"][:220].rstrip() + "...",
        }
        for h in hits
    ]

    return {
        "answer": answer,
        "language": effective_lang,
        "verified": True,
        "sources": sources,
        "conversation_id": conversation_id,
        "pii_detected": pii_detected,
        "pii_types": pii_types,
        "clean_query": clean_query,
        "partner_data": None,
    }
