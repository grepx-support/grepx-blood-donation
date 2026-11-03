# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Admin-written wording with {placeholders}. Plain text only (no template code), so it is safe to edit in the app."""
import re
from markupsafe import escape
from integrations import setting

def _fill(text, values):
    """{name} -> value; anything else (unknown names, {a.b}, {x[0]}) stays as written. No format() tricks possible."""
    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), text or "")

class CustomText:
    def get(self, key):
        text = setting(f"auto.{key}.text")
        return (setting(f"auto.{key}.subject"), text) if text.strip() else None

    def render(self, key, channel, ctx):
        """-> (subject, body) using the admin's words, or None when they kept the built-in design."""
        custom = self.get(key)
        if not custom: return None
        values = self.values(ctx)
        subject = _fill(custom[0], values)
        text = _fill(custom[1], values).strip()
        if channel != "email": return subject or text.splitlines()[0][:80], text
        return subject or text.splitlines()[0][:80], self._html(text)

    @staticmethod
    def _html(text):
        """Paragraphs and clickable links; everything else is escaped."""
        out = []
        for para in re.split(r"\n\s*\n", str(escape(text))):
            para = re.sub(r"(https?://[^\s<]+)", r'<a href="\1" style="color:#e11d48;font-weight:600">\1</a>', para)
            out.append("<p>" + para.replace("\n", "<br>") + "</p>")
        return "\n".join(out)

    @staticmethod
    def values(ctx):
        """Placeholder values from whatever the message was sent with."""
        r, d, site = ctx.get("r"), ctx.get("drive") or {}, ctx.get("site", "")
        b, slot, cert, v = ctx.get("b") or {}, ctx.get("slot") or {}, ctx.get("cert") or {}, ctx.get("voucher")
        def g(obj, k):
            try: return obj[k] or ""
            except (KeyError, TypeError, IndexError): return ""
        drive_id = g(d, "id") or g(b, "drive")
        link = (f"{site}/certificate/{g(cert, 'id')}" if cert else f"{site}/drive/{drive_id}#book" if drive_id else f"{site}/dashboard")
        voucher = ""
        if v: voucher = f"🎁 {g(v, 'title')}" + (f" ({g(v, 'partner')})" if g(v, "partner") else "") + (f" – code {g(v, 'code')}" if g(v, "code") else "")
        return {"first_name": r.first_name if r else "", "name": r.name if r else "", "org": ctx.get("org", ""), "link": link,
                "drive_title": g(d, "title") or g(b, "title"), "drive_date": g(d, "drive_date") or g(b, "drive_date"),
                "drive_time": g(d, "time_slot") or (f"{g(b, 'slot_start')}" if g(b, "slot_start") else g(b, "time_slot")) or "All day",
                "venue": g(d, "venue") or g(b, "venue"), "slot_time": f"{g(slot, 'starts_at')}–{g(slot, 'ends_at')}" if slot else "",
                "voucher": voucher, "friend": (g(ctx.get("friend"), "name") or "").split(" ")[0]}
