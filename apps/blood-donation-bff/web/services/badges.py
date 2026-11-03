# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from dataclasses import dataclass

@dataclass(frozen=True)
class Badge:
    icon: str
    title: str
    need: int
    def earned(self, donations): return donations >= self.need

BADGES = (Badge("droplet", "First Drop", 1), Badge("heart-handshake", "Life Saver", 3), Badge("medal", "Regular Hero", 5),
          Badge("trophy", "Legend", 10), Badge("crown", "Platinum", 25))

def badges_for(donations): return [(b, b.earned(donations)) for b in BADGES]
