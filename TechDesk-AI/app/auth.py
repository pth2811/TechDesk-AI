import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Response, status

from app.database.database import (
    delete_session,
    get_user,
    get_user_by_session,
    save_session
)

COOKIE_NAME = "techdesk_session"
SESSION_HOURS = 24

SPECIALIST_ACCESS_CODE = os.getenv("SPECIALIST_ACCESS_CODE", "TECH2026").strip()
ADMIN_ACCESS_CODE = os.getenv("ADMIN_ACCESS_CODE", "ADMIN2026").strip()


# =========================================================
# PASSWORD HASHING (SECURE PBKDF2-HMAC-SHA256)
# =========================================================

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()
    return f"pbkdf2_sha256${salt}${key}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against the stored PBKDF2 hash."""
    if not hashed or "$" not in hashed:
        return False

    parts = hashed.split("$")
    if len(parts) != 3 or parts[0] != "pbkdf2_sha256":
        return False

    _, salt, stored_key = parts
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return hmac.compare_digest(stored_key, key)


# =========================================================
# SESSION MANAGEMENT
# =========================================================

def create_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_login_session(response: Response, user_id: int):
    token = secrets.token_urlsafe(32)
    token_hash = create_token_hash(token)
    expires_at = (datetime.utcnow() + timedelta(hours=SESSION_HOURS)).strftime("%Y-%m-%d %H:%M:%S")

    save_session(token_hash, user_id, expires_at)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return token


def logout_session(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        delete_session(create_token_hash(token))
    response.delete_cookie(COOKIE_NAME)


def get_current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    user = get_user_by_session(create_token_hash(token), now)
    return user


def require_roles(*allowed_roles):
    def dependency(request: Request):
        user = get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please log in."
            )

        user_role = str(user.get("role", "employee")).lower()
        allowed = [r.lower() for r in allowed_roles]

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission for this portal."
            )

        return user

    return dependency


def get_role_dashboard(role: str) -> str:
    role = (role or "employee").lower()
    if role == "admin":
        return "/admin-dashboard"
    elif role == "specialist":
        return "/specialist-dashboard"
    return "/employee-dashboard"
