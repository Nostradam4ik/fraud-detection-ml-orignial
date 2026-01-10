"""
Create an admin user for testing

This script creates a default admin user with predefined credentials.
Use this for testing and development only.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models.schemas import UserCreate
from app.services.auth_service import create_user, get_user_by_username


def create_admin_user():
    """Create a default admin user"""
    print("Creating admin user...")

    # Initialize database
    init_db()

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check if admin already exists
        existing_user = get_user_by_username(db, "admin")
        if existing_user:
            print("Admin user already exists!")
            print(f"Username: admin")
            print(f"Email: {existing_user.email}")
            return

        # Create admin user
        admin_data = UserCreate(
            username="admin",
            email="admin@frauddetection.com",
            password="Admin123!@#",
            full_name="System Administrator"
        )

        user = create_user(db, admin_data)

        print("\n" + "="*50)
        print("Admin user created successfully!")
        print("="*50)
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Password: Admin123!@#")
        print("="*50)
        print("\nIMPORTANT: Change this password after first login!")
        print("="*50)

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
