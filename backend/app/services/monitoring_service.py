"""Advanced monitoring and logging service with metrics"""

import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean

from app.db.database import Base

logger = logging.getLogger(__name__)


class SystemMetric(Base):
    """Store system performance metrics"""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)

    metric_type = Column(String(50), nullable=False, index=True)  # "cpu", "memory", "disk", "api_latency"
    metric_name = Column(String(100), nullable=False)

    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # "%", "MB", "ms"

    tags = Column(Text, nullable=True)  # JSON tags for filtering

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class APIRequestLog(Base):
    """Detailed API request logging"""
    __tablename__ = "api_request_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Request details
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False, index=True)
    query_params = Column(Text, nullable=True)

    # Client info
    client_ip = Column(String(50), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)

    # Response details
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)  # Response time in milliseconds

    # Error tracking
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class MonitoringService:
    """
    Comprehensive monitoring and metrics service

    Features:
    - System resource monitoring (CPU, RAM, Disk)
    - API performance tracking
    - Error rate monitoring
    - Custom metrics
    - Real-time alerting
    """

    def __init__(self):
        # In-memory metrics cache
        self.metrics_cache = defaultdict(lambda: deque(maxlen=1000))

        # Performance tracking
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.request_count = 0

        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'api_latency_ms': 1000.0,
            'error_rate': 0.05  # 5%
        }

    def collect_system_metrics(self, db: Session):
        """Collect and store system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self._store_metric(db, "system", "cpu_usage", cpu_percent, "%")

            # Memory metrics
            memory = psutil.virtual_memory()
            self._store_metric(db, "system", "memory_usage", memory.percent, "%")
            self._store_metric(db, "system", "memory_available", memory.available / (1024**3), "GB")

            # Disk metrics
            disk = psutil.disk_usage('/')
            self._store_metric(db, "system", "disk_usage", disk.percent, "%")
            self._store_metric(db, "system", "disk_free", disk.free / (1024**3), "GB")

            # Network metrics (if available)
            try:
                net_io = psutil.net_io_counters()
                self._store_metric(db, "network", "bytes_sent", net_io.bytes_sent / (1024**2), "MB")
                self._store_metric(db, "network", "bytes_recv", net_io.bytes_recv / (1024**2), "MB")
            except:
                pass

            # Check for alerts
            self._check_system_alerts(cpu_percent, memory.percent, disk.percent)

            logger.info(f"System metrics collected: CPU={cpu_percent}%, MEM={memory.percent}%")

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    def _store_metric(
        self,
        db: Session,
        metric_type: str,
        metric_name: str,
        value: float,
        unit: Optional[str] = None
    ):
        """Store a metric in database"""
        try:
            metric = SystemMetric(
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit
            )

            db.add(metric)
            db.commit()

            # Also cache in memory
            self.metrics_cache[f"{metric_type}.{metric_name}"].append({
                'value': value,
                'timestamp': datetime.utcnow()
            })

        except Exception as e:
            logger.error(f"Failed to store metric: {e}")
            db.rollback()

    def _check_system_alerts(self, cpu: float, memory: float, disk: float):
        """Check if system metrics exceed thresholds"""
        if cpu > self.thresholds['cpu_percent']:
            logger.warning(f"HIGH CPU USAGE: {cpu}%")

        if memory > self.thresholds['memory_percent']:
            logger.warning(f"HIGH MEMORY USAGE: {memory}%")

        if disk > self.thresholds['disk_percent']:
            logger.warning(f"HIGH DISK USAGE: {disk}%")

    def log_api_request(
        self,
        db: Session,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        client_ip: Optional[str] = None,
        user_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log an API request"""
        try:
            log = APIRequestLog(
                method=method,
                path=path,
                status_code=status_code,
                response_time_ms=response_time_ms,
                client_ip=client_ip,
                user_id=user_id,
                error_message=error_message
            )

            db.add(log)
            db.commit()

            # Update in-memory stats
            self.request_times.append(response_time_ms)
            self.request_count += 1

            if status_code >= 400:
                self.error_count += 1

            # Check performance alerts
            if response_time_ms > self.thresholds['api_latency_ms']:
                logger.warning(f"SLOW API REQUEST: {path} took {response_time_ms}ms")

        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
            db.rollback()

    def get_api_performance_stats(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """Get API performance statistics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        logs = db.query(APIRequestLog).filter(
            APIRequestLog.timestamp >= cutoff
        ).all()

        if not logs:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'requests_per_hour': 0
            }

        total = len(logs)
        errors = sum(1 for log in logs if log.status_code >= 400)
        avg_time = sum(log.response_time_ms for log in logs) / total

        # Calculate requests per hour
        time_span_hours = (datetime.utcnow() - logs[-1].timestamp).total_seconds() / 3600
        requests_per_hour = total / max(time_span_hours, 1)

        # Top slow endpoints
        slow_endpoints = defaultdict(list)
        for log in logs:
            if log.response_time_ms > 500:
                slow_endpoints[log.path].append(log.response_time_ms)

        top_slow = sorted(
            [(path, sum(times)/len(times)) for path, times in slow_endpoints.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_requests': total,
            'error_count': errors,
            'error_rate': errors / total,
            'avg_response_time_ms': avg_time,
            'requests_per_hour': requests_per_hour,
            'top_slow_endpoints': [
                {'path': path, 'avg_time_ms': avg_time}
                for path, avg_time in top_slow
            ]
        }

    def get_system_health(self, db: Session) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Determine health status
            status = "healthy"
            issues = []

            if cpu > self.thresholds['cpu_percent']:
                status = "warning"
                issues.append(f"High CPU usage: {cpu}%")

            if memory.percent > self.thresholds['memory_percent']:
                status = "warning"
                issues.append(f"High memory usage: {memory.percent}%")

            if disk.percent > self.thresholds['disk_percent']:
                status = "critical"
                issues.append(f"High disk usage: {disk.percent}%")

            # Check error rate
            if self.request_count > 0:
                error_rate = self.error_count / self.request_count
                if error_rate > self.thresholds['error_rate']:
                    status = "warning"
                    issues.append(f"High error rate: {error_rate:.1%}")

            return {
                'status': status,
                'issues': issues,
                'metrics': {
                    'cpu_percent': cpu,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3),
                },
                'api_stats': {
                    'total_requests': self.request_count,
                    'error_count': self.error_count,
                    'avg_response_time_ms': sum(self.request_times) / len(self.request_times) if self.request_times else 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                'status': 'unknown',
                'issues': [str(e)],
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_metrics_history(
        self,
        db: Session,
        metric_type: str,
        metric_name: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get historical metrics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        metrics = db.query(SystemMetric).filter(
            SystemMetric.metric_type == metric_type,
            SystemMetric.metric_name == metric_name,
            SystemMetric.timestamp >= cutoff
        ).order_by(SystemMetric.timestamp).all()

        return [
            {
                'value': m.value,
                'unit': m.unit,
                'timestamp': m.timestamp.isoformat()
            }
            for m in metrics
        ]


# Global monitoring service
monitoring_service = MonitoringService()
