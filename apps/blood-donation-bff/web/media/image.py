# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError

class MediaRejected(ValueError): pass

class ImageProcessor:
    """Checks a picture is real (Pillow must open it, so a renamed .exe is refused), turns phone photos upright,
    resizes and re-encodes to WebP. Each kind has its own shape."""
    MAX_BYTES, FORMATS = 15 * 1024 * 1024, {"JPEG", "PNG", "WEBP", "GIF", "MPO"}
    KINDS = {"drive": dict(side=1920, square=False), "avatar": dict(side=512, square=True)}

    def process(self, upload, kind):
        data = upload.read(self.MAX_BYTES + 1)
        name = getattr(upload, "filename", "picture")
        if len(data) > self.MAX_BYTES: raise MediaRejected(f"{name}: larger than 15 MB.")
        try:
            img = Image.open(BytesIO(data))
            if img.format not in self.FORMATS: raise MediaRejected(f"{name}: use JPG, PNG, WebP or GIF.")
            img.load()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise MediaRejected(f"{name}: not a picture we can read.")
        spec = self.KINDS[kind]
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
        img = ImageOps.fit(img, (spec["side"], spec["side"])) if spec["square"] else self._shrink(img, spec["side"])
        out = BytesIO(); img.save(out, "WEBP", quality=82, method=4)
        return out.getvalue(), img.size

    @staticmethod
    def _shrink(img, side): img.thumbnail((side, side)); return img
