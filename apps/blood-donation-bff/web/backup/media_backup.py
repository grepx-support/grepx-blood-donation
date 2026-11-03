# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Pictures go into the backup by media id, whatever storage holds them (local folder or S3 bucket).

backup/media/<kind>/<xx>/<id>.webp mirrors the storage keys, so a restore can put them back anywhere."""
from pathlib import Path

class MediaBackup:
    def __init__(self, storage, media_rows): self.storage, self.rows = storage, media_rows

    def export(self, folder):
        """Copy every picture listed in the media table into folder/media. Unchanged files are skipped."""
        root, copied, missing = Path(folder) / "media", 0, 0
        for r in self.rows:
            dst = root / r["key"]
            if dst.is_file() and dst.stat().st_size == (r["size"] or -1): continue
            data = self.storage.get(r["key"])
            if data is None: missing += 1; continue
            dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(data); copied += 1
        return copied, missing

    def restore(self, folder):
        """Put the pictures from a backup back into the current storage."""
        root, put = Path(folder) / "media", 0
        for r in self.rows:
            src = root / r["key"]
            if src.is_file(): self.storage.put(r["key"], src.read_bytes(), r["content_type"] or "image/webp"); put += 1
        return put
