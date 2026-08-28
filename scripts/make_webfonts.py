"""Compress built fonts to WOFF2."""
import glob, os, sys
from fontTools.ttLib import TTFont

out = "fonts/webfonts"
os.makedirs(out, exist_ok=True)
rows = []
for src in sorted(glob.glob("fonts/variable/*.ttf")) + sorted(glob.glob("fonts/ttf/*.ttf")):
    f = TTFont(src)
    f.flavor = "woff2"
    dst = os.path.join(out, os.path.splitext(os.path.basename(src))[0] + ".woff2")
    f.save(dst)
    rows.append((os.path.basename(dst), os.path.getsize(src), os.path.getsize(dst)))
for n, a, b in rows:
    print(f"  {n:38s} {a/1024:7.1f}K -> {b/1024:6.1f}K  ({100*b/a:.0f}%)")
print(f"{len(rows)} webfonts")
