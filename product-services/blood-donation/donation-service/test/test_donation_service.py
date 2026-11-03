# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""donation-service: manual records, attendance reactions, stats/badges, eligible-again ticks."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from grepx_config import load_config
from nexus_testkit import MemoryClient

from domain import donor_status
from jobs import handle_booking, handle_tick
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "donation_requests", handle, cfg.live_criteria)
    harness.seed("people", "ann", {"name": "Ann Tan", "email": "ann@x.sg", "phone": "+6591234567"})
    harness.seed("events", "d1", {"title": "Town Hall", "event_date": "2026-01-10", "venue": "Hall"})
    return harness


def app(h):
    return NexusApplication(MemoryClient(h.engine), "x")


def stats(h):
    return h.read.accepted_one("donor_stats", "ann")


def test_status_rules():
    s = donor_status(["2026-01-01"], date(2026, 2, 1))
    assert s["days_left"] == 59 and not s["ready"] and s["badges"] == ["First Drop"] and s["next_eligible"] == "2026-04-01"
    assert donor_status([], date(2026, 1, 1))["first"] is True
    assert donor_status(["2025-01-01"] * 5, date(2026, 1, 1))["badges"][-1] == "Regular Hero"


def test_manual_record_should_update_stats(h):
    assert h.call("donation_requests", "donation-service", {"action": "RECORD", "donor_id": "ann", "donated_on": "2026-01-01"}).ok
    assert stats(h)["count"] == 1
    future = (date.today() + timedelta(days=3)).isoformat()
    assert h.call("donation_requests", "donation-service", {"action": "RECORD", "donor_id": "ann", "donated_on": future}).reason == "INVALID_DATE"


def test_attended_booking_should_record_a_donation_once_and_thank(h):
    reg = Row("d1-ann", {"status": "ACCEPTED", "state": "attended", "person_id": "ann", "event_id": "d1", "email": "ann@x.sg", "name": "Ann"})
    assert handle_booking(app(h), reg, cfg) == "recorded"
    assert handle_booking(app(h), reg, cfg) == "unchanged"
    assert stats(h)["last"] == "2026-01-10"
    assert [n["template"] for n in h.rows("notifications")] == ["donation_thanks"]


def test_leaving_attended_should_void(h):
    base = {"status": "ACCEPTED", "person_id": "ann", "event_id": "d1"}
    handle_booking(app(h), Row("d1-ann", {**base, "state": "attended"}), cfg)
    assert handle_booking(app(h), Row("d1-ann", {**base, "state": "confirmed"}), cfg) == "voided"
    assert stats(h)["count"] == 0


def test_eligible_again_tick(h):
    handle_booking(app(h), Row("d1-ann", {"status": "ACCEPTED", "state": "attended", "person_id": "ann", "event_id": "d1"}), cfg)
    sent = handle_tick(app(h), Row("t", {"status": "NEW", "job": "eligible-again"}), cfg, today=date(2026, 4, 10))
    assert sent == 1 and h.rows("notifications", template="eligible_again")
