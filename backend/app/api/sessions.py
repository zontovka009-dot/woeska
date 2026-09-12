from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.database import get_db
from app.models import Session, User, Membership, Message
from app.services.videos import resolve_video
import secrets
router=APIRouter(prefix="/api/sessions")

def uid(payload):
    if not payload.get("user_id"): raise HTTPException(401,"user_id required")
    return int(payload["user_id"])

@router.get("")
async def list_sessions(user_id:int, db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(Session).join(Membership, Membership.session_id==Session.id).where(Membership.user_id==user_id).order_by(Session.updated_at.desc()))).scalars().all()
    return [{"id":s.id,"title":s.title,"invite_code":s.invite_code,"provider":s.provider,"video_title":s.video_title,"playing":s.playing,"position":s.position} for s in rows[:10]]

@router.post("")
async def create(payload:dict,db:AsyncSession=Depends(get_db)):
    user=uid(payload); s=Session(title=payload.get("title") or "Новая комната",invite_code=secrets.token_urlsafe(6),owner_id=user); db.add(s); await db.flush(); db.add(Membership(session_id=s.id,user_id=user,role="owner")); await db.commit(); return {"id":s.id,"invite_code":s.invite_code}

@router.get("/{sid}")
async def detail(sid:int,user_id:int,db:AsyncSession=Depends(get_db)):
    s=await db.get(Session,sid); m=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==user_id));
    if not s or not m: raise HTTPException(404,"Room not found")
    members=(await db.execute(select(Membership,User).join(User,User.id==Membership.user_id).where(Membership.session_id==sid))).all()
    return {"id":s.id,"title":s.title,"invite_code":s.invite_code,"owner_id":s.owner_id,"provider":s.provider,"video_id":s.video_id,"video_url":s.video_url,"video_title":s.video_title,"playing":s.playing,"position":s.position,"playback_version":s.playback_version,"members":[{"id":u.id,"username":u.username,"name":u.first_name,"role":mm.role,"avatar_url":u.avatar_url} for mm,u in members]}

@router.post("/{sid}/join")
async def join(sid:int,payload:dict,db:AsyncSession=Depends(get_db)):
    s=await db.scalar(select(Session).where(Session.id==sid,Session.invite_code==payload.get("invite_code")))
    if not s: raise HTTPException(404,"Invalid invite")
    if not await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==uid(payload))): db.add(Membership(session_id=sid,user_id=uid(payload)))
    await db.commit(); return {"ok":True}

@router.post("/{sid}/leave")
async def leave(sid:int,payload:dict,db:AsyncSession=Depends(get_db)):
    await db.execute(delete(Membership).where(Membership.session_id==sid,Membership.user_id==uid(payload))); await db.commit(); return {"ok":True}

@router.post("/{sid}/video")
async def set_video(sid:int,payload:dict,db:AsyncSession=Depends(get_db)):
    s=await db.get(Session,sid); m=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==uid(payload)))
    if not s or not m or m.role not in ("owner","admin"): raise HTTPException(403,"No permission")
    try:r=resolve_video(payload["url"])
    except ValueError as e: raise HTTPException(400,str(e))
    s.provider=r["provider"]; s.video_id=r["video_id"]; s.video_url=r["url"]; s.video_title=payload.get("title") or r["video_id"]; s.position=0; s.playing=False; s.playback_version+=1; s.updated_at=datetime.utcnow(); await db.commit(); return r

@router.post("/{sid}/kick/{target}")
async def kick(sid:int,target:int,payload:dict,db:AsyncSession=Depends(get_db)):
    actor=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==uid(payload)))
    if not actor or actor.role not in ("owner","admin"): raise HTTPException(403,"No permission")
    await db.execute(delete(Membership).where(Membership.session_id==sid,Membership.user_id==target)); await db.commit(); return {"ok":True}

@router.post("/{sid}/transfer/{target}")
async def transfer(sid:int,target:int,payload:dict,db:AsyncSession=Depends(get_db)):
    actor=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==uid(payload),Membership.role=="owner")); targetm=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==target))
    if not actor or not targetm: raise HTTPException(403,"Owner only")
    actor.role="admin"; targetm.role="owner"; s=await db.get(Session,sid); s.owner_id=target; await db.commit(); return {"ok":True}

@router.get("/{sid}/messages")
async def messages(sid:int,user_id:int,db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(Message).where(Message.session_id==sid).order_by(Message.created_at.desc()).limit(100))).scalars().all(); rows=list(reversed(rows)); return [{"id":x.id,"user_id":x.user_id,"author_name":x.author_name,"text":x.text,"created_at":x.created_at.isoformat()} for x in rows]

@router.post("/{sid}/messages")
async def send_message(sid:int,payload:dict,db:AsyncSession=Depends(get_db)):
    u=await db.get(User,uid(payload)); m=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==u.id));
    if not m: raise HTTPException(403,"Not a member")
    msg=Message(session_id=sid,user_id=u.id,author_name=u.first_name,text=payload.get("text","")[:2000]); db.add(msg); await db.commit(); await db.refresh(msg); return {"id":msg.id,"user_id":u.id,"author_name":u.first_name,"text":msg.text,"created_at":msg.created_at.isoformat()}
