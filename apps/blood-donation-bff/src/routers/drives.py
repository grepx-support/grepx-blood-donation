"""Interest (public), kiosk self check-in (public), and staff drive management / check-in desk."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends, UploadFile

from grepx_bff.errors import ApiError
from grepx_bff.security import Principal, gateway, require
from views import clean, drive_view, mask_phone
from .me import store_upload

router = APIRouter(tags=["drives"])
REG, REG_SVC, DRV, DRV_SVC = gc.booking.REQUESTS, gc.booking.SERVICE, gc.event.REQUESTS, gc.event.SERVICE


@router.post("/drives/{drive_id}/interest")
def interest(drive_id: str, body: dict, gw=Depends(gateway)):
    return gw.command(REG, REG_SVC, {"action": "INTEREST", "drive_id": drive_id, **{k: body.get(k, "") for k in ("name", "phone", "email")}}).fields


@router.post("/drives/{drive_id}/kiosk/find")
def kiosk_find(drive_id: str, body: dict, gw=Depends(gateway)):
    gw.limit(f"kiosk:{drive_id}", rate=30, per=60)
    contact = str(body.get("contact", "")).strip()
    donors = gw.rows(gc.people.PEOPLE, email=contact.lower()) if "@" in contact else [d for d in gw.rows(gc.people.PEOPLE) if d.get("phone", "")[-8:] == "".join(c for c in contact if c.isdigit())[-8:]]
    if len(donors) != 1:
        raise ApiError("NOT_FOUND", 404)
    d = donors[0]
    parts = d.get("name", "").split()
    return {"donor_id": d["_key"], "name": f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else parts[0], "phone": mask_phone(d.get("phone", "")),
            "blood_group": d.get("blood_group", ""), "photo_id": d.get("photo_id", "")}


@router.post("/drives/{drive_id}/kiosk/checkin")
def kiosk_checkin(drive_id: str, body: dict, gw=Depends(gateway)):
    return gw.command(REG, REG_SVC, {"action": "CHECK_IN", "drive_id": drive_id, "donor_id": body.get("donor_id", ""), "source": "kiosk"}).fields


@router.post("/drives/{drive_id}/kiosk/register")
def kiosk_register(drive_id: str, body: dict, gw=Depends(gateway)):
    return walk_in(drive_id, body, gw, source="kiosk")


def walk_in(drive_id: str, body: dict, gw, source: str = "walkin") -> dict:
    email = str(body.get("email", "")).strip().lower()
    phone8 = "".join(c for c in str(body.get("phone", "")) if c.isdigit())[-8:]
    found = (gw.rows(gc.people.PEOPLE, email=email) if email else []) or [d for d in gw.rows(gc.people.PEOPLE) if phone8 and d.get("phone", "")[-8:] == phone8]
    donor_id = found[0]["_key"] if found else gw.command(gc.people.REQUESTS, gc.people.SERVICE, {
        "action": "CREATE", "source": source, "allow_no_email": True, **{k: body.get(k, "") for k in ("name", "phone", "email", "blood_group", "sex")}}).fields["donor_id"]
    return gw.command(REG, REG_SVC, {"action": "CHECK_IN", "drive_id": drive_id, "donor_id": donor_id, "source": source}).fields


# ---- staff ----
@router.post("/admin/drives")
def create_drive(body: dict, user: Principal = Depends(require("manage_drives")), gw=Depends(gateway)):
    assignee = gw.one(gc.people.PEOPLE, body.get("assignee_id", ""))
    extra = {"assignee": {"id": assignee["_key"], "name": assignee.get("name", ""), "email": assignee.get("email", ""), "phone": assignee.get("phone", "")}} if assignee else {}
    return gw.command(DRV, DRV_SVC, {"action": "CREATE", "actor_id": user.user_id, **body, **extra}).fields


@router.patch("/admin/drives/{drive_id}")
def update_drive(drive_id: str, body: dict, user: Principal = Depends(require("manage_drives")), gw=Depends(gateway)):
    return gw.command(DRV, DRV_SVC, {"action": "UPDATE", "drive_id": drive_id, **body}).fields


@router.post("/admin/drives/{drive_id}/{op}")
def drive_op(drive_id: str, op: str, body: dict, user: Principal = Depends(require("manage_drives")), gw=Depends(gateway)):
    """op: clone | complete | reopen | images | rewards | checklist | slots | slot-capacity | all-capacity | announce | invite"""
    if op == "clone":
        return gw.command(DRV, DRV_SVC, {"action": "CLONE", "source_drive_id": drive_id, "actor_id": user.user_id, **body}).fields
    if op in ("complete", "reopen"):
        return gw.command(DRV, DRV_SVC, {"action": op.upper(), "drive_id": drive_id, "actor_id": user.user_id, **body}).fields
    if op == "images":
        return gw.command(DRV, DRV_SVC, {"action": "SET_IMAGES", "drive_id": drive_id, "images": body.get("images", [])}).fields
    if op == "rewards":
        return gw.command(gc.recognition.REQUESTS, gc.recognition.SERVICE, {"action": "ISSUE", "drive_id": drive_id, "voucher": body}).fields
    if op == "checklist":
        d = gw.one(gc.event.EVENTS, drive_id) or {}
        action = "REMOVE" if body.get("remove") else "APPLY"
        return gw.command(gc.checklist.REQUESTS, gc.checklist.SERVICE, {"action": action, "template_key": "blood-drive-playbook", "ref_type": "event",
                                                                      "ref_id": drive_id, "ref_label": d.get("title", ""), "base_date": d.get("drive_date", ""),
                                                                      "only_open": body.get("only_open", False), "actor_id": user.user_id}).fields
    if op == "slots":
        return gw.command(gc.slot.REQUESTS, gc.slot.SERVICE, {"action": "GENERATE", "drive_id": drive_id, "plan": body}).fields
    if op == "slot-capacity":
        return gw.command(gc.slot.REQUESTS, gc.slot.SERVICE, {"action": "SET_CAPACITY", **body}).fields
    if op == "all-capacity":
        return gw.command(gc.slot.REQUESTS, gc.slot.SERVICE, {"action": "SET_ALL", "drive_id": drive_id, "value": body.get("value")}).fields
    if op in ("announce", "invite"):
        if not user.can("notify"):
            raise ApiError("FORBIDDEN", 403)
        return gw.command(gc.campaign.REQUESTS, gc.campaign.SERVICE, {"action": op.upper(), "drive_id": drive_id, "actor_id": user.user_id, **body}).fields
    raise ApiError("UNKNOWN_OPERATION", 404)


@router.post("/admin/drives/{drive_id}/pictures")
def upload_picture(drive_id: str, file: UploadFile, user: Principal = Depends(require("manage_drives")), gw=Depends(gateway)):
    media_id = store_upload(gw, file, "picture", user.user_id)
    images = list((gw.one(gc.event.EVENTS, drive_id) or {}).get("images") or []) + [media_id]
    return gw.command(DRV, DRV_SVC, {"action": "SET_IMAGES", "drive_id": drive_id, "images": images}).fields


@router.get("/admin/drives/{drive_id}/board")
def board(drive_id: str, user: Principal = Depends(require()), gw=Depends(gateway)):
    d = gw.one(gc.event.EVENTS, drive_id)
    if d is None:
        raise ApiError("UNKNOWN_DRIVE", 404)
    columns = {s: [] for s in ("interested", "confirmed", "donated", "no_show", "not_eligible")}
    for r in gw.rows(gc.booking.BOOKINGS, drive_id=drive_id):
        if r.get("state") in columns:
            columns[r["state"]].append(clean(r))
    return {"drive": drive_view(gw, d), "columns": columns}


@router.post("/admin/registrations/{registration_id}/{op}")
def registration_op(registration_id: str, op: str, body: dict, user: Principal = Depends(require("checkin")), gw=Depends(gateway)):
    """op: mark {state} | move {slot_id}"""
    if op == "mark":
        return gw.command(REG, REG_SVC, {"action": "MARK", "registration_id": registration_id, "state": body.get("state")}).fields
    if op == "move":
        return gw.command(REG, REG_SVC, {"action": "MOVE", "registration_id": registration_id, "slot_id": body.get("slot_id"),
                                         "override_capacity": user.is_admin}).fields
    raise ApiError("UNKNOWN_OPERATION", 404)


@router.post("/admin/checkin/{drive_id}")
def desk_checkin(drive_id: str, body: dict, user: Principal = Depends(require("checkin")), gw=Depends(gateway)):
    """Desk: {donor_id} from search, {code: 'LIFEFLOW:DONOR:<id>'} from the QR scanner, or walk-in details."""
    code = str(body.get("code", ""))
    donor_id = code.split(":", 2)[2] if code.startswith("LIFEFLOW:DONOR:") else body.get("donor_id", "")
    if donor_id:
        return gw.command(REG, REG_SVC, {"action": "CHECK_IN", "drive_id": drive_id, "donor_id": donor_id, "source": "desk"}).fields
    return walk_in(drive_id, body, gw)
