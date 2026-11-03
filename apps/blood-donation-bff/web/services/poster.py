# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Square 1080px JPEG poster for a drive (Instagram needs JPEG; also handy to download and post by hand).
Uses the drive's cover picture as background when it has one, otherwise the brand gradient."""
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SIZE, PAD = 1080, 80
FONT_FILES = ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"]

def _font(size):
    for f in FONT_FILES:
        try: return ImageFont.truetype(f, size)
        except OSError: continue
    return ImageFont.load_default(size)

class PosterRenderer:
    def __init__(self, org): self.org = org

    def render(self, drive, cover_bytes=None, footer=""):
        img = self._readable(self._background(cover_bytes))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((PAD, PAD, PAD + 300, PAD + 64), 32, fill=(225, 29, 72))
        d.text((PAD + 150, PAD + 32), "BLOOD DRIVE", font=_font(30), fill="white", anchor="mm")
        y = 420
        for line in textwrap.wrap(drive["title"], 18)[:3]:
            d.text((PAD, y), line, font=_font(84), fill="white"); y += 96
        y += 20
        for text in (self._date(drive), drive["time_slot"] or "All day", drive["venue"]):
            d.text((PAD, y), text[:42], font=_font(42), fill=(255, 228, 230)); y += 58
        d.text((PAD, SIZE - PAD - 40), (footer or self.org)[:48], font=_font(34), fill="white")
        out = BytesIO(); img.convert("RGB").save(out, "JPEG", quality=88, optimize=True)
        return out.getvalue()

    @staticmethod
    def _background(cover_bytes):
        if cover_bytes:
            try:
                bg = ImageOps.fit(Image.open(BytesIO(cover_bytes)).convert("RGB"), (SIZE, SIZE)).filter(ImageFilter.GaussianBlur(1))
                shade = Image.new("RGB", (SIZE, SIZE), (20, 0, 8))
                return Image.blend(bg, shade, 0.55)
            except OSError: pass
        bg = Image.new("RGB", (SIZE, SIZE))
        top, bottom = (225, 29, 72), (76, 5, 25)
        for y in range(SIZE):
            t = y / SIZE
            ImageDraw.Draw(bg).line([(0, y), (SIZE, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
        return bg

    @staticmethod
    def _readable(img):
        """Dark fade over the lower part so white text stays legible on any photo."""
        fade = Image.new("L", (1, SIZE))
        for y in range(SIZE): fade.putpixel((0, y), int(max(0, (y - 250) / (SIZE - 250)) * 210))
        black = Image.new("RGB", (SIZE, SIZE), (15, 0, 5))
        return Image.composite(black, img.convert("RGB"), fade.resize((SIZE, SIZE)))

    @staticmethod
    def _date(drive):
        from datetime import date
        try: return date.fromisoformat(drive["drive_date"]).strftime("%A, %d %B %Y")
        except ValueError: return drive["drive_date"]
