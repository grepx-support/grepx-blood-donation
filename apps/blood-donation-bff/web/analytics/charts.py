# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from .base import ChartWidget

class DonationsTrend(ChartWidget):
    key, title, icon, span, default, chart_type = "donations_trend", "Donations per month", "trending-up", 2, ("volunteer", "admin"), "area"
    def options(self):
        data = self.stats.monthly()
        return {"series": [{"name": "Donations", "data": [n for _, n in data]}], "xaxis": {"categories": [m for m, _ in data]},
                "stroke": {"curve": "smooth", "width": 3}, "fill": {"type": "gradient", "gradient": {"opacityFrom": .45, "opacityTo": .02}}}

class BloodGroups(ChartWidget):
    key, title, icon, default, chart_type = "blood_groups", "Donors by blood group", "droplets", ("public", "donor", "volunteer", "admin"), "donut"
    def options(self):
        rows = self.stats.blood_groups()
        return {"series": [r["n"] for r in rows], "labels": [r["blood_group"] for r in rows], "stroke": {"width": 0},
                "plotOptions": {"pie": {"donut": {"size": "70%", "labels": {"show": True, "total": {"show": True, "label": "Donors"}}}}}}

class DriveFunnel(ChartWidget):
    key, title, icon, default = "drive_funnel", "Registration funnel", "filter", ("volunteer", "admin")
    def options(self):
        rows = self.stats.funnel()
        return {"series": [{"name": "People", "data": [n for _, n in rows]}], "xaxis": {"categories": [l for l, _ in rows]},
                "plotOptions": {"bar": {"horizontal": True, "isFunnel": True, "borderRadius": 8, "barHeight": "80%"}},
                "dataLabels": {"enabled": True}, "legend": {"show": False}}

class UpcomingFill(ChartWidget):
    key, title, icon, default = "upcoming_fill", "Upcoming drives – spots filled", "gauge", ("donor", "volunteer", "admin")
    def options(self):
        rows = self.stats.drive_fill()
        return {"series": [{"name": "% filled", "data": [min(100, round(r["going"] / (r["capacity"] or 100) * 100)) for r in rows]}],
                "xaxis": {"categories": [r["title"][:22] for r in rows], "max": 100},
                "plotOptions": {"bar": {"horizontal": True, "borderRadius": 6, "barHeight": "55%"}}}

class TaskStatus(ChartWidget):
    key, title, icon, default, chart_type = "task_status", "Tasks by status", "list-checks", ("volunteer", "admin"), "pie"
    LABELS = {"todo": "To do", "in_progress": "In progress", "blocked": "Blocked", "done": "Done"}
    def options(self):
        rows = self.stats.task_status()
        return {"series": [r["n"] for r in rows], "labels": [self.LABELS.get(r["status"], r["status"]) for r in rows]}

class ChannelDelivery(ChartWidget):
    key, title, icon = "channel_delivery", "Message delivery by channel", "send"
    def options(self):
        from repos import NotificationLogRepo
        rows = NotificationLogRepo().by_channel()
        return {"series": [{"name": "Sent", "data": [r["sent"] for r in rows]}, {"name": "Failed", "data": [r["failed"] for r in rows]}],
                "xaxis": {"categories": [r["channel"] for r in rows]}, "chart": {"type": "bar", "height": 290, "stacked": True},
                "plotOptions": {"bar": {"borderRadius": 6, "columnWidth": "45%"}}}
