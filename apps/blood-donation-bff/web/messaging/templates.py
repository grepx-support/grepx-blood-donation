# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from flask import render_template
from jinja2 import TemplateNotFound

class MessageTemplates:
    """Finds the most specific template: event/channel.role.j2 → event/channel.j2 → event/text.j2.
    Email templates start with 'Subject: ...' and are wrapped in a branded HTML layout."""
    ROOT = "messages"

    def render(self, event, channel, role, **ctx):
        from automessages import CustomText
        custom = CustomText().render(event, channel, ctx)   # an admin's own wording wins over the built-in design
        if custom: subject, body = custom
        else: subject, body = self._split(self._render_first(self._candidates(event, channel, role), ctx))
        if channel == "email":
            layout_ctx = {k: v for k, v in ctx.items() if k not in ("body", "subject")}
            body = render_template(f"{self.ROOT}/_email_layout.html", body=body, subject=subject, **layout_ctx)
        return subject, body

    def _candidates(self, event, channel, role):
        base = f"{self.ROOT}/{event}/"
        return [f"{base}{channel}.{role}.j2", f"{base}{channel}.j2", f"{base}text.{role}.j2", f"{base}text.j2"]

    @staticmethod
    def _render_first(names, ctx):
        for name in names:
            try: return render_template(name, **ctx)
            except TemplateNotFound: continue
        raise TemplateNotFound(names[-1])

    @staticmethod
    def _split(raw):
        raw = raw.strip()
        if raw.startswith("Subject:"):
            first, _, rest = raw.partition("\n")
            return first[len("Subject:"):].strip(), rest.strip()
        return raw.splitlines()[0][:80], raw
