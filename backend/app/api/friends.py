from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models import User, Friendship
router=APIRouter(prefix="/api/friends")
@router.get("")
async def friends(user_id:int,db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(User).join(Friendship,Friendship.friend_id==User.id).where(Friendship.user_id==user_id))).scalars().all(); return [{"id":u.id,"username":u.username,"name":u.first_name,"avatar_url":u.avatar_url} for u in rows]
@router.post("/{username}")
async def add(username:str,user_id:int,db:AsyncSession=Depends(get_db)):
    target=await db.scalar(select(User).where(User.username==username.lstrip("@")))
    if not target or target.id==user_id: raise HTTPException(404,"User not found")
    for a,b in [(user_id,target.id),(target.id,user_id)]:
        if not await db.scalar(select(Friendship).where(Friendship.user_id==a,Friendship.friend_id==b)): db.add(Friendship(user_id=a,friend_id=b))
    await db.commit(); return {"ok":True}
