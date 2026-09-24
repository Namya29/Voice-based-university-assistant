"""PII (Personally Identifiable Information) detection and redaction engine."""
import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SSN_AADHAAR_PATTERN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b|\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b|\b[6-9]\d{9}\b"
)


def scrub_pii(text: str) -> dict:
    """Detect and redact PII elements from user query text.
    
    Returns a dict with:
      - clean_text: str (redacted string)
      - pii_detected: bool
      - pii_types: list[str] (e.g. ['Phone Number', 'Email Address'])
    """
    clean_text = text
    found_types = set()

    # 1. Email Redaction
    if EMAIL_PATTERN.search(clean_text):
        clean_text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", clean_text)
        found_types.add("Email Address")

    # 2. Credit/Debit Card Redaction
    def _card_replacer(match):
        digits_only = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits_only) <= 16:
            found_types.add("Credit/Debit Card")
            return "[REDACTED_CARD]"
        return match.group(0)

    clean_text = CARD_PATTERN.sub(_card_replacer, clean_text)

    # 3. National ID / SSN / Aadhaar Redaction
    if SSN_AADHAAR_PATTERN.search(clean_text):
        clean_text = SSN_AADHAAR_PATTERN.sub("[REDACTED_ID]", clean_text)
        found_types.add("National ID / Aadhaar / SSN")

    # 4. Phone Number Redaction
    if PHONE_PATTERN.search(clean_text):
        def _phone_replacer(match):
            val = match.group(0)
            if "REDACTED" in val:
                return val
            found_types.add("Phone Number")
            return "[REDACTED_PHONE]"

        clean_text = PHONE_PATTERN.sub(_phone_replacer, clean_text)

    return {
        "clean_text": clean_text,
        "pii_detected": len(found_types) > 0,
        "pii_types": sorted(list(found_types)),
    }
