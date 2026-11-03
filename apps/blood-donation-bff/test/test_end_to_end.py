"""End to end: the BFF over all 19 services on an in-memory Nexus — the donor journey and the staff journey."""
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from grepx_service.catalog import seed_catalog
from grepx_testkit.stack import start_stack
from grepx_storage import LocalStorage
from grepx_config import load_config

from grepx_bff.gateway import Gateway
from main import create_app

ROOT = Path(__file__).resolve().parents[3]
TODAY = date.today().isoformat()


def seed(stack) -> bool:
    """Load the product catalogue (templates, playbook, permissions, schedules) into the common services."""
    return all(seed_catalog(stack.requests, ROOT / "product-services/blood-donation/catalog").values())


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    stack = start_stack(ROOT)
    assert seed(stack)
    gw = Gateway(stack.client, load_config(ROOT / "apps/blood-donation-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    api = TestClient(create_app(gw))
    sign_up = lambda email, name: api.post("/api/v1/auth/register", json={"name": name, "email": email, "phone": "9123 4567", "password": "secret123",  # noqa: E731
                                                                         "blood_group": "O-", "sex": "Female", "dob": "1990-01-01"})
    admin = sign_up("admin@lifeflow.sg", "Ada Admin").json()
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": admin["user_id"], "role": "admin"}).ok
    return stack, api, sign_up, {"Authorization": f"Bearer {admin['token']}"}


def test_whole_journey(env):
    stack, api, sign_up, admin = env
    donor = sign_up("ann@x.sg", "Ann Tan")
    assert donor.status_code == 200, donor.text
    me = {"Authorization": f"Bearer {donor.json()['token']}"}
    assert sign_up("ann@x.sg", "Ann Again").json()["detail"]["reason"] == "EMAIL_TAKEN"

    created = api.post("/api/v1/admin/drives", headers=admin, json={"title": "Town Hall Drive", "venue": "Town Hall", "drive_date": TODAY,
                                                                    "slot_plan": {"start": "10:00", "end": "11:00", "minutes": 30, "capacity": 1},
                                                                    "apply_checklist": True})
    assert created.status_code == 200, created.text
    drive_id = created.json()["drive_id"]
    stack.settle()
    drive = api.get(f"/api/v1/drives/{drive_id}").json()
    assert [s["starts_at"] for s in drive["slots"]] == ["10:00", "10:30"] and drive["capacity"] == 2
    assert len(api.get(f"/api/v1/tasks?scope=all&ref={drive_id}", headers=admin).json()) == 28

    slot = drive["slots"][0]["id"]
    assert api.post(f"/api/v1/me/drives/{drive_id}/book", headers=me, json={}).json()["detail"]["reason"] == "SLOT_REQUIRED"
    assert api.post(f"/api/v1/me/drives/{drive_id}/book", headers=me, json={"slot_id": slot}).status_code == 200
    assert api.get("/api/v1/me/dashboard", headers=me).json()["registrations"][0]["slot_start"] == "10:00"

    found = api.post(f"/api/v1/drives/{drive_id}/kiosk/find", json={"contact": "ann@x.sg"}).json()
    assert found["name"] == "Ann T." and "••••" in found["phone"]
    assert api.post(f"/api/v1/admin/checkin/{drive_id}", headers=admin, json={"code": f"LIFEFLOW:DONOR:{found['donor_id']}"}).status_code == 200
    walk = api.post(f"/api/v1/admin/checkin/{drive_id}", headers=admin, json={"name": "Wally Walk", "phone": "8123 4567"})
    assert walk.status_code == 200, walk.text

    board = api.get(f"/api/v1/admin/drives/{drive_id}/board", headers=admin).json()["columns"]
    ann_reg = next(r for r in board["confirmed"] if r["donor_id"] == found["donor_id"])
    assert api.post(f"/api/v1/admin/registrations/{ann_reg['id']}/mark", headers=admin, json={"state": "donated"}).status_code == 200
    assert api.post(f"/api/v1/admin/drives/{drive_id}/complete", headers=admin, json={"voucher": {"title": "Free coffee", "code": "BLOOD1"}}).status_code == 200
    stack.settle()

    dash = api.get("/api/v1/me/dashboard", headers=me).json()
    assert dash["stats"]["count"] == 1 and dash["stats"]["badges"] == ["First Drop"]
    assert dash["vouchers"][0]["code"] == "BLOOD1" and len(dash["certificates"]) == 1
    assert api.get(f"/api/v1/certificates/{dash['certificates'][0]['id']}").json()["drive_title"] == "Town Hall Drive"

    report = api.get(f"/api/v1/admin/reports/{drive_id}", headers=admin).json()
    assert report["stats"]["donated"] == 1 and report["stats"]["no_show"] == 1 and report["stats"]["walk_ins"] == 1
    sent = {n["template"] for n in api.get("/api/v1/admin/messages/log", headers=admin).json()}
    assert {"welcome", "donation_thanks", "certificate"} <= sent


def test_permissions_and_public_tools(env):
    stack, api, sign_up, admin = env
    bob = sign_up("bob@x.sg", "Bob Lim").json()
    bob_h = {"Authorization": f"Bearer {bob['token']}"}
    assert api.post("/api/v1/admin/drives", headers=bob_h, json={}).status_code == 403
    assert api.get("/api/v1/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    check = api.post("/api/v1/eligibility/check", json={"dob": "1990-01-01", "sex": "Male", "weight": "40"}).json()
    assert check["eligible"] is False
    assert api.post("/api/v1/eligibility/chat", json={"message": ""}).json()["reply"]["reply"].startswith("Hi, I'm LifeBot")
    login = api.post("/api/v1/auth/login", json={"email": "bob@x.sg", "password": "wrong-pass"})
    assert login.status_code == 409 and login.json()["detail"]["message"] == "Wrong email or password."
    routes = api.get("/api/v1/gateway", headers=admin).json()
    assert {"auth-service", "event-service"} <= {r["service"] for r in routes}
    v = api.post("/api/v1/gateway/questionnaire-service/CHECK", headers=admin, json={"answers": {"dob": "1990-01-01", "weight": "60"}}).json()
    assert v["ok"] and v["fields"]["eligible"] is True


def test_trace_should_follow_one_request_across_services(env):
    stack, api, sign_up, admin = env
    created = api.post("/api/v1/admin/drives", headers={**admin, "X-Trace-Id": "trace-drive-1"},
                       json={"title": "Traced Drive", "venue": "Hall", "drive_date": TODAY, "apply_checklist": True,
                             "slot_plan": {"start": "09:00", "end": "10:00", "minutes": 30, "capacity": 2}})
    assert created.headers["X-Trace-Id"] == "trace-drive-1"
    stack.settle()
    report = api.get("/api/v1/admin/access/traces/trace-drive-1", headers=admin).json()
    assert report["ok"] and {"event-service", "slot-service", "checklist-service", "task-service"} <= set(report["services"])
    assert max(s["hop"] for s in report["steps"]) >= 2

    bad = api.post(f"/api/v1/me/drives/{created.json()['drive_id']}/book", headers={**admin, "X-Trace-Id": "trace-bad-1"}, json={})
    assert bad.json()["detail"]["trace_id"] == "trace-bad-1"
    failed = api.get("/api/v1/admin/access/traces/trace-bad-1", headers=admin).json()
    assert not failed["ok"] and failed["failures"][0]["service"] == "booking-service" and failed["failures"][0]["reason"] == "SLOT_REQUIRED"
