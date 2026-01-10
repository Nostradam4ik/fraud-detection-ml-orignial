"""
Check database tables and user data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import SessionLocal, init_db


def check_database():
    """Check database contents"""
    print("Checking database...")

    # Initialize database
    init_db()

    # Create database session
    db: Session = SessionLocal()

    try:
        # Check users
        print("\n" + "="*50)
        print("USERS")
        print("="*50)
        result = db.execute(text("SELECT id, username, email, created_at FROM users"))
        users = result.fetchall()
        for user in users:
            print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[3]}")

        # Check predictions
        print("\n" + "="*50)
        print("PREDICTIONS")
        print("="*50)
        result = db.execute(text("SELECT COUNT(*) as count FROM predictions"))
        count = result.fetchone()
        print(f"Total predictions: {count[0]}")

        if count[0] > 0:
            result = db.execute(text("""
                SELECT id, user_id, is_fraud, fraud_probability, created_at
                FROM predictions
                ORDER BY created_at DESC
                LIMIT 10
            """))
            predictions = result.fetchall()
            print("\nLast 10 predictions:")
            for pred in predictions:
                print(f"ID: {pred[0]}, User ID: {pred[1]}, Fraud: {pred[2]}, Prob: {pred[3]:.2%}, Created: {pred[4]}")

        # Check audit logs
        print("\n" + "="*50)
        print("AUDIT LOGS")
        print("="*50)
        result = db.execute(text("SELECT COUNT(*) as count FROM audit_logs"))
        count = result.fetchone()
        print(f"Total audit logs: {count[0]}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_database()
