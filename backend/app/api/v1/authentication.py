from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.exc import IntegrityError

from app.api.deps import DB
from app.config import get_settings
from app.services.user_repository import UserRepository

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Request schemas ────────────────────────────────────────────────────────────

class RegData(BaseModel):
    fname: str
    lname: str
    email: EmailStr
    password: str = Field(
        min_length=12,
        description="Must be at least 12 characters with uppercase, lowercase, digit, and symbol"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce strong password requirements to prevent dictionary attacks.

        Requirements:
        - Minimum 12 characters (strong entropy)
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one digit (0-9)
        - At least one special character (!@#$%^&*)

        bcrypt also has a hard 72-byte limit on UTF-8 encoded passwords.
        Two different passwords that share the same first 72 bytes would
        both authenticate successfully. We reject longer passwords early
        to avoid silent data loss and auth ambiguity.
        """
        if len(v) < 12:
            raise ValueError(
                "Password must be at least 12 characters long. "
                "Shorter passwords are vulnerable to dictionary attacks."
            )

        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes (UTF-8 encoded)")

        # Check for uppercase letters
        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter (A-Z)"
            )

        # Check for lowercase letters
        if not any(c.islower() for c in v):
            raise ValueError(
                "Password must contain at least one lowercase letter (a-z)"
            )

        # Check for digits
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit (0-9)")

        # Check for special characters
        special_chars = "!@#$%^&*()-_=+[]{}|;:',.<>?/~`"
        if not any(c in special_chars for c in v):
            raise ValueError(
                f"Password must contain at least one special character from: {special_chars}"
            )

        return v


class LoginData(BaseModel):
    email: EmailStr
    password: str


# ── Response schemas ───────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    token: str
    email: EmailStr


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=MessageResponse)
async def signup(data: RegData, db: DB) -> MessageResponse:
    repo = UserRepository(db)
    if await repo.user_exists(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        await repo.create_user(
            email=data.email,
            fname=data.fname,
            lname=data.lname,
            hashed_password=pwd.hash(data.password),
        )
    except IntegrityError:
        # Guard against check-then-insert race: two concurrent requests can
        # both pass user_exists() above, but the DB unique constraint on email
        # will reject the second insert.  Return 400 instead of leaking a 500.
        raise HTTPException(status_code=400, detail="Email already registered")
    return MessageResponse(message="Account created successfully")


@router.post("/signin", response_model=TokenResponse)
async def signin(data: LoginData, db: DB) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_user_by_email(data.email)
    if not user or not pwd.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    exp = datetime.now(UTC) + timedelta(hours=24)
    settings = get_settings()
    token = jwt.encode(
        {"email": data.email, "exp": exp}, settings.secret_key, algorithm="HS256"
    )
    return TokenResponse(token=token, email=data.email)


