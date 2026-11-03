"""donor-service: saved donor groups and the Excel import review queue."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "donor_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("donor_requests", "donor-service", f)


def test_segments_should_save_and_delete(h):
    v = call(h, action="SAVE_SEGMENT", name="Rare groups", query="group=O-&group=AB-")
    assert h.read.accepted_one("donor_segments", v.fields["segment_id"])["query"] == "group=O-&group=AB-"
    assert call(h, action="SAVE_SEGMENT", name="").reason == "MISSING_NAME"
    assert call(h, action="DELETE_SEGMENT", segment_id=v.fields["segment_id"]).ok
    assert h.read.accepted_one("donor_segments", v.fields["segment_id"]) is None


def test_import_rows_should_stage_then_update(h):
    v = call(h, action="STAGE_IMPORT_ROW", batch="b1", row_no=2, row_status="error", data={"name": "Ann"}, errors={"email": "missing"})
    row_id = v.fields["row_id"]
    assert call(h, action="UPDATE_IMPORT_ROW", row_id=row_id, row_status="valid", data={"name": "Ann", "email": "ann@x.sg"}, errors={}).ok
    row = h.read.accepted_one("import_rows", row_id)
    assert (row["row_status"], row["data"]["email"], row["errors"]) == ("valid", "ann@x.sg", {})
    assert call(h, action="UPDATE_IMPORT_ROW", row_id="nope").reason == "UNKNOWN_ROW"


def test_creating_a_donor_is_no_longer_here(h):
    assert not call(h, action="CREATE", name="Ann Tan").ok
