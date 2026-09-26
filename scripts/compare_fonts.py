"""Compare two font trees table by table.

CI copies the committed fonts aside, rebuilds, and runs this, so a change to
sources/ or scripts/ that was committed without its rebuilt fonts fails the
build instead of shipping stale binaries.

The build timestamp and the checksum that depends on it are ignored; every
other table must compile to the same bytes.
"""
import os, sys
from fontTools.ttLib import TTFont

EXTS = (".otf", ".ttf", ".woff2")


def fonts(root):
    out = {}
    for d, _, files in os.walk(root):
        for n in files:
            if n.endswith(EXTS):
                p = os.path.join(d, n)
                out[os.path.relpath(p, root)] = p
    return out


def tables(path):
    # recalcTimestamp would stamp the compile time back into head.modified.
    f = TTFont(path, recalcTimestamp=False)
    head = f["head"]
    head.modified = head.checkSumAdjustment = 0
    return {t: f[t].compile(f) for t in f.keys() if t != "GlyphOrder"}


def main(committed, built):
    a, b = fonts(committed), fonts(built)
    problems = [f"only committed: {p}" for p in sorted(a.keys() - b.keys())]
    problems += [f"only built: {p}" for p in sorted(b.keys() - a.keys())]
    for rel in sorted(a.keys() & b.keys()):
        ta, tb = tables(a[rel]), tables(b[rel])
        differ = sorted(t for t in ta.keys() | tb.keys() if ta.get(t) != tb.get(t))
        if differ:
            problems.append(f"{rel}: {' '.join(differ)}")
    for p in problems:
        print("STALE", p)
    print(f"{'STALE' if problems else 'ok'}: {len(a)} committed, {len(b)} built, {len(problems)} differences")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: compare_fonts.py <committed-dir> <built-dir>")
    main(*sys.argv[1:])
