"""
Reset password for a user or create the user if it doesn't exist

Usage: python scripts/reset_user_password.py <username> <new_password>
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
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def reset_or_create_user(username: str, password: str, email: str = None):
    """Reset password for existing user or create new user"""
    print(f"Processing user: {username}")

    # Initialize database
    init_db()

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check if user exists
        existing_user = get_user_by_username(db, username)

        if existing_user:
            print(f"User '{username}' found. Resetting password...")

            # Update password
            hashed_password = pwd_context.hash(password)
            existing_user.password_hash = hashed_password
            db.commit()

            print("\n" + "="*50)
            print("Password reset successfully!")
            print("="*50)
            print(f"Username: {existing_user.username}")
            print(f"Email: {existing_user.email}")
            print(f"New Password: {password}")
            print("="*50)
        else:
            print(f"User '{username}' not found. Creating new user...")

            # Create new user
            if not email:
                email = f"{username}@frauddetection.com"

            user_data = UserCreate(
                username=username,
                email=email,
                password=password,
                full_name=username.capitalize()
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
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/reset_user_password.py <username> [password] [email]")
        print("Example: python scripts/reset_user_password.py Nostradam MyPassword123!")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else "Password123!@#"
    email = sys.argv[3] if len(sys.argv) > 3 else None

    reset_or_create_user(username, password, email)
