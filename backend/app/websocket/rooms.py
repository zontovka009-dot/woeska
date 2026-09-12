import asyncio, json
from fastapi import WebSocket
from collections import defaultdict
connections=defaultdict(set)

async def room_socket(ws:WebSocket,sid:int):
    await ws.accept(); connections[sid].add(ws)
    try:
        while True:
            data=await ws.receive_text()
            for client in list(connections[sid]):
                if client is not ws:
                    try: await client.send_text(data)
                    except: connections[sid].discard(client)
    except Exception: pass
    finally: connections[sid].discard(ws)
