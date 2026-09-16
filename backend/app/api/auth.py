import re, secrets
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models import User, AccountSession
from app.service.auth import hash_password, verify_password, new_token, token_hash, user_from_token, user_payload, AVATARS

router=APIRouter(prefix="/api/auth")

def valid_nick(s):
    return bool(re.fullmatch(r"[A-Za-zА-Яа-яЁё0-9_]{3,20}", s or ""))

def auth_header(authorization: str | None):
    return authorization[7:] if authorization and authorization.startswith("Bearer ") else None

async def require_user(db: AsyncSession, authorization: str | None):
    u=await user_from_token(db, auth_header(authorization))
    if not u: raise HTTPException(401,"Сессия истекла")
    return u

async def make_public_id(db):
    for _ in range(100):
        value=f"{secrets.randbelow(100_000_000):08d}"
        if not await db.scalar(select(User).where(User.public_id==value)): return value
    raise HTTPException(500,"Не удалось создать ID")

@router.post("/register")
async def register(payload:dict, db:AsyncSession=Depends(get_db)):
    nickname=(payload.get("nickname") or "").strip()
    password=payload.get("password") or ""
    avatar=payload.get("avatar_key") or "violet"
    if not valid_nick(nickname): raise HTTPException(400,"Ник: 3–20 символов, буквы, цифры или _")
    if len(password)<6 or len(password)>72: raise HTTPException(400,"Пароль должен быть от 6 до 72 символов")
    if avatar not in AVATARS: avatar="violet"
    if await db.scalar(select(User).where(User.nickname.ilike(nickname))): raise HTTPException(409,"Этот ник уже занят")
    u=User(public_id=await make_public_id(db),nickname=nickname,password_hash=hash_password(password),avatar_key=avatar,first_name=nickname)
    db.add(u); await db.flush()
    # Legacy BotHost databases had a non-null telegram_id column. Keep it detached from the Telegram profile.
    if u.telegram_id is None: u.telegram_id = -u.id
    token=new_token(); db.add(AccountSession(user_id=u.id,token_hash=token_hash(token)))
    await db.commit(); await db.refresh(u)
    return {"token":token,"user":user_payload(u)}

@router.post("/login")
async def login(payload:dict, db:AsyncSession=Depends(get_db)):
    nickname=(payload.get("nickname") or "").strip()
    u=await db.scalar(select(User).where(User.nickname.ilike(nickname)))
    if not u or not u.password_hash or not verify_password(payload.get("password") or "",u.password_hash): raise HTTPException(401,"Неверный ник или пароль")
    token=new_token(); db.add(AccountSession(user_id=u.id,token_hash=token_hash(token))); await db.commit()
    return {"token":token,"user":user_payload(u)}

@router.get("/me")
async def me(authorization: str|None=Header(default=None), db:AsyncSession=Depends(get_db)):
    return user_payload(await require_user(db,authorization))

@router.patch("/profile")
async def profile(payload:dict, authorization: str|None=Header(default=None), db:AsyncSession=Depends(get_db)):
    u=await require_user(db,authorization)
    nickname=(payload.get("nickname") or u.nickname).strip()
    avatar=payload.get("avatar_key") or u.avatar_key
    if not valid_nick(nickname): raise HTTPException(400,"Ник: 3–20 символов, буквы, цифры или _")
    other=await db.scalar(select(User).where(User.nickname.ilike(nickname),User.id!=u.id))
    if other: raise HTTPException(409,"Этот ник уже занят")
    if avatar not in AVATARS: avatar=u.avatar_key
    u.nickname=nickname; u.first_name=nickname; u.avatar_key=avatar
    await db.commit(); await db.refresh(u)
    return user_payload(u)

@router.post("/logout")
async def logout(authorization: str|None=Header(default=None), db:AsyncSession=Depends(get_db)):
    token=auth_header(authorization)
    if token:
        row=await db.scalar(select(AccountSession).where(AccountSession.token_hash==token_hash(token)))
        if row: await db.delete(row); await db.commit()
    return {"ok":True}
