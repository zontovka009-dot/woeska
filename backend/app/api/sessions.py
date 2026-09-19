import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models import Session, User, Membership, Message
from app.service.auth import user_from_token
from app.service.videos import resolve_video
router=APIRouter(prefix="/api/sessions")

async def current(db, authorization):
    u=await user_from_token(db, auth_header(authorization))
    if not u: raise HTTPException(401,"Требуется вход")
    return u

def auth_header(authorization): return authorization[7:] if authorization and authorization.startswith("Bearer ") else None

async def member(db,sid,uid): return await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==uid))

@router.get("")
async def list_sessions(authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization)
    rows=(await db.execute(select(Session).join(Membership,Membership.session_id==Session.id).where(Membership.user_id==u.id).order_by(Session.updated_at.desc()))).scalars().all()
    return [{"id":s.id,"title":s.title,"invite_code":s.invite_code,"provider":s.provider,"video_title":s.video_title,"playing":s.playing,"position":s.position} for s in rows[:10]]

@router.post("")
async def create(payload:dict,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization)
    s=Session(title=(payload.get("title") or "Комната Wathis")[:160],invite_code=secrets.token_urlsafe(6),owner_id=u.id); db.add(s); await db.flush(); db.add(Membership(session_id=s.id,user_id=u.id,role="owner")); await db.commit(); return {"id":s.id,"invite_code":s.invite_code}

@router.get("/by-code/{code}")
async def by_code(code:str,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    await current(db,authorization); s=await db.scalar(select(Session).where(Session.invite_code==code))
    if not s: raise HTTPException(404,"Комната не найдена")
    return {"id":s.id,"title":s.title,"invite_code":s.invite_code,"provider":s.provider,"video_title":s.video_title}

@router.get("/{sid}")
async def detail(sid:int,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); s=await db.get(Session,sid); m=await member(db,sid,u.id)
    if not s or not m: raise HTTPException(404,"Комната не найдена")
    members=(await db.execute(select(Membership,User).join(User,User.id==Membership.user_id).where(Membership.session_id==sid))).all()
    return {"id":s.id,"title":s.title,"invite_code":s.invite_code,"owner_id":s.owner_id,"provider":s.provider,"video_id":s.video_id,"video_url":s.video_url,"video_title":s.video_title,"playing":s.playing,"position":s.position,"playback_version":s.playback_version,"members":[{"id":u2.id,"public_id":u2.public_id,"nickname":u2.nickname,"role":mm.role,"avatar_key":u2.avatar_key,"avatar_url":u2.avatar_url} for mm,u2 in members]}

@router.post("/{sid}/join")
async def join(sid:int,payload:dict,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); s=await db.scalar(select(Session).where(Session.id==sid,Session.invite_code==payload.get("invite_code")))
    if not s: raise HTTPException(404,"Неверный код приглашения")
    if not await member(db,sid,u.id): db.add(Membership(session_id=sid,user_id=u.id,role="member"))
    await db.commit(); return {"ok":True}

@router.post("/{sid}/leave")
async def leave(sid:int,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); m=await member(db,sid,u.id)
    if not m: return {"ok":True}
    if m.role=="owner": raise HTTPException(400,"Владелец должен сначала передать комнату")
    await db.delete(m); await db.commit(); return {"ok":True}

@router.post("/{sid}/video")
async def set_video(sid:int,payload:dict,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); s=await db.get(Session,sid); m=await member(db,sid,u.id)
    if not s or not m or m.role not in ("owner","admin"): raise HTTPException(403,"Нет прав")
    try:r=resolve_video(payload["url"])
    except ValueError as e: raise HTTPException(400,str(e))
    s.provider=r["provider"]; s.video_id=r["video_id"]; s.video_url=r["url"]; s.video_title=payload.get("title") or r["video_id"]; s.position=0; s.playing=False; s.playback_version+=1; s.updated_at=datetime.utcnow(); await db.commit(); return r

@router.post("/{sid}/kick/{target}")
async def kick(sid:int,target:int,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); actor=await member(db,sid,u.id); tm=await member(db,sid,target)
    if not actor or actor.role not in ("owner","admin") or not tm or tm.role=="owner": raise HTTPException(403,"Нет прав")
    if actor.role=="admin" and tm.role=="admin": raise HTTPException(403,"Администратор не может исключить администратора")
    await db.delete(tm); await db.commit(); return {"ok":True}

@router.post("/{sid}/role/{target}")
async def role(sid:int,target:int,payload:dict,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); actor=await member(db,sid,u.id); tm=await member(db,sid,target)
    if not actor or actor.role!="owner" or not tm: raise HTTPException(403,"Только владелец")
    value=payload.get("role")
    if value not in ("member","admin"): raise HTTPException(400,"Некорректная роль")
    tm.role=value; await db.commit(); return {"ok":True}

@router.post("/{sid}/transfer/{target}")
async def transfer(sid:int,target:int,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); actor=await member(db,sid,u.id); targetm=await member(db,sid,target)
    if not actor or actor.role!="owner" or not targetm: raise HTTPException(403,"Только владелец")
    actor.role="admin"; targetm.role="owner"; s=await db.get(Session,sid); s.owner_id=target; await db.commit(); return {"ok":True}

@router.get("/{sid}/messages")
async def messages(sid:int,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization);
    if not await member(db,sid,u.id): raise HTTPException(403,"Нет доступа")
    rows=(await db.execute(select(Message).where(Message.session_id==sid).order_by(Message.created_at.desc()).limit(100))).scalars().all(); rows=list(reversed(rows))
    return [{"id":x.id,"user_id":x.user_id,"author_name":x.author_name,"text":x.text,"created_at":x.created_at.isoformat()} for x in rows]

@router.post("/{sid}/messages")
async def send_message(sid:int,payload:dict,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization)
    if not await member(db,sid,u.id): raise HTTPException(403,"Нет доступа")
    text=(payload.get("text") or "").strip()[:2000]
    if not text: raise HTTPException(400,"Пустое сообщение")
    msg=Message(session_id=sid,user_id=u.id,author_name=u.nickname,text=text); db.add(msg); await db.commit(); await db.refresh(msg)
    return {"id":msg.id,"user_id":u.id,"author_name":u.nickname,"text":msg.text,"created_at":msg.created_at.isoformat()}
