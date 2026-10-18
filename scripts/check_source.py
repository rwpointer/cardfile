#!/usr/bin/env python3
"""Check that every inventory bullet appears word for word in the text it was imported from.

Usage: check_source.py [SOURCE.txt] [--inventory DIR] [--footer REGEX]
SOURCE.txt is any extracted text file (default: the one .txt file in source/). Page-number
footer lines (default: any line ending in "Page N") are removed before matching.
Bullets with a `source:` field (written by cardfile-interview) are skipped.
Bullets whose note starts "Approved resume line" must instead match a quoted
resume line in the source. Reports mismatches only; never edits files.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_resume import load_inventory  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FOOTER = r"^.*\bPage \d+(?: of \d+)?[ \t]*$"


def norm(s, footer=FOOTER):
    s = re.sub(footer, "", s, flags=re.M)
    s = re.sub(r"-\s*\n\s*", "-", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", nargs="?", type=Path)
    ap.add_argument("--footer", default=FOOTER, help="regex for page footer lines to drop")
    ap.add_argument("--inventory", type=Path, default=ROOT / "inventory")
    args = ap.parse_args()

    if args.source is None:
        found = sorted((ROOT / "source").glob("*.txt"))
        if len(found) != 1:
            sys.exit("Pass the extracted source text: check_source.py SOURCE.txt")
        args.source = found[0]
    src = norm(args.source.read_text(encoding="utf-8"), args.footer)
    roles, by_id = load_inventory(args.inventory)
    bad, approved = [], 0
    for bid, (_, b) in sorted(by_id.items()):
        if b.get("source"):
            continue
        text = norm(b["text"])
        pos = src.find(text)
        if b.get("note", "").startswith("Approved resume line"):
            approved += 1
            if pos < 0 or "resume line" not in src[max(0, pos - 600):pos].lower():
                bad.append((b["file"], bid, "approved resume line not found in source", b["text"]))
        elif pos < 0:
            bad.append((b["file"], bid, "text not found word for word", b["text"]))
    for f, bid, why, text in bad:
        print(f"MISMATCH {f} {bid}: {why}\n    {text}")
    print(f"{len(by_id)} bullets checked ({approved} approved resume lines), {len(bad)} mismatches")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
