# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Stage 2 - the original admin drive pages over all services (in-memory Nexus): create with slots, edit, board,
attendance, walk-ins, kiosk, scan, slot moves and capacity, announce, invite, complete (certificates + vouchers),
reopen, clone."""
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from test_end_to_end import ROOT, Gateway, LocalStorage, create_app, load_config, seed, start_stack

TODAY = date.today().isoformat()


def token(html: str) -> str:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html) or re.search(r'name="csrf-token" content="([^"]+)"', html)
    return m.group(1) if m else ""


def post(web, page_path, url, data=None, **kw):
    return web.post(url, data={"csrf_token": token(web.get(page_path).text), **(data or {})}, **kw)


def register(web, name, email, group="O+"):
    return post(web, "/register", "/register", {"name": name, "email": email, "phone": "9" + str(abs(hash(email)))[:7], "password": "secret123",
                                                "password2": "secret123", "blood_group": group, "sex": "female", "weight": "60", "dob": "1990-01-01"})


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    stack = start_stack(ROOT)
    assert seed(stack)
    gw = Gateway(stack.client, load_config(ROOT / "apps/blood-donation-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    app = create_app(gw)
    admin, donor = TestClient(app), TestClient(app)
    register(admin, "Ada Admin", "ada@x.sg")
    ada = next(r for r in stack.client.select("people", "") if r.fields.get("email") == "ada@x.sg").key
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": ada, "role": "admin"}).ok
    register(donor, "Dee Donor", "dee@x.sg", "A-")
    return stack, admin, donor


def test_admin_drive_lifecycle(site):
    stack, admin, donor = site
    assert admin.get("/admin/").status_code == 200
    assert admin.get("/admin/drives/").status_code == 200

    made = post(admin, "/admin/drives/new", "/admin/drives/new", {
        "title": "Town Hall Drive", "venue": "Town Hall", "drive_date": TODAY, "description": "Bring ID", "use_slots": "1",
        "slot_start": "10:00", "slot_end": "11:00", "slot_minutes": "30", "slot_capacity": "1", "add_checklist": "1"})
    assert made.status_code == 200 and "/admin/drives/" in str(made.url), made.text[:300]
    drive_id = str(made.url).rstrip("/").split("/")[-1]
    page = admin.get(f"/admin/drives/{drive_id}")
    assert page.status_code == 200 and "Town Hall Drive" in page.text
    slots = sorted((r for r in stack.client.select("slots", "") if r.fields.get("event_id") == drive_id), key=lambda r: r.fields["starts_at"])
    assert [s.fields["starts_at"] for s in slots] == ["10:00", "10:30"]
    assert any(t.fields.get("ref_id") == drive_id for t in stack.client.select("tasks", "")), "checklist tasks created"

    r = post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/edit",
             {"title": "Town Hall Drive", "venue": "Town Hall, Level 2", "drive_date": TODAY, "description": "Bring ID"})
    assert "Level 2" in r.text

    # a donor books the 10:00 slot; the slot is then full for others
    page = donor.get(f"/drive/{drive_id}").text
    donor.post(f"/drive/{drive_id}/confirm", data={"csrf_token": token(page), "slot_id": slots[0].key})
    reg = next(r for r in stack.client.select("bookings", "") if r.fields.get("event_id") == drive_id)
    assert reg.fields["state"] == "confirmed" and reg.fields["slot_id"] == slots[0].key

    # admin moves her to 10:30, raises capacity, then the board marks her donated (drive day)
    post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/people/{reg.key}/slot", {"slot_id": slots[1].key})
    assert next(r for r in stack.client.select("bookings", "") if r.key == reg.key).fields["slot_id"] == slots[1].key
    post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/slots/{slots[0].key}/capacity", {"value": "3"})
    assert next(s for s in stack.client.select("slots", "") if s.key == slots[0].key).fields["capacity"] == 3
    csrf = token(admin.get(f"/admin/drives/{drive_id}").text)
    moved = admin.post("/admin/drives/move", json={"id": reg.key, "status": "donated"}, headers={"X-CSRFToken": csrf})
    assert moved.status_code == 200, moved.text
    assert any(d.fields.get("donor_id") == reg.fields["person_id"] for d in stack.client.select("donations", "")), "donation recorded"

    # check-in desk: walk-in registration, and the kiosk
    assert admin.get(f"/admin/checkin/?drive={drive_id}").status_code == 200
    post(admin, f"/admin/checkin/?drive={drive_id}", f"/admin/checkin/{drive_id}/walkin",
         {"name": "Walt Walker", "phone": "98887777", "email": "walt@x.sg", "blood_group": "B+", "sex": "male", "weight": "70", "dob": "1985-05-05"})
    assert any(r.fields.get("name") == "Walt Walker" and r.fields.get("state") == "confirmed" for r in stack.client.select("bookings", ""))
    kiosk = TestClient(admin.app)
    page = kiosk.get(f"/drive/{drive_id}/here/").text
    kiosk.post(f"/drive/{drive_id}/here/new", data={"csrf_token": token(page), "name": "Kim Kiosk", "phone": "96665555", "email": "",
                                                     "blood_group": "O-", "sex": "female", "weight": "52", "dob": "2000-02-02"})
    assert any(r.fields.get("name") == "Kim Kiosk" for r in stack.client.select("bookings", ""))

    # announce + invite (messages go through notification-service)
    sent_before = len(stack.client.select("notifications", ""))
    post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/notify", {"audience": "donor", "channels": "email"})
    assert len(stack.client.select("notifications", "")) > sent_before
    page = admin.get(f"/admin/drives/{drive_id}/invite?group=A-")
    assert page.status_code == 200 and "Dee Donor" in page.text
    dee = next(r for r in stack.client.select("people", "") if r.fields.get("email") == "dee@x.sg").key
    before = len(stack.client.select("notifications", ""))
    post(admin, f"/admin/drives/{drive_id}/invite", f"/admin/drives/{drive_id}/invite", {"donor": dee, "channels": "email", "note": "Hope to see you"})
    assert any(n.fields.get("recipient") == "dee@x.sg" and "Hope to see you" in str(n.fields.get("values"))
               for n in stack.client.select("notifications", "")[before - 1:]) or len(stack.client.select("notifications", "")) > before

    # complete: certificates + vouchers by recognition-service; then reopen; then clone
    done = post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/complete",
                {"close_open": "1", "notify": "1", "voucher_on": "1", "voucher_title": "Free coffee", "voucher_shared": "COFFEE"})
    assert "Drive completed" in done.text, done.text[:400]
    assert any(c.fields.get("event_id") == drive_id for c in stack.client.select("certificates", ""))
    assert any(v.fields.get("code") == "COFFEE" for v in stack.client.select("vouchers", ""))
    cert = next(c for c in stack.client.select("certificates", "") if c.fields.get("event_id") == drive_id)
    assert TestClient(admin.app).get(f"/certificate/{cert.key}").status_code == 200
    assert "Dee Donor" in donor.get("/dashboard").text and "Free coffee" in donor.get("/dashboard").text

    post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/reopen")
    assert next(d for d in stack.client.select("events", "") if d.key == drive_id).fields["state"] == "open"
    copy = post(admin, f"/admin/drives/{drive_id}", f"/admin/drives/{drive_id}/clone", {"drive_date": "2031-01-01", "copy_slots": "1"})
    new_id = str(copy.url).rstrip("/").split("/")[-1]
    assert new_id != drive_id and len([s for s in stack.client.select("slots", "") if s.fields.get("event_id") == new_id]) == 2
