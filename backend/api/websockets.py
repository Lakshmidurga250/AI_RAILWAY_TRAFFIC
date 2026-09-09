"""Real-Time WebSocket Stream for Control Center."""
import asyncio
import json
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from simulation.engine.digital_twin import digital_twin
from simulation.events.event_bus import event_bus

router = APIRouter(tags=["WebSockets"])

class ConnectionManager:
    """Manages connected control-center dashboard WebSocket clients."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)
        for dc in dead_connections:
            self.disconnect(dc)

manager = ConnectionManager()

@router.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    """Streams live digital twin snapshot at 1Hz to connected clients."""
    await manager.connect(websocket)
    try:
        # Send initial snapshot immediately
        initial_snap = await asyncio.to_thread(digital_twin.get_live_snapshot)
        await websocket.send_text(json.dumps({"type": "INIT_SNAPSHOT", "data": initial_snap}))

        while True:
            await asyncio.sleep(1.0)
            snap = await asyncio.to_thread(digital_twin.get_live_snapshot)
            await websocket.send_text(json.dumps({
                "type": "TICK",
                "timestamp": snap["timestamp"],
                "simulation": snap["simulation"],
                "trains": snap["trains"],
                "signals": snap["signals"],
                "conflicts": snap["conflicts"]
            }))
    except (WebSocketDisconnect, ConnectionResetError, RuntimeError):
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
