# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from datetime import datetime
from flask import current_app
from db import engine
from .exporter import TableExporter
from .git_publisher import GitPublisher

class BackupService:
    """Export all tables -> commit -> push. Works for any database the app runs on."""
    def run(self):
        cfg = current_app.config
        git = GitPublisher(cfg["BACKUP_DIR"], cfg["BACKUP_GIT_REMOTE"], cfg["BACKUP_BRANCH"])
        git.prepare()
        manifest = TableExporter(engine()).export(cfg["BACKUP_DIR"])
        copied, missing = self.media().export(cfg["BACKUP_DIR"])
        total = sum(manifest["rows"].values())
        note = git.publish(f"Backup {datetime.now():%Y-%m-%d %H:%M} - {total} rows, {len(self.media().rows)} pictures ({manifest['database']})")
        pics = f" {copied} new picture(s) copied" + (f", {missing} missing from storage" if missing else "") + "."
        return f"Backed up {total} rows from {len(manifest['rows'])} tables to {cfg['BACKUP_DIR']}.{pics} {note}"

    @staticmethod
    def media():
        from repos import MediaRepo
        from media.storage import storage_from
        from .media_backup import MediaBackup
        return MediaBackup(storage_from(current_app.config), MediaRepo().all())
