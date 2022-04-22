import websockets
import json
from user.user import User

class Events:
    def __init__(self, websocket, app):
        self.user = None
        self.connection = None
        self.websocket = websocket
        self.app = app

    def broadcast(self, sockets, messageType, **kwargs):
        websockets.broadcast(
            sockets,
            json.dumps(
                {'type': messageType, **kwargs}
            )
        )

    def start(self, event):
        id = event['id']
        if id in self.app.keys():
            self.user = self.app[id]
            self.user.handle_reconnect(self.websocket, event['location'])
        else:       
            self.user = User(id, self.websocket, self.app)
            self.app[id] = self.user
            self.user.handle_login()

        self.broadcast({self.websocket}, 'friends', friends=self.user.get_friends())

    def accept(self, event):
        print('joining')
        self.user.join_game(self.app[event['opponent']])
        self.broadcast({self.user.opponent.websocket}, 'accept', **event)

    def invite(self, event):
        if event['target'] in self.app.keys():
            target = self.app[event['target']]
            if not target.in_game:
                self.user.join_game(self.app[event['target']])
                self.broadcast({self.user.opponent.websocket}, 'invite', **event)
            else:
                self.broadcast({self.user.websocket}, 'playing')     
        else:
            self.broadcast({self.user.websocket}, 'offline')

    def chatMessage(self, event):
        if event['recipient_id'] == 0:
            self.send_to_global(event)
        else: 
            self.send_to_specific(event)
    
    def send_to_global(self, event):
        sockets = [user.websocket for user in self.app.values() if user.id != event['id']]
        self.broadcast(sockets, 'chatMessage', **self.get_message_kwargs(event))

    def send_to_specific(self, event):
        if event['recipient_id'] in self.app.keys():
  
            self.broadcast(
                [self.app[event['recipient_id']].websocket],
                'chatMessage', **self.get_message_kwargs(event)
            )

    def get_message_kwargs(self, event):
        return {
            'sender': event['sender'],
            'recipient_id': event['recipient_id'],
            'content': event['content'],
            'sender_id': event['id']
        }

    def status(self, event):
        id, name = event['id'], event['name']
        is_online = event['id'] in self.app.keys()
        self.broadcast(
            [self.websocket], 'newFriend', id=id, name=name,
            online=is_online,
            in_game=False if not is_online else self.app[id].in_game
        )

    def coinFlip(self, event):
        self.broadcast({self.user.opponent.websocket}, 'coinFlip', coinFlip=event['coinFlip'])

    def colourChoice(self, event):
        self.broadcast({self.user.opponent.websocket}, 'colourChoice', colour=event['colour'])

    def move(self, event):
        self.broadcast({self.user.opponent.websocket}, 'move', move=event['move'])
    
    def chat(self, event):
        self.broadcast({self.user.opponent.websocket}, 'chat', message=event['message'], sender=event['sender'])

