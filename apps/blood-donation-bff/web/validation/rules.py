# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Limits shared by the server checks (forms.py) and the browser (html attributes), so both always agree."""
from grepx_service import local_today
from grepx_common.phone import rules as phone_rules
from markupsafe import Markup, escape

NAME_MAX, WEIGHT_MIN, WEIGHT_MAX, AGE_MIN, AGE_MAX, PASSWORD_MIN = 100, 30, 250, 16, 75, 8  # age: repeat donors up to 75 (HSA)

# Browser-side: characters only; the exact home-country rule (deployment file phone:) is checked by Phone.normalize.
PHONE_PATTERN = r"\s*\+?[\d\s\-()]{6,20}\s*"
PHONE_HELP = phone_rules().help

def _years_ago(n):
    t = local_today()
    try: return t.replace(year=t.year - n)
    except ValueError: return t.replace(year=t.year - n, day=28)

def attrs(kind):
    """HTML attributes for an input of this kind: {{ rules('phone') }}."""
    a = {
        "phone": dict(type="tel", inputmode="tel", autocomplete="tel", maxlength=20, pattern=PHONE_PATTERN, title=PHONE_HELP,
                      **{"data-phone": "", "data-msg": PHONE_HELP, "placeholder": phone_rules().example}),
        "name": dict(minlength=2, maxlength=NAME_MAX, pattern=r"[^0-9]*[^\s0-9][^0-9]*", autocomplete="name",
                     **{"data-msg": "Please enter a full name (letters only, no numbers)."}),
        "email": dict(type="email", maxlength=254, autocomplete="email", **{"data-msg": "Enter a valid email, like name@example.com."}),
        "weight": dict(type="number", min=WEIGHT_MIN, max=WEIGHT_MAX, step="0.1", inputmode="decimal",
                       **{"data-msg": f"Weight in kg, between {WEIGHT_MIN} and {WEIGHT_MAX}."}),
        "dob": dict(type="date", min=_years_ago(AGE_MAX + 1).isoformat(), max=_years_ago(AGE_MIN).isoformat(),
                    **{"data-msg": f"Donors must be {AGE_MIN}–{AGE_MAX} years old."}),
        "password": dict(minlength=PASSWORD_MIN, **{"data-msg": f"At least {PASSWORD_MIN} characters."}),
        "count": dict(type="number", min=1, step=1, inputmode="numeric", **{"data-msg": "Enter a whole number of 1 or more."}),
    }[kind]
    return Markup(" ".join(f'{k}="{escape(v)}"' if v != "" else k for k, v in a.items()))
