import asyncio
import os
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
                await websocket.send(json.dumps({"message": result}))
                print(f"result from plan_trip={result}")
            except Exception as e:
                await websocket.send(json.dumps({"error": str(e)}))
    finally:
        connected_clients.remove(websocket)


async def start_ws_server():
    port = int(os.environ.get("PORT", 8765))
    server = await websockets.serve(handle_client, "0.0.0.0", port)
    print("✅ TripMate WebSocket Server running on port {port}")
    await asyncio.Future()  # Run forever
    return server
