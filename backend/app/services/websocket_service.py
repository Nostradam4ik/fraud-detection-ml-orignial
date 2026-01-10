"""
WebSocket Service - Real-time notifications

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class ConnectionManager:
    """Manages WebSocket connections"""
    active_connections: Dict[int, List[WebSocket]] = field(default_factory=dict)

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws, user_id)

    async def broadcast(self, message: dict):
        """Send a message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


async def notify_fraud_detected(user_id: int, prediction_data: dict):
    """Notify user about fraud detection"""
    message = {
        "type": "fraud_detected",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "amount": prediction_data.get("amount"),
            "fraud_probability": prediction_data.get("fraud_probability"),
            "risk_score": prediction_data.get("risk_score"),
            "confidence": prediction_data.get("confidence")
        }
    }
    await manager.send_personal_message(message, user_id)


async def notify_batch_complete(user_id: int, batch_id: str, stats: dict):
    """Notify user about batch prediction completion"""
    message = {
        "type": "batch_complete",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "batch_id": batch_id,
            "total": stats.get("total"),
            "fraud_count": stats.get("fraud_count"),
            "legitimate_count": stats.get("legitimate_count")
        }
    }
    await manager.send_personal_message(message, user_id)


async def notify_model_update(version: str):
    """Notify all users about model update"""
    message = {
        "type": "model_updated",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "version": version,
            "message": f"Model updated to version {version}"
        }
    }
    await manager.broadcast(message)


async def notify_system_alert(alert_type: str, message_text: str, user_id: Optional[int] = None):
    """Send system alert to specific user or all users"""
    message = {
        "type": "system_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "alert_type": alert_type,
            "message": message_text
        }
    }

    if user_id:
        await manager.send_personal_message(message, user_id)
    else:
        await manager.broadcast(message)
