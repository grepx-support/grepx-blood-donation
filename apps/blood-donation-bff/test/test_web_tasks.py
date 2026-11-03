# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Stage 4 - planning: the original task pages over task-service (in-memory Nexus): create / assign, my tasks,
claim, drag between columns, edit, delete, bulk delete, the calendar feed, the drive checklist."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from test_web_admin_drives import ROOT, Gateway, LocalStorage, create_app, load_config, seed, post, register, start_stack, token


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    stack = start_stack(ROOT)
    assert seed(stack)
    gw = Gateway(stack.client, load_config(ROOT / "apps/blood-donation-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    app = create_app(gw)
    admin, vol = TestClient(app), TestClient(app)
    register(admin, "Ada Admin", "ada@x.sg")
    register(vol, "Vic Vol", "vic@x.sg")
    people = {r.fields["email"]: r.key for r in stack.client.select("people", "")}
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": people["ada@x.sg"], "role": "admin"}).ok
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": people["vic@x.sg"], "role": "volunteer"}).ok
    drive = stack.call("event_requests", "event-service", {"action": "CREATE", "title": "Library Drive", "venue": "Library",
                                                           "event_date": date.today().isoformat()}).fields["event_id"]
    return stack, admin, vol, people, drive


def tasks(stack, **eq):
    return [t for t in stack.client.select("tasks", "") if t.fields.get("status") == "ACCEPTED" and all(t.fields.get(k) == v for k, v in eq.items())]


def test_planning(site):
    stack, admin, vol, people, drive = site
    assert admin.get("/admin/tasks/").status_code == 200
    post(admin, "/admin/tasks/", "/admin/tasks/", {"title": "Book the hall", "description": "Call the library", "due_at": "2031-01-10T10:00",
                                                   "assignee_id": people["vic@x.sg"], "drive_id": drive, "important": "1", "status": "todo"})
    hall = tasks(stack, title="Book the hall")[0]
    assert (hall.fields["assignee_id"], hall.fields["ref_id"], hall.fields["important"]) == (people["vic@x.sg"], drive, True)
    assert any(n.fields.get("template") == "task_assigned" for n in stack.client.select("notifications", ""))
    post(admin, "/admin/tasks/", "/admin/tasks/", {"title": "Print posters", "assignee_id": "none", "status": "todo"})

    assert "Book the hall" in vol.get("/dashboard").text
    post(vol, "/dashboard", f"/my-tasks/{hall.key}/status", {"status": "in_progress"})
    assert tasks(stack, title="Book the hall")[0].fields["state"] == "in_progress"

    posters = tasks(stack, title="Print posters")[0]
    post(vol, "/admin/tasks/", f"/admin/tasks/{posters.key}/claim")
    assert tasks(stack, title="Print posters")[0].fields["assignee_id"] == people["vic@x.sg"]

    csrf = token(admin.get("/admin/tasks/").text)
    assert admin.post("/admin/tasks/move", json={"id": hall.key, "status": "done"}, headers={"X-CSRFToken": csrf}).status_code == 200
    assert tasks(stack, title="Book the hall")[0].fields["state"] == "done"
    post(admin, "/admin/tasks/", f"/admin/tasks/{hall.key}", {"title": "Book the hall (confirmed)", "assignee_id": people["vic@x.sg"],
                                                               "drive_id": drive, "status": "done"})
    assert tasks(stack, title="Book the hall (confirmed)")
    events = admin.get("/admin/tasks/events.json")
    assert events.status_code == 200 and "Book the hall" in events.text

    post(admin, "/admin/tasks/", f"/admin/tasks/{posters.key}/delete")
    assert not tasks(stack, title="Print posters")
    post(admin, f"/admin/drives/{drive}", f"/admin/drives/{drive}/checklist")
    added = tasks(stack, ref_id=drive)
    assert len(added) > 5
    post(admin, "/admin/tasks/", f"/admin/tasks/checklist/{drive}/remove", {"which": "all"})
    assert len(tasks(stack, ref_id=drive)) == 1          # only the hand-made task stays
    ids = ",".join(t.key for t in tasks(stack, ref_id=drive))
    post(admin, "/admin/tasks/", "/admin/tasks/bulk-delete", {"ids": ids})
    assert not tasks(stack, ref_id=drive)
