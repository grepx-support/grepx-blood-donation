"""Drive reports & retrospectives; retro actions become tasks."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.security import Principal, gateway, require
from views import clean

router = APIRouter(prefix="/admin/reports", tags=["reports"])


@router.get("/{drive_id}")
def report(drive_id: str, user: Principal = Depends(require("reports")), gw=Depends(gateway)):
    if gw.one(gc.event_report.EVENT_REPORTS, drive_id) is None:
        gw.command(gc.event_report.REQUESTS, gc.event_report.SERVICE, {"action": "SNAPSHOT", "drive_id": drive_id})
    return clean(gw.one(gc.event_report.EVENT_REPORTS, drive_id))


@router.post("/{drive_id}/refresh")
def refresh(drive_id: str, user: Principal = Depends(require("reports")), gw=Depends(gateway)):
    gw.command(gc.event_report.REQUESTS, gc.event_report.SERVICE, {"action": "SNAPSHOT", "drive_id": drive_id})
    return clean(gw.one(gc.event_report.EVENT_REPORTS, drive_id))


@router.put("/{drive_id}/retro")
def retro(drive_id: str, body: dict, user: Principal = Depends(require("reports")), gw=Depends(gateway)):
    gw.command(gc.event_report.REQUESTS, gc.event_report.SERVICE, {"action": "SAVE_RETRO", "drive_id": drive_id, "actor_id": user.user_id, **body})
    return clean(gw.one(gc.event_report.EVENT_REPORTS, drive_id))


@router.post("/{drive_id}/actions-to-tasks")
def actions_to_tasks(drive_id: str, user: Principal = Depends(require("reports")), gw=Depends(gateway)):
    report = gw.one(gc.event_report.EVENT_REPORTS, drive_id) or {}
    made = [gw.command(gc.task.REQUESTS, gc.task.SERVICE, {"action": "CREATE", "title": line.strip(), "actor_id": user.user_id, "phase": "Follow-up",
                                                         "ref_type": "event", "ref_id": drive_id, "ref_label": report.get("title", "")}).fields["task_id"]
            for line in str(report.get("actions") or "").splitlines() if line.strip()]
    return {"created": len(made)}
