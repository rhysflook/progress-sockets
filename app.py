import asyncio
import json
import websockets
import secrets

import os
import signal


class Connection:
    def __init__(self, id, websocket):
        self.id = id
        self.websocket = websocket
        self.in_game = False
        self.opponent = None

JOIN = {}
CHAT = set()

async def send_messages(player, opponent):

    async for message in player.websocket:
        event = json.loads(message)
        reciever = JOIN[opponent.id].websocket
        if event["type"] == "end":
            break
        if event["type"] == "accept":
            JOIN[opponent.id].websocket = player.websocket
        websockets.broadcast({reciever}, json.dumps(event))

async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    try:
        loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    except:
        print('running locally')
    port = int(os.environ.get("PORT", "8001"))
    async with websockets.serve(handler, "", port):
        await asyncio.Future() 

async def handler(websocket, path):
    """
    Handle a connection and dispatch it according to who is connecting.

    """
    CHAT.add(websocket)
    # Receive and parse the "init" event from the UI.
    async for message in websocket:
        event = json.loads(message)
        user_id = event["id"]

        if event["type"] == 'message':
            websockets.broadcast(CHAT, json.dumps(event))
        print(event)

        if event["type"] == "accept":
            print(JOIN)
            await join_game(websocket, JOIN[event["id"]], JOIN[event["opponent"]], event)


        elif event['type'] == 'invite':
            player_1 = JOIN[event["id"]]
            player_2 = JOIN[event["target"]]
            await join_game(websocket, player_1, player_2, event)

        elif event["type"] == "start":
            # First player starts a new game.
            socket = Connection(event['id'], websocket)
            JOIN[socket.id] = socket
        
async def join_game(websocket, player_1, player_2, event):
    
    player_1.in_game = True
    player_1.opponent = player_2
    player_2.in_game = True
    player_2.opponent = player_1
    websockets.broadcast({player_2.websocket}, json.dumps(event))

    try: 
        await send_messages(
            player_1, 
            player_2
        )
    finally:
        player_1.in_game = False
        player_1.opponent = None
        player_2.in_game = False
        player_2.opponent = None 

if __name__ == "__main__":
    asyncio.run(main())