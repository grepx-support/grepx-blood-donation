# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Observer pattern: features publish domain events; subscribers decide who gets told."""
from collections import defaultdict

class EventBus:
    def __init__(self): self._subs = defaultdict(list)
    def subscribe(self, name, handler):
        if handler not in self._subs[name]: self._subs[name].append(handler)
    def publish(self, name, **payload):
        for handler in self._subs[name]: handler(**payload)

bus = EventBus()
