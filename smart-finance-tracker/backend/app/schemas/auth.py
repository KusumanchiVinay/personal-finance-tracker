"""app/schemas/auth.py — Pydantic request/response models"""
from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterRequest(BaseModel):
    email:      EmailStr
    password:   str
    full_name:  str
    currency:   str = "USD"

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a digit")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          "UserOut"


class UserOut(BaseModel):
    id:             str
    email:          str
    full_name:      str
    currency:       str
    monthly_income: float

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    refresh_token: str
