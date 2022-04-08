import asyncio
import json
import websockets
import secrets

import os
import signal

import requests

class Connection:
    def __init__(self, id, websocket):
        self.id = id
        self.websocket = websocket
        self.in_game = False
        self.opponent = None
        self.active = True
    
    def get_friends(self): 

        friend_data = requests.get(f'{os.environ['API_BASE_URL']}backend/friends/getFriends.php?id={self.id}').json()
        friends = {}
        for friend in friend_data:
            id, name = friend[0], friend[1]
            friends[id] = {
                'id': id,
                'name': name,
                'online': False,
                'inGame': False
            }
            if id in JOIN.keys():
                friends[id]['online'] = True
                friends[id]['inGame'] = JOIN[id].in_game
        
        return friends
    
    def get_friends_sockets(self):
        friend_data = requests.get(f'{os.environ['API_BASE_URL']}backend/friends/getFriends.php?id={self.id}').json()
        return [JOIN[friend[0]].websocket for friend in friend_data if friend[0] in JOIN.keys()]

    def handle_login(self):
        friends = self.get_friends_sockets()
        print(friends)
        websockets.broadcast(self.get_friends_sockets(), json.dumps({
            'type': 'login',
            'id': self.id
        }))

    def notify_opponent(self, is_returning=False):
        if is_returning:
            websockets.broadcast([self.opponent.websocket], {
                'type': 'reconnect',
                'id': self.id
            })
        else:
            websockets.broadcast([self.opponent.websocket], {
                'type': 'disconnect',
                'id': self.id
            })
    
    async def handle_disconnect(self):
        if self.in_game:
            self.notify_opponent()
        await asyncio.sleep(3)
        if self.active == False:
            friends = self.get_friends()
            websockets.broadcast(
                [JOIN[id].websocket for id in friends.keys() if id in JOIN.keys()], json.dumps({
                    'type': 'logout',
                    'id': self.id,
                })
            )
            del JOIN[self.id]

    def handle_reconnect(self, socket):
        self.active = True
        self.websocket = socket
        if self.in_game:
            self.notify_opponent(True)



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
    user = 0
    # Receive and parse the "init" event from the UI.
    try:
        async for message in websocket:
            event = json.loads(message)
            user_id = event["id"]
            user = event["id"]

            if event["type"] == 'message':
                websockets.broadcast(CHAT, json.dumps(event))

            if event["type"] == "accept":
                await join_game(websocket, JOIN[event["id"]], JOIN[event["opponent"]], event)


            elif event['type'] == 'invite':
                player_1 = JOIN[event["id"]]
                player_2 = JOIN[event["target"]]
                await join_game(websocket, player_1, player_2, event)
            
            elif event['type'] == 'get_friends':
                websockets.broadcast({websocket}, json.dumps({
                    "type": "players",
                    "players": get_friends(event['ids']),
                }))

            elif event["type"] == "start":
                # First player starts a new game.
                if user in JOIN.keys():
                    socket = JOIN[user]
                    socket.active = True
                    socket.handle_reconnect(websocket)
                else:       
                    socket = Connection(event['id'], websocket)
                    JOIN[socket.id] = socket
                    socket.handle_login()

                websockets.broadcast(
                    {websocket},
                    json.dumps(
                        {'type': 'friends', 'friends': socket.get_friends()}
                    )
                )
                

            elif event['type'] == "chatMessage":
                if event['recipient_id'] == 0:

                    websockets.broadcast([user.websocket for user in JOIN.values() if user.id != event['id']], json.dumps({
                            'type': 'chatMessage',
                            'sender': event['sender'],
                            'recipient_id': event['recipient_id'],
                            'content': event['content'],
                            'sender_id': event['id']
                        }))
                else:
                    sockets = {websocket}
                    if event['recipient_id'] in JOIN.keys():
                        sockets = {websocket, JOIN[event['recipient_id']].websocket}
                    websockets.broadcast(sockets, json.dumps({
                            'type': 'chatMessage',
                            'sender': event['sender'],
                            'recipient_id': event['recipient_id'],
                            'content': event['content'],
                            'sender_id': event['id']
                        }))

                        

            elif event['type'] == 'status':
                try:
                    user = JOIN[event['id']]
                    websockets.broadcast({websocket}, json.dumps({
                        'type': 'newFriend',
                        'id': event['id'],
                        'name': event['name'],
                        'online': True,
                        'in_game': user.in_game
                    }))
                except: 
                    websockets.broadcast({websocket}, json.dumps({
                        'type': 'newFriend',
                        'id': event['id'],
                        'name': event['name'],
                        'online': False,
                        'in_game': False
                    }))
    finally: 
        JOIN[user].active = False
        await JOIN[user].handle_disconnect()
        print(JOIN)



        
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

def get_friends(ids): 
    return {JOIN[id].id: {"id": JOIN[id].id, "in_game": JOIN[id].in_game} for id in ids if id in JOIN.keys()}

if __name__ == "__main__":
    asyncio.run(main())