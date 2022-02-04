import asyncio
import json
import websockets


async def handler(websocket):
    
    async for message in websocket:
        event = json.loads(message)
        await websocket.send(json.dumps(event))
        print(message)
    # while True:
    #     try:
    #         message = await websocket.recv()
    #     except:
    #         break
    #     print(message)


async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())