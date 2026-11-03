# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Printable certificate (A4 landscape PNG, 150 dpi) made with Pillow; the same image is the WhatsApp/Facebook preview."""
from datetime import date
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1754, 1240
RED, DARK, SOFT = (225, 29, 72), (40, 20, 25), (120, 100, 105)
BOLD = ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arialbd.ttf"]
SERIF = ["DejaVuSerif-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "georgiab.ttf", "DejaVuSans-Bold.ttf"]
PLAIN = ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"]

def _font(files, size):
    for f in files:
        try: return ImageFont.truetype(f, size)
        except OSError: continue
    return ImageFont.load_default(size)

class CertificateRenderer:
    def __init__(self, org, company=""): self.org, self.company = org, company

    def render(self, cert, verify_url, photo_bytes=None):
        img = Image.new("RGB", (W, H), (255, 251, 251))
        d = ImageDraw.Draw(img)
        d.rectangle((30, 30, W - 30, H - 30), outline=RED, width=10)
        d.rectangle((58, 58, W - 58, H - 58), outline=(250, 205, 214), width=3)
        if photo_bytes: self._photo(img, photo_bytes, (W // 2 - 85, 85), 170)  # their own photo where the blood drop would be
        else: self._drop(d, W // 2, 175)
        c = W // 2
        d.text((c, 300), self.org.upper(), font=_font(BOLD, 40), fill=RED, anchor="mm")
        d.text((c, 405), "Certificate of Appreciation", font=_font(SERIF, 92), fill=DARK, anchor="mm")
        d.text((c, 505), "proudly presented to", font=_font(PLAIN, 36), fill=SOFT, anchor="mm")
        name_y = 610
        d.text((c, name_y), cert["name"], font=_font(SERIF, 104), fill=RED, anchor="mm")
        d.line((c - 480, name_y + 75, c + 480, name_y + 75), fill=(250, 205, 214), width=3)
        where = f"at {cert['title']}" if cert.get("title") else ""
        d.text((c, 735), f"for donating blood {where}".strip(), font=_font(PLAIN, 40), fill=DARK, anchor="mm")
        d.text((c, 795), f"on {self._date(cert['donated_on'])}" + (f", {cert['venue']}" if cert.get("venue") else ""), font=_font(PLAIN, 36), fill=SOFT, anchor="mm")
        d.text((c, 880), "One donation can save up to three lives. Thank you for being a hero.", font=_font(BOLD, 36), fill=DARK, anchor="mm")
        d.line((220, 1040, 640, 1040), fill=DARK, width=2); d.text((430, 1075), self.org, font=_font(PLAIN, 30), fill=SOFT, anchor="mm")
        d.line((W - 640, 1040, W - 220, 1040), fill=DARK, width=2); d.text((W - 430, 1075), f"Certificate {cert['id'][:8].upper()}", font=_font(PLAIN, 30), fill=SOFT, anchor="mm")
        d.text((c, 1150), f"Verify at {verify_url}", font=_font(PLAIN, 24), fill=SOFT, anchor="mm")
        out = BytesIO(); img.save(out, "PNG", optimize=True); return out.getvalue()

    @staticmethod
    def _drop(d, x, y):
        d.ellipse((x - 70, y - 40, x + 70, y + 100), fill=RED)
        d.polygon([(x - 62, y + 10), (x, y - 110), (x + 62, y + 10)], fill=RED)
        d.ellipse((x - 30, y + 10, x - 5, y + 45), fill=(255, 210, 220))

    @staticmethod
    def _photo(img, data, at, size):
        try:
            p = ImageOps.fit(Image.open(BytesIO(data)).convert("RGB"), (size, size))
            mask = Image.new("L", (size, size), 0); ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
            ImageDraw.Draw(img).ellipse((at[0] - 8, at[1] - 8, at[0] + size + 7, at[1] + size + 7), fill=RED)
            img.paste(p, at, mask)
        except OSError: pass

    @staticmethod
    def _date(s):
        try: return date.fromisoformat(s).strftime("%d %B %Y")
        except (TypeError, ValueError): return s or ""
