# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from .base import Widget

class ImpactStats(Widget):
    key, title, icon, kind, span = "impact", "Our impact", "heart-pulse", "stats", 3
    default = ("public", "donor", "volunteer", "admin")
    def data(self):
        s = self.stats.summary()
        return [("Registered donors", s["donors"], "users"), ("Donations", s["donations"], "droplet"),
                ("Lives touched", s["lives"], "heart"), ("Upcoming drives", s["drives"], "calendar-heart")]

class TopDonors(Widget):
    key, title, icon, kind, default = "top_donors", "Hall of heroes", "trophy", "list", ("donor", "admin")
    def data(self):
        return [(short_name(r["name"]), r["n"], "🩸") for r in self.stats.top_donors()]

def short_name(name): return f"{name.split()[0]} {name.split()[-1][0]}." if " " in name else name

class TopRecruiters(Widget):
    key, title, icon, kind, default = "top_recruiters", "Invite leaderboard", "users-round", "list", ("public", "donor", "volunteer", "admin")
    def data(self):
        from repos import DonorRepo, ReferralRepo
        from services.referral_service import ReferralService
        return [(short_name(r["name"]), r["points"], "pts") for r in ReferralService(DonorRepo(), ReferralRepo(), "").leaderboard(5)]

class FlowWidget(Widget):
    """Renders a Mermaid flowchart."""
    kind, span = "flow", 2
    source = ""
    def data(self): return self.source

class DonorJourney(FlowWidget):
    key, title, icon, default = "donor_journey", "Your donation journey", "route", ("public", "donor", "volunteer")
    source = """flowchart LR
    A([Check eligibility]) --> B[Register for a drive]
    B --> C{Health screening}
    C -- Pass --> D[Donate ~10 min]
    C -- Not today --> E[We'll remind you later]
    D --> F[Rest & refresh]
    F --> G([Eligible again in 12 weeks])
    G -.-> B"""

class TaskLifecycle(FlowWidget):
    key, title, icon, default = "task_flow", "How planning works", "workflow", ("volunteer", "admin")
    source = """flowchart LR
    A([Admin / volunteer creates task]) --> B[To do]
    B --> C[In progress]
    C --> D([Done])
    B -. due soon & not done .-> R{{Reminder via email / SMS / WhatsApp}}
    C -. overdue .-> R"""
