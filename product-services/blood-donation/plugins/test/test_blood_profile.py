"""Blood donor fields on the person record (people-service profile plugin), and people-service using it."""
from datetime import date
from pathlib import Path

import pytest
from grepx_testkit.harness import load_service, ServiceHarness

import blood_profile

ROOT = Path(__file__).resolve().parents[4]
TODAY = date(2026, 1, 1)


def test_values_are_normalised():
    assert blood_profile.clean({"blood_group": "o-", "sex": "female", "weight": "60", "dob": "1990-05-01"}, today=TODAY) == \
        {"blood_group": "O-", "sex": "Female", "weight": 60.0, "dob": "1990-05-01"}
    assert blood_profile.clean({}) == {}                       # staff and walk-ins may not know them


@pytest.mark.parametrize("field,value,reason", [("blood_group", "C+", "INVALID_BLOOD_GROUP"), ("sex", "x", "INVALID_SEX"),
                                                ("weight", "500", "INVALID_WEIGHT"), ("weight", "heavy", "INVALID_WEIGHT"),
                                                ("dob", "2015-01-01", "INVALID_AGE"), ("dob", "soon", "INVALID_AGE")])
def test_bad_values_reject_with_reason(field, value, reason):
    with pytest.raises(ValueError, match=reason):
        blood_profile.clean({field: value}, today=TODAY)


def test_people_service_stores_the_blood_fields():
    handle, cfg, _ = load_service(ROOT / "common-services" / "people-service",
                                  {"plugins": {"path": "product-services/blood-donation/plugins", "profile": "blood_profile"},
                                   "workspace": str(ROOT)})
    h = ServiceHarness().add(cfg, "people_requests", handle, cfg.live_criteria)
    ann = {"action": "CREATE", "name": "Ann Tan", "email": "ann@x.sg", "phone": "9123 4567", "blood_group": "o-", "weight": "60"}
    v = h.call("people_requests", "people-service", ann)
    person = h.read.accepted_one("people", v.fields["person_id"])
    assert (person["blood_group"], person["weight"], person["phone"]) == ("O-", 60.0, "+6591234567")
    assert h.call("people_requests", "people-service", {**ann, "email": "bob@x.sg", "blood_group": "C+"}).reason == "INVALID_BLOOD_GROUP"
    assert h.call("people_requests", "people-service", {"action": "UPDATE", "person_id": v.fields["person_id"], "weight": "500"}).reason \
        == "INVALID_WEIGHT"
