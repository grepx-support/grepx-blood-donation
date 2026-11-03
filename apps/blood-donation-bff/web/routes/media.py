# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Serves pictures by media id, from wherever MEDIA_STORAGE keeps them (local folder or an S3 bucket)."""
from pathlib import Path
from flask import Blueprint, current_app, send_from_directory, abort
from repos.media_repo import MediaRepo
from media.service import is_media_id

bp = Blueprint("media", __name__)
YEAR = 60 * 60 * 24 * 365

@bp.route("/media/<mid>")
def file(mid):
    """Bytes from the shared storage media-service wrote them to (ids never change content: cached for a year)."""
    from flask import Response
    from repos import _nexus as nx
    mid = mid.removesuffix(".webp")
    row = MediaRepo().by_id(mid) if is_media_id(mid) else None
    data = nx.GW.storage.get(row["key"]) if row else None
    if not data: abort(404)
    resp = Response(data, mimetype=row.get("content_type") or "image/webp")
    resp.headers["Cache-Control"] = f"public, max-age={YEAR}, immutable"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp

@bp.route("/media/drives/<name>")
def legacy(name):
    """Links in emails sent before the central store still work if the old file is around."""
    folder = Path(current_app.config["UPLOAD_DIR"]) / "drives"
    if not (folder / Path(name).name).is_file(): abort(404)
    return send_from_directory(folder, Path(name).name, max_age=YEAR)
