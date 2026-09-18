import asyncio, json
from datetime import datetime
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.database.database import SessionLocal
from app.models import Session, Membership, User, Message
from app.service.auth import user_from_token

connections=defaultdict(set)

async def broadcast(sid,data,skip=None):
    raw=json.dumps(data,ensure_ascii=False)
    for client in list(connections[sid]):
        if client is skip: continue
        try: await client.send_text(raw)
        except Exception: connections[sid].discard(client)

async def room_socket(ws:WebSocket,sid:int,token:str|None):
    await ws.accept()
    async with SessionLocal() as db:
        user=await user_from_token(db,token)
        membership=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==getattr(user,'id',-1))) if user else None
        room=await db.get(Session,sid)
        if not room or not membership:
            await ws.send_text(json.dumps({"type":"error","message":"Нет доступа к комнате"})); await ws.close(code=4403); return
    connections[sid].add(ws)
    await broadcast(sid,{"type":"presence","event":"join","user_id":user.id},skip=ws)
    try:
        while True:
            data=json.loads(await ws.receive_text())
            typ=data.get("type")
            async with SessionLocal() as db:
                room=await db.get(Session,sid)
                if not room: continue
                if typ in ("play","pause","seek"):
                    m=await db.scalar(select(Membership).where(Membership.session_id==sid,Membership.user_id==user.id))
                    if not m: continue
                    # Owner/admin controls the room timeline; a member may request a sync.
                    if m.role not in ("owner","admin") and typ != "seek": continue
                    if typ=="seek": room.position=max(0,float(data.get("position",0))); room.updated_at=datetime.utcnow()
                    elif typ=="play": room.position=max(0,float(data.get("position",room.position))); room.playing=True; room.updated_at=datetime.utcnow()
                    else: room.position=max(0,float(data.get("position",room.position))); room.playing=False; room.updated_at=datetime.utcnow()
                    room.playback_version+=1; await db.commit()
                    await broadcast(sid,{"type":"sync","action":typ,"position":room.position,"playing":room.playing,"version":room.playback_version,"user_id":user.id})
                elif typ=="chat":
                    text=(data.get("text") or "").strip()[:2000]
                    if not text: continue
                    msg=Message(session_id=sid,user_id=user.id,author_name=user.nickname,text=text); db.add(msg); await db.commit(); await db.refresh(msg)
                    await broadcast(sid,{"type":"chat","message":{"id":msg.id,"user_id":user.id,"author_name":user.nickname,"text":text,"created_at":msg.created_at.isoformat()}})
                elif typ=="ping":
                    await ws.send_text(json.dumps({"type":"pong"}))
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        connections[sid].discard(ws)
        await broadcast(sid,{"type":"presence","event":"leave","user_id":user.id},skip=ws)
