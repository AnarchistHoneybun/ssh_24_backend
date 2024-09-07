import json
import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/generate_roadmap"  
    async with websockets.connect(uri) as websocket:
        await websocket.send("damps.home@gmail.com")
        await websocket.send("Product manager")
        await websocket.send("Google")

        async for message in websocket:
            print(message)
            if isinstance(message, str):
                response = json.loads(message)
                if response.get("status") == "completed":
                    break

async def test__submapwebsocket():
    uri = "ws://localhost:8000/generate_submap" 
    async with websockets.connect(uri) as websocket:
        await websocket.send("goeldeepa@gmail.com")
        await websocket.send("Personal Product Management Projects")
        await websocket.send("Take on personal projects that require product management skills, such as developing a mobile app or organizing an event.")
        await websocket.send("NA")
        await websocket.send("Product Manager")
        await websocket.send("Google")
        await websocket.send("[7,1]")

        async for message in websocket:
            print(message)
            if isinstance(message, str):
                response = json.loads(message)
                if response.get("status") == "completed":
                    break


asyncio.run(test__submapwebsocket())
