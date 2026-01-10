"""
Scheduler Service - Background task scheduling

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ScheduleFrequency(str, Enum):
    """Frequency options for scheduled tasks"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    id: str
    name: str
    function: Callable
    frequency: ScheduleFrequency
    next_run: datetime
    last_run: Optional[datetime] = None
    run_count: int = 0
    is_active: bool = True
    kwargs: Dict = field(default_factory=dict)


class SchedulerService:
    """Background task scheduler"""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None

    def add_task(
        self,
        task_id: str,
        name: str,
        function: Callable,
        frequency: ScheduleFrequency,
        start_time: Optional[datetime] = None,
        **kwargs
    ) -> ScheduledTask:
        """Add a new scheduled task"""
        if start_time is None:
            start_time = self._calculate_next_run(frequency)

        task = ScheduledTask(
            id=task_id,
            name=name,
            function=function,
            frequency=frequency,
            next_run=start_time,
            kwargs=kwargs
        )

        self.tasks[task_id] = task
        logger.info(f"Scheduled task '{name}' ({task_id}) - next run: {start_time}")
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Removed task {task_id}")
            return True
        return False

    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        if task_id in self.tasks:
            self.tasks[task_id].is_active = False
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if task_id in self.tasks:
            self.tasks[task_id].is_active = True
            return True
        return False

    def _calculate_next_run(self, frequency: ScheduleFrequency, from_time: datetime = None) -> datetime:
        """Calculate the next run time based on frequency"""
        now = from_time or datetime.utcnow()

        if frequency == ScheduleFrequency.HOURLY:
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif frequency == ScheduleFrequency.DAILY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif frequency == ScheduleFrequency.WEEKLY:
            days_until_monday = (7 - now.weekday()) % 7 or 7
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        elif frequency == ScheduleFrequency.MONTHLY:
            if now.month == 12:
                return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

        return now + timedelta(hours=1)

    async def _run_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            logger.info(f"Running scheduled task: {task.name}")

            if asyncio.iscoroutinefunction(task.function):
                await task.function(**task.kwargs)
            else:
                task.function(**task.kwargs)

            task.last_run = datetime.utcnow()
            task.run_count += 1
            task.next_run = self._calculate_next_run(task.frequency, task.last_run)

            logger.info(f"Task '{task.name}' completed. Next run: {task.next_run}")

        except Exception as e:
            logger.error(f"Error running task '{task.name}': {e}")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler started")

        while self.running:
            now = datetime.utcnow()

            for task in list(self.tasks.values()):
                if task.is_active and task.next_run <= now:
                    asyncio.create_task(self._run_task(task))

            # Check every minute
            await asyncio.sleep(60)

        logger.info("Scheduler stopped")

    async def start(self):
        """Start the scheduler"""
        if self.running:
            return

        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            "running": self.running,
            "task_count": len(self.tasks),
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "frequency": t.frequency.value,
                    "is_active": t.is_active,
                    "next_run": t.next_run.isoformat() if t.next_run else None,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "run_count": t.run_count
                }
                for t in self.tasks.values()
            ]
        }


# Global scheduler instance
scheduler = SchedulerService()


# ============== Built-in Scheduled Tasks ==============

async def generate_daily_report():
    """Generate daily fraud report"""
    from .report_service import generate_scheduled_report
    await generate_scheduled_report("daily")


async def generate_weekly_report():
    """Generate weekly fraud report"""
    from .report_service import generate_scheduled_report
    await generate_scheduled_report("weekly")


async def cleanup_old_logs():
    """Clean up old audit logs"""
    from ..db.database import SessionLocal
    from ..db.models import AuditLog
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(AuditLog).filter(AuditLog.created_at < cutoff).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} old audit logs")
    except Exception as e:
        logger.error(f"Failed to cleanup logs: {e}")
        db.rollback()
    finally:
        db.close()


async def cleanup_expired_tokens():
    """Clean up expired refresh tokens"""
    from ..db.database import SessionLocal
    from ..db.models import RefreshToken
    from datetime import datetime

    db = SessionLocal()
    try:
        deleted = db.query(RefreshToken).filter(
            (RefreshToken.expires_at < datetime.utcnow()) |
            (RefreshToken.is_revoked == True)
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} expired/revoked tokens")
    except Exception as e:
        logger.error(f"Failed to cleanup tokens: {e}")
        db.rollback()
    finally:
        db.close()


def setup_default_tasks():
    """Setup default scheduled tasks"""
    # Daily report at midnight
    scheduler.add_task(
        task_id="daily_report",
        name="Daily Fraud Report",
        function=generate_daily_report,
        frequency=ScheduleFrequency.DAILY
    )

    # Weekly report on Monday
    scheduler.add_task(
        task_id="weekly_report",
        name="Weekly Fraud Report",
        function=generate_weekly_report,
        frequency=ScheduleFrequency.WEEKLY
    )

    # Cleanup old logs monthly
    scheduler.add_task(
        task_id="cleanup_logs",
        name="Cleanup Old Audit Logs",
        function=cleanup_old_logs,
        frequency=ScheduleFrequency.MONTHLY
    )

    # Cleanup expired tokens daily
    scheduler.add_task(
        task_id="cleanup_tokens",
        name="Cleanup Expired Tokens",
        function=cleanup_expired_tokens,
        frequency=ScheduleFrequency.DAILY
    )
