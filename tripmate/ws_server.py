import asyncio
import websockets
import json
from .agent import TripMateAgent  # Reuse logic
from concurrent.futures import ThreadPoolExecutor

connected_clients = set()
executor = ThreadPoolExecutor()

async def handle_client(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"🛰️  Received from Eliza: {data['message']}")
                agent = TripMateAgent()  # Provide 'self'
                result = agent.plan_trip(data['message'])
                await websocket.send(json.dumps({ "message": result }))
                print(f"result from plan_trip={result}")
            except Exception as e:
                await websocket.send(json.dumps({ "error": str(e) }))
    finally:
        connected_clients.remove(websocket)

async def start_ws_server():
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    print("✅ TripMate WebSocket Server running on ws://0.0.0.0:8765")
    await asyncio.Future()  # Run forever
    return server


# import asyncio
# import websockets
# import json
# from tripmate.main import plan_trip  # core logic from TripMate

# connected_clients = set()

# async def handle_client(websocket):
#     connected_clients.add(websocket)
#     try:
#         async for message in websocket:
#             try:
#                 data = json.loads(message)
#                 print(f"Received from Eliza: {data}")
#                 response = plan_trip(data['message'])
#                 await websocket.send(json.dumps(response))
#             except Exception as e:
#                 await websocket.send(json.dumps({"error": str(e)}))
#     finally:
#         connected_clients.remove(websocket)

# async def main():
#     async with websockets.serve(handle_client, "192.168.0.1", 8765):
#         print("TripMate WebSocket Server running on ws://192.168.0.1:8765")
#         await asyncio.Future()  # Run forever

# if __name__ == "__main__":
#     asyncio.run(main())
