from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models import User
from app.service.telegram import validate_init_data
router=APIRouter(prefix="/api/auth")

def current_user(init_data: str, db: AsyncSession):
    return None

@router.post("/telegram")
async def auth(payload: dict, db: AsyncSession=Depends(get_db)):
    try: u=validate_init_data(payload.get("init_data", ""))
    except ValueError as e: raise HTTPException(401,str(e))
    user=await db.scalar(select(User).where(User.telegram_id==u["id"]))
    if not user:
        user=User(telegram_id=u["id"],username=u.get("username"),first_name=u.get("first_name","User"),last_name=u.get("last_name"),avatar_url=u.get("photo_url")); db.add(user)
    else:
        user.username=u.get("username"); user.first_name=u.get("first_name","User"); user.last_name=u.get("last_name"); user.avatar_url=u.get("photo_url")
    await db.commit(); await db.refresh(user)
    return {"id":user.id,"telegram_id":user.telegram_id,"username":user.username,"first_name":user.first_name,"last_name":user.last_name,"avatar_url":user.avatar_url}
