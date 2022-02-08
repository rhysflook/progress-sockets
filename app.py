import asyncio
import json
import websockets
import secrets

import os
import signal

JOIN = {}

async def send_messages(websocket, connected):

    async for message in websocket:
        event = json.loads(message)
        websockets.broadcast(connected, json.dumps(event))

async def start(websocket, token):
    connected = {websocket}
    print(token)
    JOIN[token] = connected
    print(JOIN)
    try:
        await send_messages(websocket, connected)
    finally:
        del JOIN[token]

async def join(websocket, token):
    print(JOIN)
    print(token)
    connected = JOIN[token]
    connected.add(websocket)
    try:
        await send_messages(websocket, connected)
    finally:
        connected.remove()

async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    port = int(os.environ.get("PORT", "8001"))
    async with websockets.serve(handler, "", port):
        await stop

async def handler(websocket, path):
    """
    Handle a connection and dispatch it according to who is connecting.

    """
    # Receive and parse the "init" event from the UI.
    message = await websocket.recv()
    event = json.loads(message)

    if event['type'] == 'join':
        # Second player joins an existing game.
        await join(websocket, event['token'])
    else:
        # First player starts a new game.
        await start(websocket, event['id'])

if __name__ == "__main__":
    asyncio.run(main())