"""Blood donor fields on the generic person record, loaded by people-service (deployment.yaml plugins.profile). Pure.

Plugin interface:  FIELDS = (...)   the product's own person fields
                   clean(raw, partial) -> dict   validated values; raises ValueError(<REASON_CODE>)
Same limits the original site enforced: blood group, sex, weight 30-250 kg, age 16-75.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
SEXES = ("Male", "Female")
WEIGHT_MIN, WEIGHT_MAX, AGE_MIN, AGE_MAX = 30, 250, 16, 75
FIELDS = ("blood_group", "sex", "weight", "dob")


def _age(dob: date, today: date) -> int:
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _today() -> date:
    try:
        from grepx_service import local_today
        return local_today()
    except ImportError:
        return date.today()


def clean(raw: dict, partial: bool = False, today: Optional[date] = None) -> dict:
    """Every field is optional (staff and walk-ins may not know them); present values must be valid."""
    out, has = {}, (lambda k: k in raw and raw[k] not in (None, ""))  # noqa: E731
    if "blood_group" in raw:
        group = str(raw.get("blood_group") or "").strip().upper()
        if group and group not in BLOOD_GROUPS:
            raise ValueError("INVALID_BLOOD_GROUP")
        out["blood_group"] = group
    if has("sex"):
        sex = str(raw["sex"]).strip().capitalize()
        if sex not in SEXES:
            raise ValueError("INVALID_SEX")
        out["sex"] = sex
    if has("weight"):
        try:
            weight = float(raw["weight"])
        except (TypeError, ValueError) as exc:
            raise ValueError("INVALID_WEIGHT") from exc
        if not WEIGHT_MIN <= weight <= WEIGHT_MAX:
            raise ValueError("INVALID_WEIGHT")
        out["weight"] = weight
    if has("dob"):
        try:
            dob = date.fromisoformat(str(raw["dob"]))
        except ValueError as exc:
            raise ValueError("INVALID_AGE") from exc
        if not AGE_MIN <= _age(dob, today or _today()) <= AGE_MAX:
            raise ValueError("INVALID_AGE")
        out["dob"] = dob.isoformat()
    return out
