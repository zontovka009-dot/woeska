from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    avatar_key: Mapped[str] = mapped_column(String(64), default="violet")
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), default="User")
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
