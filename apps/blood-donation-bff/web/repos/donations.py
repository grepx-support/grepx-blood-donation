"""Donations (donation-service), certificates and vouchers (recognition-service), referral standings and site statistics."""
from __future__ import annotations
import grepx_contracts as gc

from datetime import date
from grepx_service import local_today

from dates import today

from . import _nexus as nx

DONATION_REQ, DONATION_SVC = gc.donation.REQUESTS, gc.donation.SERVICE


def _with_drive(row: dict, title_key: str = "title") -> dict:
    d = nx.one(gc.event.EVENTS, row.get("drive_id")) if row.get("drive_id") else None
    return {**row, title_key: (d or {}).get("title"), "venue": (d or {}).get("venue"), "drive_date": (d or {}).get("drive_date")}


class DonationRepo:
    def for_donor(self, i):
        return sorted((_with_drive(x) for x in nx.where(gc.donation.DONATIONS, donor_id=i)), key=lambda x: x.get("donated_on") or "", reverse=True)

    def add(self, donor_id, date, drive_id=None, units=1):
        v = nx.command(DONATION_REQ, DONATION_SVC, {"action": "RECORD", "donor_id": donor_id, "drive_id": drive_id or "",
                                                    "donated_on": date, "units": units, "actor_id": nx.actor()})
        return v.fields.get("donation_id")

    def for_drive(self, drive_id):
        return nx.where(gc.donation.DONATIONS, drive_id=drive_id)

    def exists_for(self, donor_id, drive_id):
        return bool(nx.where(gc.donation.DONATIONS, donor_id=donor_id, drive_id=drive_id))

    def remove_for(self, donor_id, drive_id):
        for x in nx.where(gc.donation.DONATIONS, donor_id=donor_id, drive_id=drive_id):
            nx.command(DONATION_REQ, DONATION_SVC, {"action": "VOID", "donation_id": x["id"], "actor_id": nx.actor()})


class CertificateRepo:
    def add(self, code, donor_id, drive_id, donated_on):
        pass                                        # recognition-service issues certificates when a drive is completed

    def exists(self, donor_id, drive_id):
        return bool(nx.where(gc.recognition.CERTIFICATES, donor_id=donor_id, drive_id=drive_id))

    def by_code(self, code):
        c = nx.one(gc.recognition.CERTIFICATES, code)
        if not c:
            return None
        p = nx.one(gc.people.PEOPLE, c.get("donor_id")) or {}
        return {**_with_drive(c), "name": p.get("name"), "photo_id": p.get("photo_id")}

    def for_donor(self, donor_id):
        return sorted((_with_drive(c) for c in nx.where(gc.recognition.CERTIFICATES, donor_id=donor_id)),
                      key=lambda c: c.get("donated_on") or "", reverse=True)

    def for_drive(self, drive_id):
        out = []
        for c in nx.where(gc.recognition.CERTIFICATES, drive_id=drive_id):
            p = nx.one(gc.people.PEOPLE, c.get("donor_id")) or {}
            access = nx.one(gc.access.USER_ACCESS, c.get("donor_id")) or {}
            out.append({**c, "name": p.get("name"), "email": p.get("email"), "phone": p.get("phone"), "role": access.get("role") or "donor"})
        return sorted(out, key=lambda c: (c.get("name") or "").lower())

    def mark_sent(self, code, when):
        pass                                        # recognition-service records sending


class VoucherRepo:
    def add(self, drive_id, donor_id, title, partner, details, code, expires_on):
        pass                                        # recognition-service hands out vouchers when a drive is completed

    def has(self, drive_id, donor_id):
        return bool(nx.where(gc.recognition.VOUCHERS, drive_id=drive_id, donor_id=donor_id))

    def for_donor(self, donor_id):
        return [_with_drive(v, "drive_title") for v in sorted(nx.where(gc.recognition.VOUCHERS, donor_id=donor_id),
                                                               key=lambda v: v.get("created") or "", reverse=True)]

    def for_drive(self, drive_id):
        return nx.where(gc.recognition.VOUCHERS, drive_id=drive_id)

    def first_for(self, drive_id, donor_id):
        rows = nx.where(gc.recognition.VOUCHERS, drive_id=drive_id, donor_id=donor_id)
        return rows[0] if rows else None


class ReferralRepo:
    """Referral points come from referral-service (referral_scores); the web never scores."""
    def _scores(self):
        return [{"id": s["id"], "name": s.get("name", ""), "joined": int(s.get("joined") or 0), "donated": int(s.get("donated") or 0),
                 "points": int(s.get("points") or 0)} for s in nx.table(gc.referral.REFERRAL_SCORES)]

    def leaderboard(self, n=10):
        return sorted(self._scores(), key=lambda s: (-s["points"], s["name"]))[:n]

    def stats_for(self, donor_id):
        row = next((s for s in self._scores() if s["id"] == str(donor_id)), None)
        return {k: row[k] if row else 0 for k in ("joined", "donated", "points")}

    def rank_of(self, donor_id):
        ids = [r["id"] for r in self.leaderboard(10000)]
        return ids.index(str(donor_id)) + 1 if str(donor_id) in ids else None


class StatsRepo:
    @staticmethod
    def _role(i):
        return (nx.one(gc.access.USER_ACCESS, i) or {}).get("role") or "donor"

    def summary(self):
        donors = nx.table(gc.people.PEOPLE)
        donations = len(nx.table(gc.donation.DONATIONS))
        donor_count = sum(1 for d in donors if self._role(d["id"]) == "donor")
        return {"donors": donor_count, "donations": donations, "lives": donations * 3, "staff": len(donors) - donor_count,
                "drives": sum(1 for d in nx.table(gc.event.EVENTS) if (d.get("drive_date") or "") >= today())}

    def monthly(self, months=12):
        counts: dict[str, int] = {}
        for x in nx.table(gc.donation.DONATIONS):
            m = (x.get("donated_on") or "")[:7]
            counts[m] = counts.get(m, 0) + 1
        y, m, out = local_today().year, local_today().month, []
        for _ in range(months):
            out.append((date(y, m, 1).strftime("%b %y"), counts.get(f"{y}-{m:02d}", 0)))
            y, m = (y, m - 1) if m > 1 else (y - 1, 12)
        return out[::-1]

    def blood_groups(self):
        counts: dict[str, int] = {}
        for d in nx.table(gc.people.PEOPLE):
            if self._role(d["id"]) == "donor":
                g = d.get("blood_group") or "Unknown"
                counts[g] = counts.get(g, 0) + 1
        return [{"blood_group": g, "n": n} for g, n in sorted(counts.items(), key=lambda kv: -kv[1])]

    def funnel(self):
        regs = [r for r in nx.table(gc.booking.BOOKINGS) if r.get("state") in ("interested", "confirmed", "donated", "no_show", "not_eligible")]
        return [("Interested", len(regs)), ("Confirmed", sum(1 for r in regs if r.get("state") in ("confirmed", "donated"))),
                ("Donated", sum(1 for r in regs if r.get("state") == "donated"))]

    def drive_fill(self):
        from .drives import DriveRepo
        return [{"title": d["title"], "capacity": d["capacity"], "going": d["going"]} for d in DriveRepo().upcoming()[:6]]

    def task_status(self):
        counts: dict[str, int] = {}
        for t in nx.table(gc.task.TASKS):
            s = t.get("state") or "todo"
            counts[s] = counts.get(s, 0) + 1
        return [{"status": s, "n": n} for s, n in counts.items()]

    def top_donors(self, n=5):
        counts: dict[str, int] = {}
        for x in nx.table(gc.donation.DONATIONS):
            counts[x.get("donor_id")] = counts.get(x.get("donor_id"), 0) + 1
        names = {d["id"]: d.get("name", "") for d in nx.table(gc.people.PEOPLE)}
        rows = [{"name": names.get(i, "?"), "n": c} for i, c in counts.items() if i in names]
        return sorted(rows, key=lambda r: (-r["n"], r["name"]))[:n]
