from datetime import datetime
from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=200)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TodoCreateIn(BaseModel):
    task: str = Field(min_length=1, max_length=300)


class TodoStatusIn(BaseModel):
    task: str
    status: bool


class TodoDeleteIn(BaseModel):
    task: str


class TodoOut(BaseModel):
    task: str
    status: bool
    created_at: datetime