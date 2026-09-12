import hashlib, hmac, time
from urllib.parse import parse_qsl
from app.config.settings import settings

def validate_init_data(init_data: str) -> dict:
    if not init_data:
        raise ValueError("Missing Telegram initData")
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received = data.pop("hash", None)
    if not received:
        raise ValueError("Missing initData hash")
    auth_date = int(data.get("auth_date", "0"))
    if abs(time.time() - auth_date) > 86400:
        raise ValueError("Expired initData")
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise ValueError("Invalid initData")
    import json
    return json.loads(data["user"])
