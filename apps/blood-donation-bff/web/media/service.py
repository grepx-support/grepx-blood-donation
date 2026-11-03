# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import grepx_contracts as gc
import uuid
from flask import current_app, url_for
from repos.media_repo import MediaRepo
from .image import ImageProcessor, MediaRejected

class MediaService:
    """Facade: save an upload -> media id; delete. media-service processes and stores every picture (resized WebP);
    this only stages the upload in the shared storage and asks for it."""
    MAX_BYTES = 15 * 1024 * 1024

    def __init__(self, repo=None, storage=None, processor=None):
        from repos import _nexus as nx
        self.nx, self.processor = nx, processor or ImageProcessor()
        self.storage = storage or nx.GW.storage

    def save(self, upload, kind, owner_id=None):
        self.processor.process(upload, kind)            # same checks as before: refuses anything that isn't a picture
        upload.stream.seek(0)
        data = upload.read()
        if len(data) > self.MAX_BYTES:
            raise MediaRejected("That picture is too large (max 15 MB).")
        staged = f"staging/{uuid.uuid4().hex}"
        self.storage.put(staged, data)
        v = self.nx.command(gc.media.REQUESTS, gc.media.SERVICE, {"action": "PROCESS", "staged_key": staged, "kind": kind,
                                                                "owner_id": owner_id or ""})
        return v.fields["media_id"]

    def delete(self, mid):
        self.nx.command(gc.media.REQUESTS, gc.media.SERVICE, {"action": "DELETE", "media_id": mid}, ok_only=False)


def is_media_id(value): return isinstance(value, str) and len(value) == 32 and all(c in "0123456789abcdef" for c in value)

def media_url(value):
    """Template filter: a media id -> its URL; anything else (an https link, an old /media/... path) is returned as is."""
    if not value: return ""
    if not is_media_id(value): return value
    base = (current_app.config.get("MEDIA_BASE_URL") or "").rstrip("/")
    if base:  # CDN / other server holding the same keys
        row = MediaRepo().by_id(value)
        return f"{base}/{row['key']}" if row else ""
    return url_for("media.file", mid=value)
