# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Singapore donor requirements (HSA): ONE place for the numbers used by the website, the quick form and LifeBot.
Update here when HSA changes them."""
from dataclasses import dataclass
from datetime import date

from grepx_service import local_today

HSA_URL = "https://www.hsa.gov.sg/blood-donation"   # "Check eligibility" there lists every country and its waiting time

AGE_MIN, AGE_MAX = 16, 65            # anyone in this range
REPEAT_AGE_MAX = 75                  # people who have donated before may continue up to this age
CONSENT_BELOW = 18                   # 16 and 17 need a signed parental consent form
WEIGHT_MIN = 45                      # kg
HB_MIN = {"Female": 12.5, "Male": 13.0}   # g/dL, tested by nurses at the drive
SYMPTOM_FREE_DAYS = 7                # sore throat, cough, runny nose, diarrhoea …
FEVER_FREE_WEEKS = 4

def _add_months(d, months):
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    for day in (d.day, 30, 29, 28):
        try: return date(y, m, day)
        except ValueError: continue

@dataclass(frozen=True)
class TravelAdvisory:
    """Overnight stay in these places -> wait N months after coming back (worded generically, no start date)."""
    places: tuple
    wait_months: int

    @property
    def places_text(self): return ", ".join(self.places[:-1]) + " or " + self.places[-1]
    def wait_until(self, returned): return _add_months(returned, self.wait_months)
    def applies(self, returned): return returned is not None and local_today() < self.wait_until(returned)

ADVISORY = TravelAdvisory(("India", "Batam", "Bintan"), 4)

REQUIREMENTS = [  # what the website shows, in order
    ("cake", f"{AGE_MIN}–{AGE_MAX}", "years old", f"Anyone aged {AGE_MIN} to {AGE_MAX} can donate. Repeat donors can continue up to {REPEAT_AGE_MAX}."),
    ("file-signature", f"{AGE_MIN}–{CONSENT_BELOW - 1}", "parental consent", f"Youth aged {AGE_MIN} and {CONSENT_BELOW - 1} need a signed parental consent form; we'll contact you after you register."),
    ("scale", f"{WEIGHT_MIN} kg", "or more", f"You need to weigh at least {WEIGHT_MIN} kg."),
    ("shield-check", f"{SYMPTOM_FREE_DAYS} days", "symptom-free", "Good health, with no sore throat, cough, runny nose or diarrhoea for at least a week."),
    ("thermometer", f"{FEVER_FREE_WEEKS} weeks", "without fever", f"No fever in the last {FEVER_FREE_WEEKS} weeks."),
    ("droplet", f"{HB_MIN['Female']} / {HB_MIN['Male']}", "g/dL haemoglobin", f"At least {HB_MIN['Female']} g/dL for women and {HB_MIN['Male']} g/dL for men. Nurses test it at the drive."),
]
