# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import json
from media.service import is_media_id

class GalleryFull(ValueError): pass

class DriveGallery:
    """Up to N pictures per drive, stored as media ids (or outside https links). The first one is the cover,
    kept in drives.image_url so every page can show it."""
    def __init__(self, media, limit=3): self.media, self.limit = media, limit

    @staticmethod
    def images(d):
        try: imgs = json.loads(d["images"] or "[]")
        except (KeyError, TypeError, ValueError): imgs = []
        if not imgs and d["image_url"]: imgs = [d["image_url"]]
        return imgs

    def add(self, d, files=(), urls=()):
        """Returns (added, problems). Pictures over the limit are refused with a message, never silently dropped."""
        imgs, problems = self.images(d), []
        for url in (u.strip() for u in urls if u and u.strip()):
            if not url.startswith(("https://", "http://")): problems.append(f"{url[:40]}: links must start with https://"); continue
            if len(imgs) >= self.limit: problems.append(f"Only {self.limit} pictures per drive."); break
            if url not in imgs: imgs.append(url)
        for f in (f for f in files if f and f.filename):
            if len(imgs) >= self.limit: problems.append(f"Only {self.limit} pictures per drive — {f.filename} was not added."); continue
            try: imgs.append(self.media.save(f, "drive", d["id"]))
            except ValueError as e: problems.append(str(e))
        added = len(imgs) - len(self.images(d))
        self._save(d["id"], imgs)
        return added, problems

    def remove(self, d, ref):
        self._save(d["id"], [u for u in self.images(d) if u != ref])
        from repos import DriveRepo
        if is_media_id(ref) and not DriveRepo().uses_picture(ref): self.media.delete(ref)

    def make_cover(self, d, ref):
        imgs = self.images(d)
        if ref in imgs: imgs.remove(ref); imgs.insert(0, ref); self._save(d["id"], imgs)

    @staticmethod
    def _save(drive_id, imgs):
        from repos import DriveRepo
        DriveRepo().set_images(drive_id, json.dumps(imgs), imgs[0] if imgs else None)
