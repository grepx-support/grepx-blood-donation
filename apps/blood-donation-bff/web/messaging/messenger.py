# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import grepx_contracts as gc
from grepx_service import local_today
from ui.site import site_url
from flask import current_app
from .channels import CHANNELS
from .templates import MessageTemplates

class Messenger:
    """Facade: one call sends a templated message to many people over many channels and logs it."""
    def __init__(self, log, templates=None, channels=None):
        self.log, self.templates, self.channels = log, templates or MessageTemplates(), channels or CHANNELS

    def send(self, event, recipients, channels, drive_id=None, **ctx):
        sent = 0
        cfg = current_app.config
        ctx.setdefault("org", cfg["ORG_NAME"]); ctx.setdefault("site", site_url())
        ctx.setdefault("company", cfg["COMPANY_NAME"]); ctx.setdefault("company_url", cfg["COMPANY_URL"]); ctx.setdefault("year", local_today().year)
        for r in recipients:
            for key in channels:
                sent += self._deliver(event, r, key, drive_id, ctx)
        return sent

    def send_auto(self, event, recipients, drive_id=None, **ctx):
        """Automatic messages: only when the admin left them on, over the channels they chose."""
        from automessages import AutoPolicy
        channels = AutoPolicy.channels(event)
        return self.send(event, recipients, channels, drive_id, **ctx) if channels else 0

    def _deliver(self, event, recipient, key, drive_id, ctx):
        """Render with the site's own message templates, deliver through notification-service (it logs every message)."""
        from repos import _nexus as nx
        channel = self.channels.get(key)
        address = channel.address(recipient) if channel else ""
        if not address: return 0
        try:
            subject, body = self.templates.render(event, key, recipient.role, r=recipient, **ctx)
            v = nx.command(gc.notification.NOTIFICATIONS, gc.notification.SERVICE, {
                "action": "SEND", "template": "staff_message", "channel": key, "recipient": address, "auto": False,
                "values": {"subject": subject or "", "text": body or ""}, "ref": f"{event}|{drive_id or ''}",
                "event": event, "drive_id": drive_id or "", "user_id": str(getattr(recipient, "id", "") or "")}, ok_only=False)
            return int(v.ok and v.fields.get("delivery") in ("SENT", "LOGGED"))
        except Exception as e:
            current_app.logger.warning("send failed: %s", e)
            return 0
