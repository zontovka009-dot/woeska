from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.database.database import init_db
from app.api import auth,sessions,friends,invitations,videos
from app.websocket.rooms import room_socket
app=FastAPI(title="Wathis API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(auth.router); app.include_router(sessions.router); app.include_router(friends.router); app.include_router(invitations.router); app.include_router(videos.router)
@app.on_event("startup")
async def startup(): await init_db()
@app.get("/api/health")
async def health(): return {"ok":True,"service":"wathis-backend"}
@app.websocket("/ws/rooms/{sid}")
async def ws(sid:int, websocket:WebSocket): await room_socket(websocket,sid)
