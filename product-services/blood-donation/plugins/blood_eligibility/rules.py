# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Open/Closed: add a new rule by adding a class to RULES; nothing else changes."""
from datetime import datetime

from grepx_service import local_today

from . import criteria as C

class Rule:
    """check(a) -> None when fine, otherwise the reason. note(a) -> an extra hint that does not block."""
    def check(self, a): return None
    def note(self, a): return None

class AgeRule(Rule):
    def check(self, a):
        top = C.REPEAT_AGE_MAX if a.get("repeat") else C.AGE_MAX
        if a["age"] < C.AGE_MIN: return f"Donors must be at least {C.AGE_MIN}."
        if a["age"] > top:
            return (f"Repeat donors can donate up to age {C.REPEAT_AGE_MAX}." if a.get("repeat")
                    else f"First-time donors must be {C.AGE_MIN}–{C.AGE_MAX} (repeat donors up to {C.REPEAT_AGE_MAX}).")
    def note(self, a):
        if C.AGE_MIN <= a["age"] < C.CONSENT_BELOW: return "Aged 16–17: you'll need a signed parental consent form — we'll contact you after you register."
class WeightRule(Rule):
    def check(self, a):
        if a["weight"] < C.WEIGHT_MIN: return f"You need to weigh at least {C.WEIGHT_MIN} kg."
class HemoglobinRule(Rule):
    def check(self, a):
        need = C.HB_MIN.get(a.get("sex") or "Female", C.HB_MIN["Female"])
        if a.get("hb") and a["hb"] < need: return f"Haemoglobin should be at least {need} g/dL (nurses test it at the drive)."
class GapRule(Rule):
    def __init__(self, days=90): self.days = days
    def check(self, a):
        if a.get("last") and (local_today() - a["last"]).days < self.days:
            return f"Wait {self.days} days between donations."
class SymptomsRule(Rule):
    def check(self, a):
        if a.get("illness"): return f"Wait until you've had no sore throat, cough, runny nose or diarrhoea for at least {C.SYMPTOM_FREE_DAYS} days."
class FeverRule(Rule):
    def check(self, a):
        if a.get("fever"): return f"No fever for {C.FEVER_FREE_WEEKS} weeks is needed before donating."
class TravelAdvisoryRule(Rule):
    def check(self, a):
        back = a.get("advisory_return")
        if C.ADVISORY.applies(back):
            return f"After an overnight stay in {C.ADVISORY.places_text}, please wait {C.ADVISORY.wait_months} months: you can donate from {C.ADVISORY.wait_until(back):%d %b %Y}."
class TravelRule(Rule):
    def check(self, a):
        if a.get("travel"): return "A recent trip to a malaria or Zika risk area may mean a short wait."
    def note(self, a):
        if a.get("travel") or a.get("abroad"): return "Check the waiting time for each country you visited on the HSA website (Check eligibility)."
class TattooRule(Rule):
    def check(self, a):
        if a.get("tattoo"): return "Tattoo/piercing in the last 6 months: please wait."
class PregnancyRule(Rule):
    def check(self, a):
        if a.get("pregnant"): return "Pregnancy or breastfeeding: not eligible right now."
class MedicationRule(Rule):
    def check(self, a):
        if a.get("medication"): return "Antibiotics or blood thinners: ask the camp doctor first."

RULES = [AgeRule(), WeightRule(), HemoglobinRule(), GapRule(), SymptomsRule(), FeverRule(), TravelAdvisoryRule(), TravelRule(),
         TattooRule(), PregnancyRule(), MedicationRule()]

def evaluate(answers, rules=RULES):
    """-> (eligible, reasons, notes)"""
    reasons = [r for r in (rule.check(answers) for rule in rules) if r]
    notes = [n for n in (rule.note(answers) for rule in rules) if n]
    return not reasons, reasons, notes

def parse_form(f):
    dob = datetime.strptime(f["dob"], "%Y-%m-%d").date()
    today = local_today()
    day = lambda k: datetime.strptime(f[k], "%Y-%m-%d").date() if f.get(k) else None
    return {
        "age": today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)),
        "sex": f.get("sex") or None,
        "weight": float(f["weight"]),
        "hb": float(f["hb"]) if f.get("hb") else None,
        "last": day("last"),
        "repeat": bool(f.get("last")) or f.get("repeat") == "yes",
        "advisory_return": day("advisory_return") if f.get("advisory") == "yes" else None,
        **{k: f.get(k) == "yes" for k in ("travel", "abroad", "illness", "fever", "tattoo", "pregnant", "medication")},
    }
