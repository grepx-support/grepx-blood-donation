# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""The channels people can be messaged on, as the pages need them: which address to use and whether it is set up.
Delivery itself is notification-service's job (Messenger sends there)."""
from dataclasses import dataclass

from integrations import settings


@dataclass(frozen=True)
class Channel:
    key: str
    contact: str          # recipient attribute holding the address ("email" or "phone")
    required: tuple       # settings that must be filled in (Integrations page or .env)
    integration: str      # the Integrations card that sets it up

    @property
    def setup_hint(self): return f"Integrations → {self.integration}"

    def address(self, recipient): return getattr(recipient, self.contact, "") or ""

    def configured(self) -> bool:
        c = settings()
        return all(c.get(k) for k in self.required)


CHANNELS = {c.key: c for c in (
    Channel("email", "email", ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"), "Email (SMTP)"),
    Channel("sms", "phone", ("TWILIO_SID", "TWILIO_TOKEN", "TWILIO_SMS_FROM"), "SMS & WhatsApp (Twilio)"),
    Channel("whatsapp", "phone", ("TWILIO_SID", "TWILIO_TOKEN", "TWILIO_WHATSAPP_FROM"), "SMS & WhatsApp (Twilio)"),
)}
