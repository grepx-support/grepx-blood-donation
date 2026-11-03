"""Stage 5 - messages, automatic messages, integrations, analytics access and social publishing through the original
pages: notification-service delivers and logs, template-service holds the automatic-message settings, settings-service
holds integration settings (secrets sealed), campaign-service publishes to social networks."""
import pytest
from fastapi.testclient import TestClient

from test_web_admin_drives import ROOT, Gateway, LocalStorage, create_app, load_config, seed, post, register, start_stack


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


def rows(stack, table, **eq):
    return [r.fields for r in stack.client.select(table, "") if r.fields.get("status") == "ACCEPTED"
            and all(r.fields.get(k) == v for k, v in eq.items())]


def test_messages_and_broadcast(site):
    stack, admin = site
    assert admin.get("/admin/messages/").status_code == 200
    r = post(admin, "/admin/messages/", "/admin/messages/test", {"channel": "email"})
    assert "not set up yet" in r.text                     # as before: no SMTP saved yet, so nothing is attempted
    post(admin, "/admin/messages/", "/admin/messages/broadcast", {"audience": "admin", "channels": "email", "subject": "Team news",
                                                                 "message": "Drive on Saturday"})
    assert any("Team news" in str(n.get("values")) for n in rows(stack, "notifications"))
    assert "Team news" in admin.get("/admin/messages/").text   # the delivery log on the page


def test_automatic_messages_follow_admin_settings(site):
    stack, admin = site
    assert admin.get("/admin/messages/automatic/").status_code == 200
    post(admin, "/admin/messages/automatic/", "/admin/messages/automatic/welcome", {"channels": "email"})   # unticked = off
    assert rows(stack, "message_settings", template_key="welcome")[0]["enabled"] is False
    register(TestClient(admin.app), "Newbie Nee", "nee@x.sg")
    welcome = rows(stack, "notifications", template="welcome", recipient="nee@x.sg")
    assert welcome and welcome[0]["delivery"] == "SKIPPED"


def test_integrations_are_saved_sealed_and_used_by_notification_service(site):
    stack, admin = site
    assert admin.get("/admin/integrations/").status_code == 200
    post(admin, "/admin/integrations/", "/admin/integrations/email", {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": "1", "SMTP_USER": "me@x.sg",
                                                                       "SMTP_PASS": "hunter2", "SMTP_FROM": "me@x.sg"})
    saved = {r["name"]: r for r in rows(stack, "app_settings")}
    assert saved["SMTP_HOST"]["value"] == "127.0.0.1" and saved["SMTP_PASS"]["value"].startswith("enc:") and "hunter2" not in str(saved)
    r = post(admin, "/admin/messages/", "/admin/messages/test", {"channel": "email"})
    assert "failed" in r.text                             # notification-service now really tries the saved SMTP server
    test = rows(stack, "notifications", recipient="ada@x.sg", event="test")
    assert test and test[-1]["delivery"] == "FAILED" and test[-1]["error"]


def test_analytics_access_and_social(site):
    stack, admin = site
    assert admin.get("/admin/analytics/").status_code == 200
    post(admin, "/admin/analytics/access", "/admin/analytics/access", {})
    assert rows(stack, "app_settings", name="analytics.widget_access")
    drive = stack.call("event_requests", "event-service", {"action": "CREATE", "title": "Mall Drive", "venue": "Mall",
                                                           "event_date": "2031-02-02"}).fields["event_id"]
    post(admin, f"/admin/drives/{drive}", f"/admin/drives/{drive}/social", {"network": "facebook", "caption": "Join us"})
    posts = rows(stack, "social_posts", event_id=drive)
    assert posts and posts[0]["post_status"] == "failed" and "not set up" in posts[0]["error"]
    assert "not set up" in admin.get(f"/admin/drives/{drive}").text
