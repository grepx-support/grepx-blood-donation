# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Pydantic form models shared by every screen that writes people's details (one set of rules, everywhere)."""
from datetime import date
from grepx_service import local_today
from typing import Annotated, Literal, Optional
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, ValidationError, field_validator
from grepx_common import Phone
from . import rules

def _name(v):
    v = " ".join(str(v or "").split())
    if len(v) < 2: raise ValueError("Please enter a full name.")
    if len(v) > rules.NAME_MAX: raise ValueError(f"Names can be at most {rules.NAME_MAX} characters.")
    if any(c.isdigit() for c in v): raise ValueError("Names can't contain numbers.")
    if not any(c.isalpha() for c in v): raise ValueError("Please enter a real name.")
    return v

def _blank_none(v): return None if v is None or str(v).strip() == "" else v
def _upper(v): return str(v).strip().upper() if v else None
def _cap(v): return str(v).strip().capitalize() if v else None

Name = Annotated[str, BeforeValidator(_name)]
PhoneNo = Annotated[str, BeforeValidator(Phone.normalize)]
OptionalPhone = Annotated[Optional[str], BeforeValidator(lambda v: Phone.normalize(v) if _blank_none(v) else None)]
Email = Annotated[EmailStr, BeforeValidator(lambda v: str(v or "").strip().lower())]
BloodGroup = Annotated[Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]], BeforeValidator(lambda v: _upper(_blank_none(v)))]
Sex = Annotated[Optional[Literal["Male", "Female"]], BeforeValidator(lambda v: _cap(_blank_none(v)))]
Weight = Annotated[Optional[Annotated[float, Field(ge=rules.WEIGHT_MIN, le=rules.WEIGHT_MAX)]], BeforeValidator(_blank_none)]

def _age(v):
    if v and not rules.AGE_MIN <= (local_today() - v).days / 365.25 <= rules.AGE_MAX:
        raise ValueError(f"Donors must be {rules.AGE_MIN}–{rules.AGE_MAX} years old.")
    return v
Dob = Annotated[Optional[date], BeforeValidator(_blank_none), AfterValidator(_age)]

class Form(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

class ContactForm(Form):
    """'I'm interested' on the website."""
    name: Name
    phone: PhoneNo
    email: Email

class DonorForm(ContactForm):
    """Full donor details: add/edit donor, profile, Excel/grid import."""
    blood_group: BloodGroup = None
    sex: Sex = None
    weight: Weight = None
    dob: Dob = None

    def values(self): return {**self.model_dump(), "dob": self.dob.isoformat() if self.dob else None}

class WalkInForm(DonorForm):
    """Quick register at the desk or kiosk: email optional."""
    email: Optional[Email] = None
    @field_validator("email", mode="before")
    @classmethod
    def _optional(cls, v): return _blank_none(v)

class RegisterForm(DonorForm):
    password: str = Field(min_length=rules.PASSWORD_MIN)

class UserForm(Form):
    """Admin's Users & passwords screen: phone optional (staff may not share one)."""
    name: Name
    email: Email
    phone: OptionalPhone = None

FRIENDLY = {"email": "Enter a valid email, like name@example.com.", "weight": f"Weight must be a number from {rules.WEIGHT_MIN} to {rules.WEIGHT_MAX} kg.",
            "dob": "Date of birth must be a real date (YYYY-MM-DD).", "blood_group": "Blood group must be A+, A-, B+, B-, AB+, AB-, O+ or O-.",
            "sex": "Sex must be Male or Female.", "password": f"Passwords need at least {rules.PASSWORD_MIN} characters."}
LABELS = {"name": "Name", "phone": "Phone", "email": "Email", "weight": "Weight", "dob": "Date of birth",
          "blood_group": "Blood group", "sex": "Sex", "password": "Password"}

def check(model, data):
    """-> (clean model or None, {field: friendly message})."""
    try: return model(**{k: data.get(k) for k in model.model_fields}), {}
    except ValidationError as e:
        errors = {}
        for err in e.errors():
            field = str(err["loc"][0]) if err["loc"] else "form"
            if field in errors: continue
            raw = data.get(field)
            if err["type"] in ("missing",) or (raw is None or str(raw).strip() == "") and err["type"] != "value_error":
                errors[field] = "Required"
            elif err["type"] == "value_error" and field != "email":
                errors[field] = str(err.get("ctx", {}).get("error") or err["msg"]).removeprefix("Value error, ")
            else:
                errors[field] = FRIENDLY.get(field, err["msg"])
        return None, errors

def summary(errors):
    """One flash line: 'Phone: Use a Singapore number… · Weight: …'"""
    return " · ".join(f"{LABELS.get(k, k.title())}: {v}" for k, v in errors.items())
