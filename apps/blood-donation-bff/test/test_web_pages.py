"""The original LifeFlow web pages, served by the BFF over all services on an in-memory Nexus (stage 1: public + donor)."""
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from test_end_to_end import ROOT, Gateway, LocalStorage, create_app, load_config, seed, start_stack

TODAY = date.today().isoformat()


def token(html: str) -> str:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else ""


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    stack = start_stack(ROOT)
    assert seed(stack)
    gw = Gateway(stack.client, load_config(ROOT / "apps/blood-donation-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    web = TestClient(create_app(gw))
    drive = stack.call("event_requests", "event-service", {"action": "CREATE", "title": "Town Hall Drive", "venue": "Town Hall",
                                                           "event_date": TODAY, "capacity": 50})
    assert drive.ok
    return web, drive.fields["event_id"]


def test_public_pages_render(site):
    web, drive_id = site
    for path in ("/", "/eligibility", "/login", "/register", f"/drive/{drive_id}"):
        page = web.get(path)
        assert page.status_code == 200, (path, page.text[:300])
    assert "Town Hall Drive" in web.get("/").text


def test_donor_journey_through_the_original_pages(site):
    web, drive_id = site
    form = web.get("/register").text
    done = web.post("/register", data={"csrf_token": token(form), "name": "Ann Tan", "email": "ann@x.sg", "phone": "91234567",
                                       "password": "secret123", "password2": "secret123", "blood_group": "O-", "sex": "female",
                                       "weight": "55", "dob": "1990-01-01"})
    assert done.status_code == 200 and "/dashboard" in str(done.url), done.text[:300]
    assert "Ann" in done.text

    page = web.get(f"/drive/{drive_id}").text
    web.post(f"/drive/{drive_id}/confirm", data={"csrf_token": token(page)})
    assert "Town Hall Drive" in web.get("/dashboard").text.split("My upcoming drives", 1)[1][:4000]

    page = web.get(f"/drive/{drive_id}").text
    web.post(f"/drive/{drive_id}/cancel", data={"csrf_token": token(page)})
    assert "No drives yet" in web.get("/dashboard").text

    web.get("/logout")
    page = web.get("/login").text
    bad = web.post("/login", data={"csrf_token": token(page), "email": "ann@x.sg", "password": "wrong-one"})
    assert "/login" in str(bad.url)
    good = web.post("/login", data={"csrf_token": token(web.get("/login").text), "email": "ann@x.sg", "password": "secret123"})
    assert "/dashboard" in str(good.url)


def test_eligibility_check_page(site):
    web, _ = site
    page = web.get("/eligibility").text
    result = web.post("/eligibility", data={"csrf_token": token(page), "age": "30", "weight": "60", "sex": "female"})
    assert result.status_code == 200


def test_lifebot_chat_goes_through_eligibility_service(site):
    web, _ = site
    page = web.get("/").text
    reply = web.post("/api/chat", json={"message": "__start__"}, headers={"X-CSRFToken": token(page)})
    assert reply.status_code == 200 and "LifeBot" in reply.json()["reply"]


def test_google_button_only_when_set_up_and_finish_page_needs_a_google_sign_in(site):
    web, _ = site
    web.get("/logout")
    assert "Continue with Google" not in web.get("/login").text
    assert "/login" in str(web.get("/login/google").url)                  # not set up: back to the login page
    assert "/register" in str(web.get("/register/google").url)            # no Google sign-in in progress
    assert "/login" in str(web.get("/login/google/callback?state=forged&code=x").url)


def test_google_set_up_shows_the_button_and_the_finish_form(site, monkeypatch):
    web, _ = site
    monkeypatch.setattr("integrations.sign_in.setting", lambda key, default="": "cid.apps.googleusercontent.com")
    monkeypatch.setattr("routes.google_login.google_enabled", lambda: True)
    start = web.get("/login/google", follow_redirects=False)
    assert start.status_code == 302 and start.headers["location"].startswith("https://accounts.google.com/")
    assert "redirect_uri=http%3A%2F%2Ftestserver%2Flogin%2Fgoogle%2Fcallback" in start.headers["location"]
