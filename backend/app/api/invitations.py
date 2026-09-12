from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models import Invitation, Session, User
router=APIRouter(prefix="/api/invitations")
@router.get("")
async def list_invites(user_id:int,db:AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(Invitation,Session,User).join(Session,Session.id==Invitation.session_id).join(User,User.id==Invitation.sender_id).where(Invitation.recipient_id==user_id,Invitation.status=="pending"))).all(); return [{"id":i.id,"session_id":s.id,"session_title":s.title,"sender":u.first_name,"invite_code":s.invite_code} for i,s,u in rows]
@router.post("/{session_id}/{user_id}")
async def invite(session_id:int,user_id:int,payload:dict,db:AsyncSession=Depends(get_db)):
    db.add(Invitation(session_id=session_id,sender_id=payload["sender_id"],recipient_id=user_id)); await db.commit(); return {"ok":True}
