"""
Team Service - Team management and collaboration

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..db.models import Team, User, team_members


def create_team(db: Session, name: str, owner_id: int, description: Optional[str] = None) -> Team:
    """Create a new team"""
    team = Team(
        name=name,
        description=description,
        owner_id=owner_id,
        is_active=True
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    # Add owner as a member
    add_team_member(db, team.id, owner_id)

    return team


def get_team(db: Session, team_id: int) -> Optional[Team]:
    """Get a team by ID"""
    return db.query(Team).filter(Team.id == team_id).first()


def get_user_teams(db: Session, user_id: int) -> List[Team]:
    """Get all teams a user belongs to"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    return user.teams


def get_owned_teams(db: Session, user_id: int) -> List[Team]:
    """Get all teams owned by a user"""
    return db.query(Team).filter(Team.owner_id == user_id).all()


def add_team_member(db: Session, team_id: int, user_id: int) -> bool:
    """Add a user to a team"""
    team = get_team(db, team_id)
    user = db.query(User).filter(User.id == user_id).first()

    if not team or not user:
        return False

    if user in team.members:
        return True  # Already a member

    team.members.append(user)
    db.commit()

    return True


def remove_team_member(db: Session, team_id: int, user_id: int, requester_id: int) -> bool:
    """Remove a user from a team"""
    team = get_team(db, team_id)

    if not team:
        return False

    # Only owner can remove members
    if team.owner_id != requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can remove members"
        )

    # Can't remove the owner
    if user_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove team owner"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user not in team.members:
        return False

    team.members.remove(user)
    db.commit()

    return True


def update_team(
    db: Session,
    team_id: int,
    requester_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Optional[Team]:
    """Update team details"""
    team = get_team(db, team_id)

    if not team:
        return None

    # Only owner can update
    if team.owner_id != requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can update team"
        )

    if name:
        team.name = name
    if description is not None:
        team.description = description

    db.commit()
    db.refresh(team)

    return team


def delete_team(db: Session, team_id: int, requester_id: int) -> bool:
    """Delete a team (soft delete)"""
    team = get_team(db, team_id)

    if not team:
        return False

    # Only owner can delete
    if team.owner_id != requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can delete team"
        )

    team.is_active = False
    db.commit()

    return True


def get_team_members(db: Session, team_id: int) -> List[User]:
    """Get all members of a team"""
    team = get_team(db, team_id)
    if not team:
        return []
    return team.members


def is_team_member(db: Session, team_id: int, user_id: int) -> bool:
    """Check if a user is a member of a team"""
    team = get_team(db, team_id)
    if not team:
        return False

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    return user in team.members
