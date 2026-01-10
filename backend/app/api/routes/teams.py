"""
Team Routes - Team Management and Collaboration

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Team, User, AuditAction
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_user
from ...services.team_service import (
    create_team,
    get_team as get_team_by_id,
    get_user_teams,
    add_team_member,
    remove_team_member as remove_member_service,
    delete_team as delete_team_service,
    update_team as update_team_service
)
from ...services.audit_service import log_action

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get(
    "",
    summary="Get user's teams",
    description="Get all teams the current user is a member of."
)
async def list_my_teams(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all teams the user is a member of or owns"""
    teams = get_user_teams(db, int(current_user.id))

    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "owner_id": t.owner_id,
            "is_owner": t.owner_id == int(current_user.id),
            "member_count": len(t.members),
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in teams
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new team",
    description="Create a new team. The creator becomes the owner."
)
async def create_new_team(
    name: str,
    description: str = None,
    request: Request = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Create a new team"""
    team = create_team(db, name, int(current_user.id), description)

    # Log the action
    if request:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:255]
        log_action(
            db, AuditAction.USER_CREATE,
            user_id=int(current_user.id),
            resource_type="team",
            resource_id=str(team.id),
            details={"name": name},
            ip_address=client_ip,
            user_agent=user_agent
        )

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "created_at": team.created_at.isoformat() if team.created_at else None
    }


@router.get(
    "/{team_id}",
    summary="Get team details",
    description="Get details of a specific team."
)
async def get_team(
    team_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get team details"""
    team = get_team_by_id(db, team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is a member
    user_ids = [m.id for m in team.members]
    if int(current_user.id) not in user_ids and team.owner_id != int(current_user.id):
        raise HTTPException(status_code=403, detail="Not a member of this team")

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "is_active": team.is_active,
        "created_at": team.created_at.isoformat() if team.created_at else None,
        "members": [
            {
                "id": m.id,
                "username": m.username,
                "email": m.email,
                "full_name": m.full_name,
                "role": m.role.value if m.role else "viewer"
            }
            for m in team.members
        ]
    }


@router.patch(
    "/{team_id}",
    summary="Update team",
    description="Update team details. Only the owner can update."
)
async def update_team_details(
    team_id: int,
    name: str = None,
    description: str = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update team details"""
    team = get_team_by_id(db, team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.owner_id != int(current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can update the team")

    updated = update_team_service(db, team_id, int(current_user.id), name, description)

    return {
        "id": updated.id,
        "name": updated.name,
        "description": updated.description,
        "updated_at": updated.updated_at.isoformat() if updated.updated_at else None
    }


@router.post(
    "/{team_id}/members/{user_id}",
    summary="Add team member",
    description="Add a user to the team. Only the owner can add members."
)
async def add_member(
    team_id: int,
    user_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Add a member to the team"""
    team = get_team_by_id(db, team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.owner_id != int(current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can add members")

    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = add_team_member(db, team_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail="User is already a member")

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.USER_UPDATE,
        user_id=int(current_user.id),
        resource_type="team",
        resource_id=str(team_id),
        details={"action": "add_member", "added_user_id": user_id},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": f"User added to team successfully"}


@router.delete(
    "/{team_id}/members/{user_id}",
    summary="Remove team member",
    description="Remove a user from the team. Owner can remove anyone, members can remove themselves."
)
async def remove_member(
    team_id: int,
    user_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Remove a member from the team"""
    team = get_team_by_id(db, team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check permissions
    is_owner = team.owner_id == int(current_user.id)
    is_self = user_id == int(current_user.id)

    if not is_owner and not is_self:
        raise HTTPException(status_code=403, detail="Cannot remove other members")

    # Owner cannot leave their own team
    if is_self and is_owner:
        raise HTTPException(status_code=400, detail="Owner cannot leave the team. Transfer ownership or delete the team.")

    success = remove_member_service(db, team_id, user_id, int(current_user.id))

    if not success:
        raise HTTPException(status_code=400, detail="User is not a member")

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.USER_UPDATE,
        user_id=int(current_user.id),
        resource_type="team",
        resource_id=str(team_id),
        details={"action": "remove_member", "removed_user_id": user_id},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": "User removed from team"}


@router.delete(
    "/{team_id}",
    summary="Delete team",
    description="Delete a team. Only the owner can delete."
)
async def delete_team_endpoint(
    team_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Delete a team"""
    team = get_team_by_id(db, team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.owner_id != int(current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can delete the team")

    team_name = team.name
    delete_team_service(db, team_id, int(current_user.id))

    # Log the action
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:255]
    log_action(
        db, AuditAction.USER_DELETE,
        user_id=int(current_user.id),
        resource_type="team",
        resource_id=str(team_id),
        details={"deleted_team_name": team_name},
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": "Team deleted successfully"}
