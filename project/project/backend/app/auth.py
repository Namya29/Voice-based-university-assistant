"""Authentication & Authorization module with JWT token generation and role verification."""
import base64
import hashlib
import hmac
import json
import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = "greenfield-university-voice-assistant-jwt-secret-key"
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 86400  # 24 hours

security = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory user database initialized with standard demo accounts
USERS_DB = {
    "sonal2112g@gmail.com": {
        "email": "sonal2112g@gmail.com",
        "full_name": "Sonal Gupta",
        "role": "student",
        "hashed_password": hashlib.sha256("student123".encode()).hexdigest(),
    },
    "namyaajain29@gmail.com": {
        "email": "namyaajain29@gmail.com",
        "full_name": "Namya Jain",
        "role": "student",
        "hashed_password": hashlib.sha256("student123".encode()).hexdigest(),
    },
    "student@greenfield.edu": {
        "email": "student@greenfield.edu",
        "full_name": "Sonal Gupta",
        "role": "student",
        "hashed_password": hashlib.sha256("student123".encode()).hexdigest(),
    },
    "admin@greenfield.edu": {
        "email": "admin@greenfield.edu",
        "full_name": "Dr. Sarah Jenkins",
        "role": "admin",
        "hashed_password": hashlib.sha256("admin123".encode()).hexdigest(),
    },
}


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str.encode())


def create_jwt_token(payload: dict) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode()
    payload_claim = payload.copy()
    payload_claim["exp"] = int(time.time()) + TOKEN_TTL_SECONDS
    payload_json = json.dumps(payload_claim, separators=(",", ":")).encode()

    token_part = f"{_b64_encode(header_json)}.{_b64_encode(payload_json)}"
    signature = hmac.new(SECRET_KEY.encode(), token_part.encode(), hashlib.sha256).digest()
    return f"{token_part}.{_b64_encode(signature)}"


def decode_jwt_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        token_part = f"{parts[0]}.{parts[1]}"
        expected_sig = _b64_encode(hmac.new(SECRET_KEY.encode(), token_part.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(parts[2], expected_sig):
            raise ValueError("Invalid signature")

        payload_bytes = _b64_decode(parts[1])
        payload = json.loads(payload_bytes.decode())

        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if not credentials or not credentials.credentials:
        # Fallback for public demo access if token not provided
        return {
            "email": "guest@greenfield.edu",
            "full_name": "Guest Student",
            "role": "student",
            "is_guest": True,
        }
    token = credentials.credentials
    payload = decode_jwt_token(token)
    email = payload.get("sub")
    if not email or email not in USERS_DB:
        # If user registered dynamically
        return {
            "email": email or "user@greenfield.edu",
            "full_name": payload.get("name", "Registered User"),
            "role": payload.get("role", "student"),
            "is_guest": False,
        }
    user = USERS_DB[email].copy()
    user.pop("hashed_password", None)
    user["is_guest"] = False
    return user


def require_role(required_role: str):
    def _role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires '{required_role}' role.",
            )
        return user
    return _role_checker


@auth_router.post("/login")
def login(payload: dict):
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = USERS_DB.get(email)
    hashed_input = hashlib.sha256(password.encode()).hexdigest()

    if not user or user["hashed_password"] != hashed_input:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_jwt_token({"sub": email, "name": user["full_name"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


@auth_router.post("/register")
def register(payload: dict):
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    full_name = payload.get("full_name", "").strip() or email.split("@")[0].capitalize()
    role = payload.get("role", "student")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    if email in USERS_DB:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    USERS_DB[email] = {
        "email": email,
        "full_name": full_name,
        "role": role,
        "hashed_password": hashed_password,
    }

    token = create_jwt_token({"sub": email, "name": full_name, "role": role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": email, "full_name": full_name, "role": role},
    }


@auth_router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
