"""
API Keys Routes - Manage external API keys for integrations

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...db.database import get_db
from ...db.models import User
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# In-memory storage for API keys (in production, use database)
# Structure: {key_hash: {user_id, name, created_at, last_used, scopes, is_active}}
api_keys_store = {}


class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = ["read"]  # read, write, admin
    expires_in_days: Optional[int] = 365


class APIKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: str
    last_used: Optional[str]
    expires_at: Optional[str]
    is_active: bool


class APIKeyCreateResponse(BaseModel):
    key: str  # Only shown once at creation
    id: str
    name: str
    prefix: str
    scopes: List[str]
    expires_at: Optional[str]


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hash"""
    key = f"fds_{secrets.token_urlsafe(32)}"  # fds = fraud detection system
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key for storage/lookup"""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str) -> Optional[dict]:
    """Verify an API key and return its data if valid"""
    key_hash = hash_api_key(key)
    if key_hash in api_keys_store:
        key_data = api_keys_store[key_hash]
        if key_data["is_active"]:
            # Check expiration
            if key_data.get("expires_at"):
                if datetime.fromisoformat(key_data["expires_at"]) < datetime.utcnow():
                    return None
            # Update last used
            key_data["last_used"] = datetime.utcnow().isoformat()
            return key_data
    return None


@router.post(
    "",
    response_model=APIKeyCreateResponse,
    summary="Create new API key",
    description="Create a new API key for external integrations."
)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key.

    The full key is only shown once at creation time. Store it securely!

    Scopes:
    - read: Can read predictions and analytics
    - write: Can create predictions
    - admin: Full access including user management
    """
    # Validate scopes
    valid_scopes = {"read", "write", "admin"}
    if not all(scope in valid_scopes for scope in key_data.scopes):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scopes. Valid scopes are: {valid_scopes}"
        )

    # Check user's existing keys (limit to 5)
    user_keys = [
        k for k in api_keys_store.values()
        if k["user_id"] == int(current_user.id) and k["is_active"]
    ]
    if len(user_keys) >= 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 active API keys per user. Please revoke an existing key."
        )

    # Generate key
    key, key_hash = generate_api_key()
    key_id = secrets.token_hex(8)

    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = (datetime.utcnow() + timedelta(days=key_data.expires_in_days)).isoformat()

    # Store key data
    api_keys_store[key_hash] = {
        "id": key_id,
        "user_id": int(current_user.id),
        "name": key_data.name,
        "prefix": key[:12],  # Store prefix for identification
        "scopes": key_data.scopes,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "expires_at": expires_at,
        "is_active": True
    }

    return APIKeyCreateResponse(
        key=key,
        id=key_id,
        name=key_data.name,
        prefix=key[:12],
        scopes=key_data.scopes,
        expires_at=expires_at
    )


@router.get(
    "",
    response_model=List[APIKeyResponse],
    summary="List API keys",
    description="List all API keys for the current user."
)
async def list_api_keys(
    current_user: UserResponse = Depends(get_current_user)
):
    """List all API keys for the current user (without revealing the actual keys)."""
    user_keys = [
        APIKeyResponse(
            id=k["id"],
            name=k["name"],
            prefix=k["prefix"],
            scopes=k["scopes"],
            created_at=k["created_at"],
            last_used=k["last_used"],
            expires_at=k["expires_at"],
            is_active=k["is_active"]
        )
        for k in api_keys_store.values()
        if k["user_id"] == int(current_user.id)
    ]

    return sorted(user_keys, key=lambda x: x.created_at, reverse=True)


@router.delete(
    "/{key_id}",
    summary="Revoke API key",
    description="Revoke an API key by its ID."
)
async def revoke_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Revoke an API key. This action cannot be undone."""
    for key_hash, key_data in api_keys_store.items():
        if key_data["id"] == key_id and key_data["user_id"] == int(current_user.id):
            key_data["is_active"] = False
            return {"message": "API key revoked successfully"}

    raise HTTPException(status_code=404, detail="API key not found")


@router.post(
    "/{key_id}/rotate",
    response_model=APIKeyCreateResponse,
    summary="Rotate API key",
    description="Rotate an API key, generating a new key while keeping the same settings."
)
async def rotate_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Rotate an API key.

    This revokes the old key and creates a new one with the same settings.
    """
    old_key_data = None
    old_key_hash = None

    for key_hash, key_data in api_keys_store.items():
        if key_data["id"] == key_id and key_data["user_id"] == int(current_user.id):
            old_key_data = key_data
            old_key_hash = key_hash
            break

    if not old_key_data:
        raise HTTPException(status_code=404, detail="API key not found")

    # Revoke old key
    old_key_data["is_active"] = False

    # Generate new key with same settings
    new_key, new_key_hash = generate_api_key()
    new_key_id = secrets.token_hex(8)

    api_keys_store[new_key_hash] = {
        "id": new_key_id,
        "user_id": int(current_user.id),
        "name": old_key_data["name"],
        "prefix": new_key[:12],
        "scopes": old_key_data["scopes"],
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "expires_at": old_key_data["expires_at"],
        "is_active": True
    }

    return APIKeyCreateResponse(
        key=new_key,
        id=new_key_id,
        name=old_key_data["name"],
        prefix=new_key[:12],
        scopes=old_key_data["scopes"],
        expires_at=old_key_data["expires_at"]
    )


@router.get(
    "/{key_id}/usage",
    summary="Get API key usage",
    description="Get usage statistics for an API key."
)
async def get_api_key_usage(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get usage statistics for an API key."""
    for key_data in api_keys_store.values():
        if key_data["id"] == key_id and key_data["user_id"] == int(current_user.id):
            return {
                "id": key_id,
                "name": key_data["name"],
                "created_at": key_data["created_at"],
                "last_used": key_data["last_used"],
                "is_active": key_data["is_active"],
                "expires_at": key_data["expires_at"],
                # In production, you would track actual usage metrics
                "usage_stats": {
                    "total_requests": 0,  # Would be tracked in production
                    "last_24h": 0,
                    "last_7d": 0
                }
            }

    raise HTTPException(status_code=404, detail="API key not found")
