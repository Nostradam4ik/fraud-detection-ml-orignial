#!/usr/bin/env python3
"""
Automated Database Backup Script

Features:
- SQLite database backup with compression
- Automatic rotation (keep last N backups)
- Cloud upload support (S3, GCS)
- Email notifications on failure
- Cron-friendly for scheduling

Usage:
    python backup.py                    # Full backup
    python backup.py --compress         # Compressed backup
    python backup.py --upload s3        # Upload to S3
    python backup.py --rotate 7         # Keep only last 7 backups
"""

import os
import sys
import shutil
import gzip
import hashlib
import argparse
import smtplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "db_path": "backend/fraud_detection.db",
    "backup_dir": "backups",
    "max_backups": 30,
    "compress": True,
    "notify_on_failure": True,
    "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "smtp_user": os.environ.get("SMTP_USER", ""),
    "smtp_password": os.environ.get("SMTP_PASSWORD", ""),
    "notify_email": os.environ.get("BACKUP_NOTIFY_EMAIL", ""),
    "s3_bucket": os.environ.get("BACKUP_S3_BUCKET", ""),
    "gcs_bucket": os.environ.get("BACKUP_GCS_BUCKET", ""),
}


def get_file_hash(filepath: str) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_backup(db_path: str, backup_dir: str, compress: bool = True) -> Optional[str]:
    """
    Create a backup of the database

    Args:
        db_path: Path to the database file
        backup_dir: Directory to store backups
        compress: Whether to compress the backup

    Returns:
        Path to the created backup file or None on failure
    """
    try:
        # Ensure backup directory exists
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"fraud_detection_{timestamp}"

        if not os.path.exists(db_path):
            logger.error(f"Database not found: {db_path}")
            return None

        if compress:
            backup_path = os.path.join(backup_dir, f"{backup_name}.db.gz")
            logger.info(f"Creating compressed backup: {backup_path}")

            with open(db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            backup_path = os.path.join(backup_dir, f"{backup_name}.db")
            logger.info(f"Creating backup: {backup_path}")
            shutil.copy2(db_path, backup_path)

        # Calculate and log hash
        original_hash = get_file_hash(db_path)
        backup_size = os.path.getsize(backup_path)
        original_size = os.path.getsize(db_path)

        logger.info(f"Backup created successfully:")
        logger.info(f"  - Original size: {original_size / 1024:.2f} KB")
        logger.info(f"  - Backup size: {backup_size / 1024:.2f} KB")
        logger.info(f"  - Compression ratio: {backup_size / original_size * 100:.1f}%")
        logger.info(f"  - Original MD5: {original_hash}")

        # Create metadata file
        metadata_path = backup_path + ".meta"
        with open(metadata_path, 'w') as f:
            f.write(f"timestamp={timestamp}\n")
            f.write(f"original_hash={original_hash}\n")
            f.write(f"original_size={original_size}\n")
            f.write(f"backup_size={backup_size}\n")
            f.write(f"compressed={compress}\n")

        return backup_path

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


def rotate_backups(backup_dir: str, max_backups: int) -> List[str]:
    """
    Remove old backups, keeping only the most recent ones

    Args:
        backup_dir: Directory containing backups
        max_backups: Maximum number of backups to keep

    Returns:
        List of deleted backup files
    """
    deleted = []

    try:
        # Get all backup files
        backup_files = []
        for f in Path(backup_dir).glob("fraud_detection_*.db*"):
            if not f.name.endswith(".meta"):
                backup_files.append(f)

        # Sort by modification time (oldest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime)

        # Delete oldest if exceeding max
        while len(backup_files) > max_backups:
            old_backup = backup_files.pop(0)
            meta_file = Path(str(old_backup) + ".meta")

            logger.info(f"Removing old backup: {old_backup.name}")
            old_backup.unlink()
            deleted.append(str(old_backup))

            if meta_file.exists():
                meta_file.unlink()

        logger.info(f"Rotation complete. {len(backup_files)} backups remaining.")

    except Exception as e:
        logger.error(f"Rotation failed: {e}")

    return deleted


def upload_to_s3(backup_path: str, bucket: str) -> bool:
    """Upload backup to AWS S3"""
    try:
        import boto3

        s3 = boto3.client('s3')
        key = f"backups/{os.path.basename(backup_path)}"

        logger.info(f"Uploading to S3: s3://{bucket}/{key}")
        s3.upload_file(backup_path, bucket, key)

        # Upload metadata too
        meta_path = backup_path + ".meta"
        if os.path.exists(meta_path):
            s3.upload_file(meta_path, bucket, key + ".meta")

        logger.info("S3 upload complete")
        return True

    except ImportError:
        logger.error("boto3 not installed. Run: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return False


def upload_to_gcs(backup_path: str, bucket: str) -> bool:
    """Upload backup to Google Cloud Storage"""
    try:
        from google.cloud import storage

        client = storage.Client()
        bucket_obj = client.bucket(bucket)
        blob_name = f"backups/{os.path.basename(backup_path)}"
        blob = bucket_obj.blob(blob_name)

        logger.info(f"Uploading to GCS: gs://{bucket}/{blob_name}")
        blob.upload_from_filename(backup_path)

        # Upload metadata too
        meta_path = backup_path + ".meta"
        if os.path.exists(meta_path):
            meta_blob = bucket_obj.blob(blob_name + ".meta")
            meta_blob.upload_from_filename(meta_path)

        logger.info("GCS upload complete")
        return True

    except ImportError:
        logger.error("google-cloud-storage not installed. Run: pip install google-cloud-storage")
        return False
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        return False


def send_notification(subject: str, body: str, is_error: bool = False) -> bool:
    """Send email notification"""
    if not CONFIG["notify_email"] or not CONFIG["smtp_user"]:
        logger.warning("Email notification not configured")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = CONFIG["smtp_user"]
        msg['To'] = CONFIG["notify_email"]
        msg['Subject'] = f"[Fraud Detection Backup] {subject}"

        if is_error:
            body = f"ERROR: {body}\n\nPlease check the backup system."

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(CONFIG["smtp_host"], CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(CONFIG["smtp_user"], CONFIG["smtp_password"])
            server.send_message(msg)

        logger.info("Notification email sent")
        return True

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def restore_backup(backup_path: str, db_path: str) -> bool:
    """
    Restore a database from backup

    Args:
        backup_path: Path to the backup file
        db_path: Path to restore to

    Returns:
        True if successful
    """
    try:
        # Create a backup of current DB first
        if os.path.exists(db_path):
            pre_restore_backup = db_path + ".pre_restore"
            shutil.copy2(db_path, pre_restore_backup)
            logger.info(f"Created pre-restore backup: {pre_restore_backup}")

        # Restore
        if backup_path.endswith('.gz'):
            logger.info(f"Decompressing and restoring: {backup_path}")
            with gzip.open(backup_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            logger.info(f"Restoring: {backup_path}")
            shutil.copy2(backup_path, db_path)

        logger.info("Restore complete")
        return True

    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def list_backups(backup_dir: str) -> List[dict]:
    """List all available backups with metadata"""
    backups = []

    for f in sorted(Path(backup_dir).glob("fraud_detection_*.db*")):
        if f.name.endswith(".meta"):
            continue

        info = {
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_mtime),
            "compressed": f.name.endswith(".gz")
        }

        # Read metadata if available
        meta_path = Path(str(f) + ".meta")
        if meta_path.exists():
            with open(meta_path) as mf:
                for line in mf:
                    key, value = line.strip().split("=", 1)
                    info[key] = value

        backups.append(info)

    return backups


def main():
    parser = argparse.ArgumentParser(description="Database Backup Utility")
    parser.add_argument("--db", default=CONFIG["db_path"], help="Path to database")
    parser.add_argument("--backup-dir", default=CONFIG["backup_dir"], help="Backup directory")
    parser.add_argument("--compress", action="store_true", default=CONFIG["compress"], help="Compress backup")
    parser.add_argument("--no-compress", action="store_true", help="Don't compress backup")
    parser.add_argument("--rotate", type=int, default=CONFIG["max_backups"], help="Max backups to keep")
    parser.add_argument("--upload", choices=["s3", "gcs"], help="Upload to cloud storage")
    parser.add_argument("--restore", metavar="BACKUP_FILE", help="Restore from backup")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--notify", action="store_true", help="Send email notification")

    args = parser.parse_args()

    # List backups
    if args.list:
        backups = list_backups(args.backup_dir)
        if not backups:
            print("No backups found.")
        else:
            print(f"\n{'Name':<45} {'Size':<12} {'Created':<20}")
            print("-" * 80)
            for b in backups:
                size_str = f"{b['size'] / 1024:.1f} KB"
                print(f"{b['name']:<45} {size_str:<12} {b['created'].strftime('%Y-%m-%d %H:%M')}")
        return

    # Restore from backup
    if args.restore:
        success = restore_backup(args.restore, args.db)
        sys.exit(0 if success else 1)

    # Create backup
    compress = args.compress and not args.no_compress
    backup_path = create_backup(args.db, args.backup_dir, compress)

    if not backup_path:
        if args.notify or CONFIG["notify_on_failure"]:
            send_notification("Backup Failed", "Database backup failed", is_error=True)
        sys.exit(1)

    # Rotate old backups
    rotate_backups(args.backup_dir, args.rotate)

    # Upload to cloud
    if args.upload == "s3" and CONFIG["s3_bucket"]:
        upload_to_s3(backup_path, CONFIG["s3_bucket"])
    elif args.upload == "gcs" and CONFIG["gcs_bucket"]:
        upload_to_gcs(backup_path, CONFIG["gcs_bucket"])

    # Send notification
    if args.notify:
        send_notification(
            "Backup Successful",
            f"Database backup completed successfully.\nBackup: {backup_path}"
        )

    logger.info("Backup process complete!")


if __name__ == "__main__":
    main()
