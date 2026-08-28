"""Pack the built fonts into release archives.

Archives are reproducible: entries are sorted, permissions are fixed, and every
timestamp comes from SOURCE_DATE_EPOCH or the current commit, so building the
same tag twice produces the same bytes.
"""
import os
import subprocess
import sys
import time
import zipfile

OUT = "dist"

# name -> the paths each archive carries.
ARCHIVES = {
    "": ["fonts/otf", "fonts/ttf", "fonts/variable", "fonts/webfonts",
         "README.md", "UNLICENSE"],
    "-desktop": ["fonts/otf", "README.md", "UNLICENSE"],
    "-web": ["fonts/webfonts", "README.md", "UNLICENSE"],
}


def commit_epoch():
    if "SOURCE_DATE_EPOCH" in os.environ:
        return int(os.environ["SOURCE_DATE_EPOCH"])
    return int(subprocess.run(
        ["git", "log", "-1", "--format=%ct"],
        capture_output=True, text=True, check=True).stdout.strip())


def members(paths):
    """Every file under `paths`, sorted, skipping anything that starts with a dot.

    macOS leaves .DS_Store around, and nothing hidden belongs in a published
    archive. Without this the archives are clean only because ARCHIVES happens
    to name subdirectories rather than fonts/ itself.
    """
    for path in paths:
        if os.path.isfile(path):
            yield path
        else:
            for root, dirs, files in os.walk(path):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for name in sorted(files):
                    if not name.startswith("."):
                        yield os.path.join(root, name)


def build(version, suffix, paths, date_time):
    name = f"Metropolis-{version}{suffix}.zip"
    path = os.path.join(OUT, name)
    count = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member in sorted(members(paths)):
            info = zipfile.ZipInfo(
                f"Metropolis-{version}/{member}", date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(member, "rb") as f:
                z.writestr(info, f.read())
            count += 1
    return name, count, os.path.getsize(path)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: make_dist.py <version>")
    version = sys.argv[1].lstrip("v")

    if not os.path.isdir("fonts/otf"):
        sys.exit("no fonts built; run `make` first")

    os.makedirs(OUT, exist_ok=True)
    date_time = time.gmtime(commit_epoch())[:6]

    for suffix, paths in ARCHIVES.items():
        name, count, size = build(version, suffix, paths, date_time)
        print(f"  {name:38s} {count:2d} files  {size / 1024:6.0f}K")


if __name__ == "__main__":
    main()
