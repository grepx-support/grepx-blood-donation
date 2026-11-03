# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

class TaskPolicy:
    """Who may do what with tasks. Admins (or 'manage_tasks') assign anyone; everyone manages their own and may pick up unassigned ones."""
    def __init__(self, user): self.user = user

    def can_assign_others(self): return self.user.can("manage_tasks")
    def can_edit(self, task):
        return self.user.is_admin or self.can_assign_others() or self.user.id in (task["assignee_id"], task["created_by"])
    def can_claim(self, task): return task["assignee_id"] is None

    def assignee(self, requested):
        """'none' = leave unassigned (only for people who can assign); empty = me."""
        if not self.can_assign_others(): return self.user.id
        if requested == "none": return None
        return str(requested) if requested else self.user.id
