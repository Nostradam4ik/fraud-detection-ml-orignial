"""
Delete and recreate a user with a new password
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models.schemas import UserCreate
from app.services.auth_service import create_user, get_user_by_username
from app.db.models import User


def delete_and_recreate_user(username: str, password: str, email: str = None):
    """Delete existing user and create new one"""
    print(f"Processing user: {username}")

    # Initialize database
    init_db()

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check if user exists
        existing_user = get_user_by_username(db, username)

        if existing_user:
            print(f"Deleting existing user '{username}'...")
            db.delete(existing_user)
            db.commit()
            print("User deleted.")

        # Create new user
        if not email:
            email = f"{username.lower()}@frauddetection.com"

        print(f"Creating new user '{username}'...")

        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=username
        )

        user = create_user(db, user_data)

        print("\n" + "="*50)
        print("User created successfully!")
        print("="*50)
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Password: {password}")
        print("="*50)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/delete_and_recreate_user.py <username> <password> [email]")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3] if len(sys.argv) > 3 else None

    delete_and_recreate_user(username, password, email)
