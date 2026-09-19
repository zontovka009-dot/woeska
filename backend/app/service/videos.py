from urllib.parse import urlparse, parse_qs
import re, httpx
from app.config.settings import settings

def resolve_video(url: str) -> dict:
    p = urlparse(url)
    host = p.netloc.lower()
    if "youtu.be" in host:
        vid = p.path.strip("/")
        return {"provider":"youtube","video_id":vid,"url":url,"embed_url":f"https://www.youtube.com/embed/{vid}?enablejsapi=1&playsinline=1"}
    if "youtube.com" in host:
        vid = parse_qs(p.query).get("v", [None])[0]
        m = re.search(r"/shorts/([^/?]+)", p.path)
        vid = vid or (m.group(1) if m else None)
        if vid: return {"provider":"youtube","video_id":vid,"url":url,"embed_url":f"https://www.youtube.com/embed/{vid}?enablejsapi=1&playsinline=1"}
    if "vk.com" in host or "vkvideo.ru" in host:
        m = re.search(r"video[- ]?(\d+)[_/](\d+)", url)
        if m:
            oid, vid = m.groups()
            return {"provider":"vk","video_id":f"{oid}_{vid}","url":url,"embed_url":f"https://vk.com/video_ext.php?oid={oid}&id={vid}&js_api=1"}
    if "drive.google.com" in host:
        m = re.search(r"/file/d/([^/]+)", p.path)
        if m:
            vid=m.group(1)
            return {"provider":"drive","video_id":vid,"url":url,"embed_url":f"https://drive.google.com/file/d/{vid}/preview"}
    raise ValueError("Unsupported or unrecognized video URL")

async def youtube_search(q: str):
    if not settings.youtube_api_key: return []
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get("https://www.googleapis.com/youtube/v3/search", params={"part":"snippet","q":q,"type":"video","maxResults":10,"key":settings.youtube_api_key})
        r.raise_for_status()
        return [{"provider":"youtube","video_id":x["id"]["videoId"],"title":x["snippet"]["title"],"thumbnail":x["snippet"]["thumbnails"]["high"]["url"]} for x in r.json().get("items",[])]

async def vk_search(q: str):
    if not settings.vk_service_token: return []
    async with httpx.AsyncClient(timeout=10) as c:
        r=await c.get("https://api.vk.com/method/video.search",params={"q":q,"count":10,"access_token":settings.vk_service_token,"v":"5.199"})
        data=r.json().get("response",{}).get("items",[])
        return [{"provider":"vk","video_id":f'{x.get("owner_id")}_{x.get("id")}',"title":x.get("title","VK Video"),"thumbnail":x.get("photo_320")} for x in data]
