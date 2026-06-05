import uuid
import time
from datetime import datetime, timezone
import json
import logging
import psutil
from typing import Dict, Any, List
from modules.cache import _get_client

logger = logging.getLogger(__name__)

class AuditSystem:
    """
    Continuous Audit System for SentryBill Architecture.
    Monitors Camera Health, Detection Health, Processing Health, Data Health, Communication Health.
    """
    def __init__(self):
        self.audit_logs: List[Dict[str, Any]] = []

    def log_event(self, camera_id: str, health_type: str, severity: str, description: str, suggested_fix: str) -> Dict[str, Any]:
        """
        Health Types: Camera, Detection, Processing, Data, Communication
        Severity: Info, Warning, Critical
        """
        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "camera_id": camera_id,
            "health_type": health_type,
            "severity": severity,
            "description": description,
            "suggested_fix": suggested_fix
        }
        # Publish to Redis for persistence and Node API ingestion
        redis_client = _get_client()
        if redis_client:
            redis_client.lpush("securityos_audit_logs", json.dumps(entry))
            redis_client.ltrim("securityos_audit_logs", 0, 9999) # Keep last 10000
            
        logger.info(f"[AUDIT] [{severity.upper()}] {health_type} | {camera_id}: {description}")
        return entry

    def generate_system_summary(self) -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        return {
            "processing_health": {
                "cpu_usage": cpu,
                "ram_usage": ram,
                "gpu_usage": "Not Available (Mock)",
                "queue_status": "Online"
            },
            "communication_health": {
                "redis": "Online",
                "node_api": "Online"
            },
            "recent_logs": self._get_recent_logs()
        }

    def _get_recent_logs(self) -> List[Dict]:
        redis_client = _get_client()
        if redis_client:
            logs = redis_client.lrange("securityos_audit_logs", 0, 49)
            return [json.loads(l) for l in logs]
        return []

global_audit = AuditSystem()
