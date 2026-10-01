"""Select CI work from the complete Git diff, including deleted/renamed paths."""
import json
import os
from pathlib import Path
import subprocess
import sys


JOBS = ("fonts", "rebuild", "artwork", "site")
NON_BUILD_SCRIPTS = {
    "scripts/check_fonts.py", "scripts/make_specimen_image.py",
    "scripts/ci_changes.py", "scripts/make_dist.py",
    "scripts/extend_charset.py", "scripts/add_tabular_figures.py",
}
VARIABLE_WEBFONTS = {
    "fonts/webfonts/Metropolis[wght].woff2",
    "fonts/webfonts/Metropolis-Italic[wght].woff2",
}
ARTWORK_INPUTS = {
    "scripts/make_specimen_image.py", "make/artwork.mk",
    "requirements-artwork.txt", "requirements-check.txt",
    "documentation/cover-city.jpg", "documentation/specimen.svg",
    "documentation/social-preview.svg", "documentation/specimen-light.svg",
    "documentation/specimen-dark.svg", "documentation/social-preview.jpg",
}


def classify(paths):
    work = dict.fromkeys(JOBS, False)
    for path in paths:
        rebuild = (
            (path.startswith(("sources/", "fonts/")) and not path.endswith((".md", ".txt")))
            or path in {"Makefile", "make/fonts.mk", "requirements.txt", "requirements-check.txt"}
            or (path.startswith("make/") and path not in {"make/artwork.mk", "make/specimen.mk"})
            or (path.startswith("scripts/") and path not in NON_BUILD_SCRIPTS)
        )
        work["rebuild"] |= rebuild
        work["fonts"] |= rebuild or path == "scripts/check_fonts.py"
        work["artwork"] |= (
            path.startswith("fonts/variable/") or path in ARTWORK_INPUTS
            or path == "Makefile"
        )
        # README/license/editor files do not change the generated website.
        site = path.startswith("specimen/") and not (
            (path.count("/") == 1 and path.endswith((".md", ".txt")))
            or Path(path).name in {".gitignore", ".editorconfig", ".prettierignore", ".eslintignore"}
        )
        work["site"] |= site or path in VARIABLE_WEBFONTS or path in {
            "Makefile", "make/specimen.mk", ".bun-version", ".github/workflows/pages.yml",
        }
    return work


def git(*args):
    return subprocess.check_output(["git", *args])


def ensure_commit(sha):
    try:
        git("cat-file", "-e", f"{sha}^{{commit}}")
    except subprocess.CalledProcessError:
        git("fetch", "--no-tags", "--depth=1", "origin", sha)


def changed_paths(event_name, event):
    if event_name == "pull_request":
        base = event["pull_request"]["base"]["sha"]
        head = event["pull_request"]["head"]["sha"]
        ensure_commit(base)
        ensure_commit(head)
        base = git("merge-base", base, head).decode().strip()
    elif event_name == "push":
        base, head = event["before"], event["after"]
        if not base.strip("0"):
            return None
        ensure_commit(base)
        ensure_commit(head)
    else:
        return None
    return diff_paths(base, head)


def diff_paths(base, head):
    # --no-renames checks both sides of a move. NUL handles unusual filenames.
    data = git("diff", "--name-only", "--no-renames", "-z", base, head)
    return [p for p in data.decode().split("\0") if p]


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--site-current":
        latest = sys.argv[2]
        ensure_commit(latest)
        # A README/cover edit does not invalidate a site already built.
        current = not classify(diff_paths("HEAD", latest))["site"]
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"deploy={str(current).lower()}\n")
        print("Site inputs still match main." if current else "Newer site inputs on main; skipping deployment.")
        return
    event_name = os.environ["GITHUB_EVENT_NAME"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    try:
        paths = changed_paths(event_name, event)
    except (KeyError, subprocess.CalledProcessError) as exc:
        print(f"::warning::Cannot establish the changed files; running all checks ({exc}).")
        paths = None
    work = dict.fromkeys(JOBS, True) if paths is None else classify(paths)
    lines = [f"{name}={str(enabled).lower()}" for name, enabled in work.items()]
    print("\n".join(lines))
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write("| Work | Needed |\n|---|---|\n")
        for name, enabled in work.items():
            f.write(f"| {name} | {'yes' if enabled else 'no'} |\n")


if __name__ == "__main__":
    main()
