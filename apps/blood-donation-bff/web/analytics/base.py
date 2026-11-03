# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from abc import ABC, abstractmethod
from repos import StatsRepo

AUDIENCES = {"public": "Website visitors", "donor": "Donors", "volunteer": "Volunteers", "admin": "Admins"}

class Widget(ABC):
    """An analytics card. kind = chart | stats | list | flow. 'default' = who sees it until an admin changes it."""
    key = title = icon = ""
    kind, span, default = "chart", 1, ("admin",)
    def __init__(self, stats=None): self.stats = stats or StatsRepo()
    @abstractmethod
    def data(self): ...

class ChartWidget(Widget):
    """Template Method: subclasses return series/categories; we add the shared chart styling."""
    chart_type, height = "bar", 290
    def data(self):
        opts = {"chart": {"type": self.chart_type, "height": self.height}, "dataLabels": {"enabled": False},
                "grid": {"strokeDashArray": 4}, "legend": {"position": "bottom"}}
        opts.update(self.options())
        return opts
    @abstractmethod
    def options(self): ...
