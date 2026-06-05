from fastapi import APIRouter
from modules.audit_system import global_audit

router = APIRouter(tags=["audit"])

@router.get("/audit/summary", summary="Root Admin Reporting - System Summary")
async def get_audit_summary():
    """
    Generates detailed summaries per SentryBill contract.
    Returns System Summary & latest Audit Logs.
    """
    return {
        "success": True,
        "data": global_audit.generate_system_summary()
    }

@router.post("/audit/log", summary="Log an internal audit event manually")
async def log_audit_event(camera_id: str, health_type: str, severity: str, description: str, suggested_fix: str):
    entry = global_audit.log_event(camera_id, health_type, severity, description, suggested_fix)
    return {"success": True, "entry": entry}
