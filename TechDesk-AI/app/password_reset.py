import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.database.database import get_user_by_email, update_user_password
from app.auth import hash_password

router = APIRouter(prefix="/auth", tags=["Password Reset"])

RESET_TOKENS = {}  # token -> {"user_id": int, "email": str, "expires": datetime}

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    email = req.email.strip().lower()
    user = get_user_by_email(email)
    if not user:
        # Don't leak account existence
        return {"message": "If that email exists in our system, a password reset token has been generated."}

    token = secrets.token_urlsafe(32)
    RESET_TOKENS[token] = {
        "user_id": user["id"],
        "email": email,
        "expires": datetime.utcnow() + timedelta(minutes=30)
    }

    # In development/demo, print token to console for easy testing
    print("==================================================")
    print(f"[PASSWORD RESET TOKEN for {email}]:")
    print(f"Token: {token}")
    print(f"Reset Link: http://127.0.0.1:8001/password-reset.html?token={token}")
    print("==================================================")

    return {
        "message": "Password reset instructions have been dispatched.",
        "demo_token": token  # Included for smooth local testing
    }


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    record = RESET_TOKENS.get(req.token)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    if datetime.utcnow() > record["expires"]:
        del RESET_TOKENS[req.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters."
        )

    new_hash = hash_password(req.new_password)
    update_user_password(record["user_id"], new_hash)
    del RESET_TOKENS[req.token]

    return {"message": "Password has been successfully reset! You can now log in."}
