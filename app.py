import asyncio
import json
import websockets
import secrets
from dotenv import load_dotenv
import os
import signal
import requests
from events.events import Events

class App: 
    def __init__(self):
        self.connections = {}
    
    async def main(self):
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        try:
            loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
        except:
            print('running locally')
        port = int(os.environ.get("PORT", "8001"))
        async with websockets.serve(self.handler, "", port):
            await asyncio.Future() 

    async def handler(self, websocket, path):
        """
        Handle a connection and dispatch it according to who is connecting.

        """
        handler = Events(websocket, self.connections)
        # Receive and parse the "init" event from the UI.
        try:
            async for message in websocket:
                event = json.loads(message)
                getattr(handler, event['type'])(event)

        finally: 
            await handler.user.handle_disconnect()

if __name__ == "__main__":
    load_dotenv()
    app = App()
    asyncio.run(app.main())