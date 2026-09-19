from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models import User, Friendship
from app.service.auth import user_from_token
router=APIRouter(prefix="/api/friends")

async def current(db,auth):
    token=auth[7:] if auth and auth.startswith("Bearer ") else None; u=await user_from_token(db,token)
    if not u: raise HTTPException(401,"Требуется вход")
    return u

def pack(u,status="accepted"): return {"id":u.id,"public_id":u.public_id,"nickname":u.nickname,"avatar_key":u.avatar_key,"avatar_url":u.avatar_url,"status":status}

@router.get("")
async def friends(authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization)
    rows=(await db.execute(select(Friendship,User).join(User,User.id==Friendship.friend_id).where(Friendship.user_id==u.id,Friendship.status=="accepted"))).all()
    return [pack(x,status=s.status) for s,x in rows]

@router.get("/requests")
async def requests(authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization)
    rows=(await db.execute(select(Friendship,User).join(User,User.id==Friendship.user_id).where(Friendship.friend_id==u.id,Friendship.status=="pending"))).all()
    return [pack(x,"pending") for s,x in rows]

@router.get("/search")
async def search(q:str,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); q=q.strip().lstrip("@")
    rows=(await db.execute(select(User).where(User.id!=u.id,or_(User.public_id==q,User.nickname.ilike(f"%{q}%"))).limit(20))).scalars().all()
    return [pack(x,"search") for x in rows]

@router.post("/request/{public_id}")
async def add(public_id:str,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); target=await db.scalar(select(User).where(User.public_id==public_id))
    if not target or target.id==u.id: raise HTTPException(404,"Пользователь не найден")
    exists=await db.scalar(select(Friendship).where(Friendship.user_id==u.id,Friendship.friend_id==target.id))
    if exists: raise HTTPException(409,"Заявка уже существует")
    reverse=await db.scalar(select(Friendship).where(Friendship.user_id==target.id,Friendship.friend_id==u.id))
    if reverse and reverse.status=="pending":
        reverse.status="accepted"; db.add(Friendship(user_id=u.id,friend_id=target.id,status="accepted"))
    else: db.add(Friendship(user_id=u.id,friend_id=target.id,status="pending"))
    await db.commit(); return {"ok":True}

@router.post("/requests/{public_id}/accept")
async def accept(public_id:str,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); target=await db.scalar(select(User).where(User.public_id==public_id)); req=await db.scalar(select(Friendship).where(Friendship.user_id==getattr(target,'id',-1),Friendship.friend_id==u.id,Friendship.status=="pending"))
    if not target or not req: raise HTTPException(404,"Заявка не найдена")
    req.status="accepted"; db.add(Friendship(user_id=u.id,friend_id=target.id,status="accepted")); await db.commit(); return {"ok":True}

@router.delete("/{public_id}")
async def remove(public_id:str,authorization:str|None=Header(default=None),db:AsyncSession=Depends(get_db)):
    u=await current(db,authorization); target=await db.scalar(select(User).where(User.public_id==public_id))
    if target:
        await db.execute(Friendship.__table__.delete().where(or_(and_(Friendship.user_id==u.id,Friendship.friend_id==target.id),and_(Friendship.user_id==target.id,Friendship.friend_id==u.id))))
        await db.commit()
    return {"ok":True}
