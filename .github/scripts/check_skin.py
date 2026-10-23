"""Lumen CI checks.

1. Every XML file in the skin parses.
2. The upstream add-on ID (skin.arctic.fuse.3) has not crept back in, e.g. after an upstream merge.
3. kodi-addon-checker passes, ignoring dependency findings: Lumen's dependencies come from the
   jurialmunkey repository, which the checker can't see, so it reports them as missing or too old.
"""
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".github"}
OLD_ID = "skin.arctic.fuse.3"
# Files allowed to mention the upstream ID (credits and history).
OLD_ID_ALLOWED = {"Readme.md", "CHANGES.md"}
IGNORED_CHECKER_ERRORS = re.compile(r"required dependency", re.IGNORECASE)
ANSI_CODES = re.compile(r"\x1b\[[0-9;]*m")


def skin_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(ROOT).parts):
            yield path


def check_xml():
    failures = []
    for path in skin_files():
        if path.suffix.lower() != ".xml":
            continue
        try:
            ET.parse(path)
        except ET.ParseError as err:
            failures.append(f"{path.relative_to(ROOT)}: {err}")
    return failures


def check_old_id():
    failures = []
    for path in skin_files():
        if path.name in OLD_ID_ALLOWED or path.suffix.lower() not in {".xml", ".po", ".json", ".py", ".txt", ".md"}:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if OLD_ID in line:
                failures.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    return failures


def check_addon_checker():
    result = subprocess.run(
        ["kodi-addon-checker", "--branch", "omega", str(ROOT)],
        capture_output=True, text=True, cwd=ROOT.parent,
    )
    # The checker colours its output; strip ANSI codes so lines start with "ERROR:".
    output = ANSI_CODES.sub("", result.stdout + result.stderr)
    print(output)
    return [
        line for line in output.splitlines()
        if line.startswith("ERROR:") and not IGNORED_CHECKER_ERRORS.search(line)
        and not line.startswith("ERROR: We found")
    ]


def main():
    checks = {
        "XML parses": check_xml(),
        f"No {OLD_ID} references": check_old_id(),
        "kodi-addon-checker": check_addon_checker(),
    }
    failed = False
    for name, failures in checks.items():
        print(f"{'FAIL' if failures else 'PASS'}: {name}")
        for failure in failures:
            print(f"  {failure}")
        failed |= bool(failures)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
