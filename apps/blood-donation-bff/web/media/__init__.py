# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Central place for every uploaded picture (donor photos, drive banners).

The database only stores a media id (32 hex characters). Where the file lives is decided by one setting:
  MEDIA_STORAGE=local   files under UPLOAD_DIR (default instance/uploads), served by this app at /media/<id>
  MEDIA_STORAGE=s3      any S3-compatible bucket (AWS S3, Cloudflare R2, DigitalOcean Spaces, MinIO)
and MEDIA_BASE_URL can point straight at a CDN or another server holding the same files.
Moving the pictures elsewhere = copy the folder/bucket and change the setting; no data changes."""
from .service import MediaService, media_url, MediaRejected

__all__ = ["MediaService", "media_url", "MediaRejected"]
