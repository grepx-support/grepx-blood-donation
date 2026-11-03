# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Stage 3 - the original donor administration over all services (in-memory Nexus): grid + filters + paging, add a
donor, paste many, Excel import (stage -> fix -> commit), saved segments, bulk edit / message, export, donor profile
(edit, donation), users & passwords, volunteers & roles."""
import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from test_web_admin_drives import ROOT, Gateway, LocalStorage, create_app, load_config, seed, post, register, start_stack, token


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    stack = start_stack(ROOT)
    assert seed(stack)
    gw = Gateway(stack.client, load_config(ROOT / "apps/blood-donation-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    admin = TestClient(create_app(gw))
    register(admin, "Ada Admin", "ada@x.sg")
    ada = next(r for r in stack.client.select("people", "") if r.fields.get("email") == "ada@x.sg").key
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": ada, "role": "admin"}).ok
    return stack, admin


def donor(stack, email):
    return next((r for r in stack.client.select("people", "") if r.fields.get("email") == email), None)


def test_add_import_and_grid(site):
    stack, admin = site
    post(admin, "/admin/donors/", "/admin/donors/add", {"name": "Ann Tan", "email": "ann@x.sg", "phone": "91234567", "blood_group": "O-",
                                                        "sex": "Female", "weight": "55", "dob": "1990-01-01"})
    assert donor(stack, "ann@x.sg") is not None

    wb = Workbook(); ws = wb.active
    ws.append(["Name", "Email", "Phone", "Blood Group", "Sex", "Weight (kg)", "Date of Birth"])
    ws.append(["Bob Lim", "bob@x.sg", "92345678", "A+", "Male", 70, "1985-03-03"])
    ws.append(["No Email", "", "93456789", "B+", "Male", 70, "1985-03-03"])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    up = admin.post("/admin/import/upload", data={"csrf_token": token(admin.get("/admin/import/").text)},
                    files={"file": ("donors.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert "/admin/import/" in str(up.url), up.text[:300]
    batch = str(up.url).rstrip("/").split("/")[-1]
    rows = sorted((r for r in stack.client.select("import_rows", "") if r.fields.get("batch") == batch), key=lambda r: r.fields["row_no"])
    assert [r.fields["row_status"] for r in rows] == ["valid", "error"]
    post(admin, f"/admin/import/{batch}", f"/admin/import/{batch}/fix/{rows[1].key}",
         {"name": "No Email", "email": "noemail@x.sg", "phone": "93456789", "blood_group": "B+", "sex": "Male", "weight": "70", "dob": "1985-03-03"})
    post(admin, f"/admin/import/{batch}", f"/admin/import/{batch}/commit")
    assert donor(stack, "bob@x.sg") and donor(stack, "noemail@x.sg")

    grid = admin.get("/admin/donors/rows?group=O-").text
    assert "Ann Tan" in grid and "Bob Lim" not in grid
    assert "Bob Lim" in admin.get("/admin/donors/rows?q=bob").text
    xlsx = admin.get("/admin/donors/export.xlsx")
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"


def test_segments_bulk_and_profile(site):
    stack, admin = site
    post(admin, "/admin/donors/", "/admin/donors/segments", {"name": "Rare O-", "qs": "group=O-"})
    seg = next(r for r in stack.client.select("donor_segments", "") if r.fields.get("name") == "Rare O-")
    assert "Rare O-" in admin.get("/admin/donors/").text
    post(admin, "/admin/donors/", f"/admin/donors/segments/{seg.key}/delete")
    assert not [r for r in stack.client.select("donor_segments", "") if r.fields.get("name") == "Rare O-"]

    bob = donor(stack, "bob@x.sg").key
    post(admin, "/admin/donors/", "/admin/donors/bulk/edit", {"ids": bob, "blood_group": "AB+", "sex": "__keep__", "role": "__keep__"})
    assert donor(stack, "bob@x.sg").fields["blood_group"] == "AB+"
    before = len(stack.client.select("notifications", ""))
    post(admin, "/admin/donors/", "/admin/donors/bulk/message", {"ids": bob, "channels": "email", "subject": "Hello", "message": "Thanks!"})
    assert len(stack.client.select("notifications", "")) > before

    page = admin.get(f"/admin/donors/{bob}")
    assert page.status_code == 200 and "Bob Lim" in page.text
    post(admin, f"/admin/donors/{bob}", f"/admin/donors/{bob}/donation", {"donated_on": "2026-01-15"})
    assert any(d.fields.get("donor_id") == bob for d in stack.client.select("donations", ""))
    post(admin, f"/admin/donors/{bob}", f"/admin/donors/{bob}/edit", {"name": "Bob Lim Jr", "email": "bob@x.sg", "phone": "92345678",
                                                                       "blood_group": "AB+", "sex": "Male", "weight": "71", "dob": "1985-03-03"})
    assert donor(stack, "bob@x.sg").fields["name"] == "Bob Lim Jr"


def test_users_staff_and_roles(site):
    stack, admin = site
    assert admin.get("/admin/users/").status_code == 200 and admin.get("/admin/staff/").status_code == 200
    post(admin, "/admin/staff/", "/admin/staff/roles", {"name": "Desk team", "description": "check-in", "perm": ["checkin"]})
    role = next(r for r in stack.client.select("staff_roles", "") if r.fields.get("name") == "Desk team")
    post(admin, "/admin/staff/", "/admin/staff/new", {"name": "Vic Vol", "email": "vic@x.sg", "phone": "94567890", "role": "volunteer",
                                                      "staff_role_id": role.key, "password": "volunteer1"})
    vic = donor(stack, "vic@x.sg")
    assert vic is not None
    access = next(r for r in stack.client.select("user_access", "") if r.key == vic.key).fields
    assert access["role"] == "volunteer" and access["staff_role_id"] == role.key

    vol = TestClient(admin.app)
    page = vol.get("/login").text
    assert "/admin" in str(vol.post("/login", data={"csrf_token": token(page), "email": "vic@x.sg", "password": "volunteer1"}).url)

    post(admin, "/admin/users/", f"/admin/users/{vic.key}/password", {"password": "newpass123"})
    vol2 = TestClient(admin.app)
    page = vol2.get("/login").text
    assert "/admin" in str(vol2.post("/login", data={"csrf_token": token(page), "email": "vic@x.sg", "password": "newpass123"}).url)
