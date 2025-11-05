"""
FastAPI Server

Web server for serving dashboard and WebSocket updates.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="LLMPoker Assistant API", version="0.1.0")

# Store active WebSocket connections
active_connections: List[WebSocket] = []


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
except RuntimeError:
    logger.warning("Static files directory not found")


@app.get("/")
async def root():
    """Serve main dashboard page."""
    try:
        with open("src/ui/static/index.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>LLMPoker Assistant</h1><p>Dashboard loading...</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "connections": len(active_connections),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Sends game state updates and recommendations to connected clients.
    """
    await websocket.accept()
    active_connections.append(websocket)

    logger.info(f"WebSocket client connected (total: {len(active_connections)})")

    try:
        # Keep connection alive
        while True:
            # Wait for messages (keep-alive)
            data = await websocket.receive_text()

            # Echo back (for testing)
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected (total: {len(active_connections)})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_update(message: dict):
    """
    Broadcast message to all connected WebSocket clients.

    Args:
        message: Dict to send as JSON
    """
    if not active_connections:
        return

    # Convert to JSON
    message_json = json.dumps(message)

    # Send to all connections
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message_json)
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            disconnected.append(connection)

    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


async def send_game_state_update(game_state: dict, vision_confidence: float):
    """
    Send game state update to clients.

    Args:
        game_state: Current game state
        vision_confidence: Vision confidence score
    """
    await broadcast_update(
        {
            "type": "game_state_update",
            "state": game_state,
            "vision_confidence": vision_confidence,
        }
    )


async def send_recommendation(recommendation: dict):
    """
    Send recommendation to clients.

    Args:
        recommendation: Recommendation dict
    """
    await broadcast_update(
        {
            "type": "recommendation",
            **recommendation,
        }
    )


async def send_system_alert(message: str, level: str = "info"):
    """
    Send system alert to clients.

    Args:
        message: Alert message
        level: Alert level (info, warning, error)
    """
    await broadcast_update(
        {
            "type": "system_alert",
            "message": message,
            "level": level,
        }
    )


def get_connection_count() -> int:
    """Get number of active WebSocket connections."""
    return len(active_connections)
