# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Stage 6 - drive reports and retros (event-report-service computes the numbers), analytics, the lesson shown when planning
the next drive, certificates."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from test_web_admin_drives import ROOT, Gateway, LocalStorage, create_app, load_config, seed, post, register, start_stack


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    stack = start_stack(ROOT)
    assert seed(stack)
    gw = Gateway(stack.client, load_config(ROOT / "apps/blood-donation-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    admin, donor = TestClient(create_app(gw)), None
    register(admin, "Ada Admin", "ada@x.sg")
    ada = next(r for r in stack.client.select("people", "") if r.fields.get("email") == "ada@x.sg").key
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": ada, "role": "admin"}).ok
    drive = stack.call("event_requests", "event-service", {"action": "CREATE", "title": "Harbour Drive", "venue": "Harbour",
                                                           "event_date": date.today().isoformat(), "capacity": 4}).fields["event_id"]
    for name, email, state in (("Ann Tan", "ann@x.sg", "donated"), ("Bob Lim", "bob@x.sg", "no_show"), ("Cat Ng", "cat@x.sg", "confirmed")):
        donor_id = stack.call("people_requests", "people-service", {"action": "CREATE", "name": name, "email": email, "phone": "91234567",
                                                                  "blood_group": "O-", "source": "staff"}).fields["person_id"]
        reg = stack.call("booking_requests", "booking-service", {"action": "CHECK_IN", "event_id": drive, "person_id": donor_id})
        if state != "confirmed":
            assert stack.call("booking_requests", "booking-service", {"action": "MARK", "booking_id": reg.fields["booking_id"],
                                                                                "state": {"donated": "attended"}.get(state, state)}).ok
    return stack, admin, drive


def test_report_retro_and_lessons(site):
    stack, admin, drive = site
    assert admin.get("/admin/reports/").status_code == 200
    page = admin.get(f"/admin/reports/{drive}")
    assert page.status_code == 200 and "Harbour Drive" in page.text
    stats = next(r for r in stack.client.select("event_reports", "") if r.key == drive).fields["stats"]
    assert (stats["registered"], stats["attended"], stats["no_show"], stats["show_rate"], stats["fill_rate"]) == (3, 1, 1, 33, 50)
    assert stats["blood_groups"] == {"O-": 1} and stats["event"]["title"] == "Harbour Drive"

    post(admin, f"/admin/reports/{drive}", f"/admin/reports/{drive}", {"went_well": "Great venue", "to_improve": "More signage",
                                                                       "actions": "Print signs", "notes": "", "rating": "4"})
    report = next(r for r in stack.client.select("event_reports", "") if r.key == drive).fields
    assert (report["went_well"], report["rating"]) == ("Great venue", 4)
    assert "More signage" in admin.get("/admin/drives/new").text          # the lesson shows when planning the next drive
    post(admin, f"/admin/reports/{drive}", f"/admin/reports/{drive}/refresh")
    post(admin, f"/admin/reports/{drive}", f"/admin/reports/{drive}/task", {"title": "Print signs"})
    assert any(t.fields.get("title") == "Print signs" for t in stack.client.select("tasks", ""))
    xlsx = admin.get(f"/admin/reports/{drive}/export.xlsx")
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"


def test_analytics_and_certificate(site):
    stack, admin, drive = site
    assert admin.get("/admin/analytics/").status_code == 200
    done = post(admin, f"/admin/drives/{drive}", f"/admin/drives/{drive}/complete", {"close_open": "1", "notify": "1"})
    assert "Drive completed" in done.text
    cert = next(c for c in stack.client.select("certificates", "") if c.fields.get("event_id") == drive)
    public = TestClient(admin.app)
    assert "Ann Tan" in public.get(f"/certificate/{cert.key}").text
    png = public.get(f"/certificate/{cert.key}.png")
    assert png.status_code == 200 and png.content[:4] == b"\x89PNG"
