import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_to_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def expires_in_hours(hours: int = 24) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)