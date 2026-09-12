from datetime import datetime
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), default="Новая комната")
    invite_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str | None] = mapped_column(String(32))
    video_id: Mapped[str | None] = mapped_column(String(256))
    video_url: Mapped[str | None] = mapped_column(String(2000))
    video_title: Mapped[str | None] = mapped_column(String(300))
    playing: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[float] = mapped_column(Float, default=0)
    playback_version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=True)
