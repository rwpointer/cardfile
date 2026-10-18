#!/usr/bin/env python3
"""Role splitting, inventory-file matching and date checks for import_compare.py.

Standard library only. Imported by import_compare.py; not run directly.
"""
import re

MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
DATE = re.compile(rf"(?:({MON})\s+)?((?:19|20)\d\d)\s*(?:[–—-]+|to)\s*(?:({MON})\s+)?((?:19|20)\d\d|present|current)", re.I)
BULLET = re.compile(r"^\s*[•◦▪·*\-–]\s+")
STOP = {"the", "and", "of", "at", "for", "a", "in", "inc", "llc", "co", "company", "to"}


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ")).split()


def toks(s):
    return {w for w in norm(s) if w not in STOP}


def years(s):
    ys = [int(y) for y in re.findall(r"(?:19|20)\d\d", s)]
    return set(range(min(ys), max(ys) + 1)) if ys else set()


def split_roles(text):
    roles, pending = [{"head": [], "lines": []}], []
    for s in (l.strip() for l in text.splitlines()):
        if not s:
            continue
        if BULLET.match(s):
            if not roles[-1]["lines"] and len(roles) > 1:
                roles[-1]["head"] += pending
            roles[-1]["lines"].append(BULLET.sub("", s))
            pending = []
        elif DATE.search(s) and len(s) < 120:
            roles.append({"head": pending + [s], "lines": []})
            pending = []
        elif s.isupper():
            continue
        elif s[0].islower() and roles[-1]["lines"]:
            roles[-1]["lines"][-1] += " " + s
        elif len(s) > 90 or s.endswith("."):
            roles[-1]["lines"].append(s)
        else:
            pending.append(s)
    return roles


def match_file(head, files):
    text, best = " ".join(head), (0, None)
    for r in files:
        name = toks(r["meta"].get("org", "") + " " + r["meta"].get("title", ""))
        score = 0.7 * len(toks(text) & name) / max(len(name), 1) + (0.3 if years(text) & years(r["meta"].get("dates", "")) else 0)
        best = max(best, (score, r["bullets"][0]["file"]), key=lambda x: x[0])
    return best if best[0] >= 0.35 else (best[0], None)


def date_note(head, dates):
    """Compare the dates in an old resume's role header with an inventory dates field."""
    old, inv = DATE.search(" ".join(head)), DATE.search(dates)
    if not (old and inv):
        return ""
    end = lambda m: m.group(4).lower().replace("current", "present")  # noqa: E731
    if [old.group(2), end(old)] != [inv.group(2), end(inv)]:
        return f"DATES CONFLICT: resume '{old.group(0)}' vs inventory '{dates}'"
    if (old.group(1) or old.group(3)) and not (inv.group(1) or inv.group(3)):
        return f"DATES UPDATE?: '{dates}' -> '{old.group(0)}'"
    return ""
