"""
WebSocket Routes - Real-time communication

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import JWTError, jwt

from ...core.config import settings
from ...services.websocket_service import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


def verify_websocket_token(token: str) -> dict:
    """Verify JWT token for WebSocket connection"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username or not user_id:
            return None

        return {"username": username, "user_id": int(user_id)}
    except JWTError:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications.

    Connect with: ws://host/api/v1/ws?token=YOUR_JWT_TOKEN

    Message types received:
    - fraud_detected: When fraud is detected in a prediction
    - batch_complete: When batch processing is complete
    - model_updated: When the ML model is updated
    - system_alert: System-wide notifications

    You can also send messages:
    - ping: Server will respond with pong
    - subscribe: Subscribe to specific event types
    """
    # Verify token
    user_data = verify_websocket_token(token)
    if not user_data:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = user_data["user_id"]

    # Accept connection
    await manager.connect(websocket, user_id)

    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": f"Welcome {user_data['username']}! You are now connected to real-time updates.",
        "user_id": user_id
    })

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            # Handle different message types
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe":
                # Client wants to subscribe to specific events
                events = data.get("events", [])
                await websocket.send_json({
                    "type": "subscribed",
                    "events": events
                })

            else:
                # Echo unknown messages back
                await websocket.send_json({
                    "type": "echo",
                    "original": data
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


@router.get("/ws/stats", tags=["WebSocket"])
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": manager.get_connection_count(),
        "active_users": manager.get_user_count()
    }
