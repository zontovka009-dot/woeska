import hashlib, hmac, secrets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, AccountSession

AVATARS = {"violet", "cyan", "pink", "blue", "green", "orange", "ghost", "fox"}

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return f"pbkdf2$180000${salt.hex()}${dk.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt_hex, digest = stored.split("$", 3)
        got = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(got, digest)
    except Exception:
        return False

def new_token() -> str:
    return secrets.token_urlsafe(48)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def user_from_token(db: AsyncSession, token: str | None):
    if not token: return None
    row = await db.scalar(select(AccountSession).where(AccountSession.token_hash == token_hash(token)))
    if not row: return None
    return await db.get(User, row.user_id)

def user_payload(u: User):
    return {"id": u.id, "public_id": u.public_id, "nickname": u.nickname, "avatar_key": u.avatar_key, "avatar_url": u.avatar_url}
