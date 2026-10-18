#!/usr/bin/env python3
"""Sort an old resume's lines against the CardFile inventory. Report only; changes nothing.

Usage: import_compare.py OLD.txt [--inventory DIR]
Splits the resume into roles (import_roles.py), matches each to an inventory file, and sorts
each line into ALREADY / REWORDED / CONFLICT / MISSING. Scores are heuristics for Claude to confirm.
"""
import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_resume import load_inventory  # noqa: E402
from import_roles import date_note, match_file, norm, split_roles, toks  # noqa: E402


def facts(s):
    return {n.rstrip(",.") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}, set(re.findall(r"\b[A-Z][a-zA-Z]+", s)[1:])


def classify(line, bullets, bw):
    lt = toks(line)
    cands = sorted(bullets, key=lambda b: -len(lt & bw[b["id"]]) / (len(lt | bw[b["id"]]) or 1))[:3]
    ratio, b = max(((SequenceMatcher(None, " ".join(norm(line)), " ".join(norm(c["text"]))).ratio(), c) for c in cands), key=lambda x: x[0])
    if ratio < 0.5:
        return "MISSING", None, ratio, ""
    (on, oc), (inn, ic) = facts(line), facts(b["text"])
    why = [f"numbers {sorted(on - inn)} vs {sorted(inn - on)}"] if on - inn and inn - on else []
    why += [f"names {sorted(oc - ic)} vs {sorted(ic - oc)}"] if ratio >= 0.7 and oc - ic and ic - oc else []
    return ("CONFLICT" if why else "ALREADY" if ratio >= 0.95 else "REWORDED"), b, ratio, "; ".join(why)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("old", type=Path)
    ap.add_argument("--inventory", type=Path, default=Path(__file__).resolve().parent.parent / "inventory")
    args = ap.parse_args()
    inv_roles, by_id = load_inventory(args.inventory)
    files = [r for r in inv_roles if r["bullets"]]
    bullets = [b for _, b in by_id.values() if not b.get("exclude")]
    bw = {b["id"]: toks(b["text"]) for b in bullets}
    roles = split_roles(args.old.read_text(encoding="utf-8", errors="replace"))
    total = len(roles) - 1
    for k, role in enumerate(roles):
        counts = {}
        print(f"\n=== {'BEFORE FIRST DATED ROLE (contact, summary, skills)' if k == 0 else f'ROLE {k} of {total}: ' + ' / '.join(role['head'])}")
        if k:
            score, fname = match_file(role["head"], files)
            meta = next((r["meta"] for r in files if r["bullets"][0]["file"] == fname), None)
            print(f"  inventory file: {fname} ({score:.2f}) | {meta['title']} | {meta['org']} | {meta['dates']}" if meta else "  inventory file: NONE (ask before creating a new role file)")
            note = date_note(role["head"], meta["dates"]) if meta else ""
            print(f"  {note}" if note else "", end="\n" if note else "")
        for line in role["lines"]:
            if len(line.split()) < 4:
                continue
            g, b, ratio, why = classify(line, bullets, bw)
            counts[g] = counts.get(g, 0) + 1
            print(f"  {g}{f' {b['id']} ({ratio:.2f})' if b else ''}: {line}")
            if g in ("REWORDED", "CONFLICT"):
                print(f"      inventory: {b['text']}" + (f"\n      differs: {why}" if why else ""))
        print(f"  counts: {counts}")


if __name__ == "__main__":
    main()
