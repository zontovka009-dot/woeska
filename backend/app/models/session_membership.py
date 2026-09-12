from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base
class Membership(Base):
    __tablename__="memberships"
    id: Mapped[int]=mapped_column(primary_key=True)
    session_id: Mapped[int]=mapped_column(ForeignKey("sessions.id"))
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    role: Mapped[str]=mapped_column(String(16),default="member")
    __table_args__=(UniqueConstraint("session_id","user_id"),)
