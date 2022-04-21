import websockets
import asyncio
import requests
import os
import json

class User:
    def __init__(self, id, websocket, app):
        self.id = id
        self.websocket = websocket
        self.app = app
        self.in_game = False
        self.opponent = None
        self.active = True
    
    def get_friends(self): 

        friend_data = requests.get(f'{os.environ.get("API_BASE_URL")}backend/friends/getFriends.php?id={self.id}').json()
        friends = {}
        for friend in friend_data:
            id, name = friend[0], friend[1]
            friends[id] = {
                'id': id,
                'name': name,
                'online': False,
                'inGame': False
            }
            if id in self.app.keys():
                friends[id]['online'] = True
                friends[id]['inGame'] = self.app[id].in_game
        
        return friends
    
    def get_friends_sockets(self):
        friend_data = requests.get(f'{os.environ.get("API_BASE_URL")}backend/friends/getFriends.php?id={self.id}').json()
        return [self.app[friend[0]].websocket for friend in friend_data if friend[0] in self.app.keys()]

    def handle_login(self):
        friends = self.get_friends_sockets()
        self.notify_friends('login')

    def notify_opponent(self, is_returning=False):
        if is_returning:
            websockets.broadcast({self.opponent.websocket}, json.dumps({
                'type': 'reconnect',
                'id': self.id
            }))
        else:
            websockets.broadcast({self.opponent.websocket}, json.dumps({
                'type': 'disconnect',
                'id': self.id
            }))

    
    async def handle_disconnect(self):
        print(self.app)
        self.active = False
        if self.in_game:
            self.notify_opponent()
        await asyncio.sleep(30)
        if self.active == False:
            self.notify_friends('logout')
            try:
                print(self.app)
                del self.app[self.id]
            except: 
                print('Connection already closed')


    def handle_reconnect(self, socket, location):
        self.active = True
        self.websocket = socket
        if self.in_game and location == 'game':
            self.notify_opponent(True)
        else:
            self.in_game = False
    
    def join_game(self, opponent):
        self.in_game = True
        self.opponent = opponent
        self.notify_friends('joinGame')

    def leave_game(self):
        self.in_game = False
        self.opponent = None
        self.notify_friends('leaveGame')

    def notify_friends(self, messageType, **kwargs):
        sockets = self.get_friends_sockets()
        websockets.broadcast(sockets, json.dumps({
            'type': messageType,
            'id': self.id,
            **kwargs
        }))