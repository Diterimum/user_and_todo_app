from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from db import get_db
from models.orm import User, Token
from models.schemas import RegisterIn, LoginIn, TokenOut
from security import (
    hash_password,
    verify_password,
    new_token,
    token_to_hash,
    expires_in_hours,
)

router = APIRouter(tags=["auth"])


def _get_user_by_username(db: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalars().first()


def _cleanup_expired_tokens(db: Session) -> None:
    now = datetime.now(timezone.utc)
    db.execute(delete(Token).where(Token.expires_at <= now))
    db.commit()


def _get_user_by_token(db: Session, authorization: Optional[str]) -> tuple[int, str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token>",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    th = token_to_hash(token)
    now = datetime.now(timezone.utc)

    stmt = (
        select(User.id, User.username)
        .join(Token, Token.user_id == User.id)
        .where(Token.token_hash == th, Token.expires_at > now)
    )
    row = db.execute(stmt).first()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return row[0], row[1]


@router.post("/auth/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if _get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    u = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(u)
    db.commit()
    db.refresh(u)

    return {"ok": True, "username": u.username, "created_at": u.created_at}


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    _cleanup_expired_tokens(db)

    u = _get_user_by_username(db, payload.username)
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Wrong username or password")

    token = new_token()
    th = token_to_hash(token)
    expires_at = expires_in_hours(24)

    t = Token(user_id=u.id, token_hash=th, expires_at=expires_at)
    db.add(t)
    db.commit()

    return TokenOut(access_token=token, expires_at=expires_at)


@router.post("/auth/logout")
def logout(Authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not Authorization or not Authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = Authorization.split(" ", 1)[1].strip()
    th = token_to_hash(token)

    res = db.execute(delete(Token).where(Token.token_hash == th))
    db.commit()

    if res.rowcount == 0:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"ok": True}


@router.get("/me")
def me(Authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    _, username = _get_user_by_token(db, Authorization)
    return {"username": username}


def get_user_by_token(Authorization: Optional[str], db: Session) -> tuple[int, str]:
    return _get_user_by_token(db, Authorization)