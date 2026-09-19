import secrets, string
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Session, User

def code(): return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(8))

async def is_member(db: AsyncSession, sid: int, uid: int):
    from app.models import Friendship
    # membership is represented by a small dynamic table created below
    from app.models.session_membership import Membership
    r=await db.scalar(select(Membership).where(Membership.session_id==sid, Membership.user_id==uid))
    return r
