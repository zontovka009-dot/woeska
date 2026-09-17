from fastapi import APIRouter, HTTPException
from app.service.videos import resolve_video,youtube_search,vk_search
router=APIRouter(prefix="/api/videos")
@router.get("/resolve")
async def resolve(url:str):
    try:return resolve_video(url)
    except ValueError as e:raise HTTPException(400,str(e))
@router.get("/search/youtube")
async def yt(q:str):return await youtube_search(q)
@router.get("/search/vk")
async def vk(q:str):return await vk_search(q)
