# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

import subprocess
from pathlib import Path

class GitError(Exception): pass

class GitPublisher:
    """Commits a folder and pushes it to a (private!) GitHub repo using the git command line."""
    def __init__(self, folder, remote="", branch="main"): self.dir, self.remote, self.branch = Path(folder), remote, branch

    def prepare(self):
        if (self.dir / ".git").is_dir(): return
        if self.remote and not (self.dir.exists() and any(self.dir.iterdir())):
            try: return self._git("clone", self.remote, str(self.dir), cwd=self.dir.parent)
            except GitError: pass  # empty or new remote: fall through and init
        self.dir.mkdir(parents=True, exist_ok=True)
        self._git("init", "-q"); self._git("checkout", "-q", "-B", self.branch)
        if self.remote: self._git("remote", "add", "origin", self.remote)

    def publish(self, message):
        self._identity()
        self._git("add", "-A")
        if not self._git("status", "--porcelain").strip(): return "No changes since the last backup."
        self._git("commit", "-q", "-m", message)
        if not self.remote: return "Committed locally (set BACKUP_GIT_REMOTE to push to GitHub)."
        self._git("push", "-q", "-u", "origin", f"HEAD:{self.branch}")
        return f"Pushed to {self.remote} ({self.branch})."

    def _identity(self):
        if not self._git("config", "user.email", check=False).strip():
            self._git("config", "user.email", "backup@bloodcamp.local"); self._git("config", "user.name", "Blood Camp Backup")

    def _git(self, *args, cwd=None, check=True):
        cwd = cwd or self.dir; Path(cwd).mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
        if check and r.returncode != 0: raise GitError((r.stderr or r.stdout).strip())
        return r.stdout
