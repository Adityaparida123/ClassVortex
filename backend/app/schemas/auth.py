from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "teacher"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
