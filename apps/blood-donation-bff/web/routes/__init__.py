# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from . import (public, auth, donor, admin, analytics, drives, donors, staff, checkin, tasks, messages, imports, chat,
               calendar, kiosk, reports, users, my_tasks, media, attendees, social, completion, integrations, automessages, google_login)

BLUEPRINTS = [m.bp for m in (public, auth, donor, admin, analytics, drives, donors, staff, checkin, tasks, messages, imports, chat,
                             calendar, kiosk, reports, users, my_tasks, media, attendees, social, completion, integrations, automessages, google_login)]
