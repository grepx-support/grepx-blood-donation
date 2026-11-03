# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from .base import AUDIENCES
from .registry import WIDGET_CLASSES

class AnalyticsService:
    """Decides which widgets each audience sees. Admins always see everything."""
    def __init__(self, access_repo, classes=WIDGET_CLASSES):
        self.access, self.classes = access_repo, classes

    @staticmethod
    def audience_of(user):
        return user.role if user.is_authenticated else "public"

    def for_audience(self, audience, kinds=None):
        saved = self.access.all()
        return [cls() for cls in self.classes
                if (audience == "admin" or audience in saved.get(cls.key, set(cls.default)))
                and (kinds is None or cls.kind in kinds)]

    def matrix(self):
        saved = self.access.all()
        return [(cls, saved.get(cls.key, set(cls.default))) for cls in self.classes], AUDIENCES

    def save(self, form):
        self.access.replace({cls.key: {a for a in AUDIENCES if form.get(f"{cls.key}:{a}")} for cls in self.classes})
