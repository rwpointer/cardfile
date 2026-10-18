#!/usr/bin/env python3
"""Compare a job posting to the inventory: which key terms are covered, which are missing.

Usage: gap_report.py POSTING.txt [--inventory DIR] [--top N]
Keyword matching only; check the missing list for synonyms by hand. Standard library only.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_resume import load_inventory  # noqa: E402

STOP = set("""a an and are as at be by for from has have in is it its of on or our that the their this to we will with you your
who what when where which while about across all also any can do more most must new not other out over per such than then
they these those up use used using work working years year experience ability strong skills team teams role job position
candidate required preferred responsibilities including related s""".split())


def stem(w):
    return re.sub(r"(ing|ed|es|s|e|d)$", "", w) if len(w) > 4 else w


def terms(text, top):
    words = re.findall(r"[a-z0-9+#/.-]+", text.lower())
    words = [w.strip(".-/") for w in words]
    grams = Counter()
    for n in (1, 2):
        for i in range(len(words) - n + 1):
            g = words[i:i + n]
            if all(w and w not in STOP and len(w) > 2 for w in g):
                grams[" ".join(g)] += 1
    ranked = sorted(grams.items(), key=lambda kv: (-kv[1], -len(kv[0])))
    return [t for t, c in ranked if c > 1 or " " not in t][:top]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("posting", type=Path)
    ap.add_argument("--inventory", type=Path, default=Path(__file__).resolve().parent.parent / "inventory")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()
    _, by_id = load_inventory(args.inventory)
    hay = {i: " ".join(stem(w) for w in re.findall(r"[a-z0-9+#/.-]+", (b["text"] + " " + b["tags"]).lower())) for i, (_, b) in by_id.items() if not b.get("exclude")}
    covered, missing = [], []
    for t in terms(args.posting.read_text(encoding="utf-8", errors="replace"), args.top):
        key = " ".join(stem(w) for w in t.split())
        ids = [i for i, h in hay.items() if re.search(r"(?<!\w)" + re.escape(key), h)]
        (covered if ids else missing).append((t, ids))
    print(f"COVERED ({len(covered)})")
    for t, ids in covered:
        print(f"  {t}: {', '.join(ids[:6])}{' ...' if len(ids) > 6 else ''} ({len(ids)})")
    print(f"\nMISSING ({len(missing)})")
    for t, _ in missing:
        print(f"  {t}")


if __name__ == "__main__":
    main()
