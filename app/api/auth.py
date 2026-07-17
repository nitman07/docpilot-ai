from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.core.db import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=201)
async def register(req: RegisterRequest) -> dict:
    existing = await get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    hashed = hash_password(req.password)
    user = await create_user(req.email, hashed)
    return {"id": str(user["id"]), "email": user["email"], "role": user["role"]}


@router.post("/login")
async def login(req: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user_id = str(user["id"])
    return TokenResponse(
        access_token=create_access_token(user_id, user["email"], user["role"]),
        refresh_token=create_refresh_token(user_id, user["email"], user["role"]),
    )


@router.post("/refresh")
async def refresh(req: RefreshRequest) -> TokenResponse:
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload["sub"]
    email = payload["email"]
    role = payload["role"]
    return TokenResponse(
        access_token=create_access_token(user_id, email, role),
        refresh_token=create_refresh_token(user_id, email, role),
    )


@router.get("/me")
async def me(user: dict = Depends(get_current_user)) -> dict:
    return {"id": str(user["id"]), "email": user["email"], "role": user["role"]}
