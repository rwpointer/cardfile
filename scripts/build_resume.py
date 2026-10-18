#!/usr/bin/env python3
"""Build a plain-text CardFile draft (resume, cover letter notes, bio) from selected bullet ids.

Usage: build_resume.py ID [ID ...] [--inventory DIR] [--out FILE] [--allow-unverified]
Ids may be space- or comma-separated. Standard library only.
"""
import argparse
import re
import sys
from pathlib import Path

SECTION_ORDER = ["Experience", "Projects", "Research", "Education", "Certifications", "Publications", "Volunteer", "Skills"]
BLOCKED = ("ESTIMATE", "VERIFY")
FIELD = re.compile(r"^\s*-?\s*(id|text|tags|evidence|note|source|exclude):\s*(.*)$")


def parse_role(path):
    """Return (meta, bullets) for one inventory file."""
    raw = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    meta, bullets, body = {}, [], raw
    if raw.startswith("---"):
        _, front, body = raw.split("---", 2)
        for line in front.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    for line in body.splitlines():
        m = FIELD.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if key == "id":
            bullets.append({"id": value, "text": "", "tags": "", "evidence": "", "file": path.name})
        elif bullets:
            bullets[-1][key] = value
    return meta, bullets


def load_inventory(inv_dir):
    roles, by_id = [], {}
    for path in sorted(inv_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, bullets = parse_role(path)
        role = {"meta": meta, "bullets": bullets}
        roles.append(role)
        for b in bullets:
            if b["id"] in by_id:
                sys.exit(f"Duplicate id {b['id']!r} in {b['file']} and {by_id[b['id']][1]['file']}")
            by_id[b["id"]] = (role, b)
    return roles, by_id


def section_key(name):
    return (SECTION_ORDER.index(name), "") if name in SECTION_ORDER else (len(SECTION_ORDER), name)


def build(roles, chosen):
    sections = {}
    for role in roles:
        picked = [b for b in role["bullets"] if b["id"] in chosen]
        if picked:
            sections.setdefault(role["meta"].get("section", "Experience"), []).append((role, picked))
    lines = []
    for name in sorted(sections, key=section_key):
        lines += [name.upper(), "=" * len(name), ""]
        entries = sorted(sections[name], key=lambda e: int(e[0]["meta"].get("order", 999)))
        for role, picked in entries:
            m = role["meta"]
            lines.append(" | ".join(v for v in (m.get("title"), m.get("org")) if v))
            sub = " | ".join(v for v in (m.get("dates"), m.get("location")) if v)
            if sub:
                lines.append(sub)
            lines += [f"  - {b['text']}" for b in picked] + [""]
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ids", nargs="+", help="bullet ids marked yes")
    ap.add_argument("--inventory", type=Path, default=Path(__file__).resolve().parent.parent / "inventory")
    ap.add_argument("--out", type=Path, default=Path("cardfile_draft.txt"))
    ap.add_argument("--allow-unverified", action="store_true", help="permit ESTIMATE/VERIFY bullets")
    args = ap.parse_args()

    chosen = {i.strip() for arg in args.ids for i in re.split(r"[,\s]+", arg) if i.strip()}
    roles, by_id = load_inventory(args.inventory)
    unknown = sorted(chosen - {i for i, (_, b) in by_id.items() if not b.get("exclude")})
    if unknown:
        sys.exit(f"Unknown or excluded bullet ids: {', '.join(unknown)}")
    blocked = sorted(i for i in chosen if by_id[i][1]["evidence"].upper() in BLOCKED)
    if blocked and not args.allow_unverified:
        sys.exit(f"Blocked (ESTIMATE/VERIFY evidence): {', '.join(blocked)}. Pass --allow-unverified to override.")
    args.out.write_text(build(roles, chosen), encoding="utf-8")
    print(f"Wrote {len(chosen)} bullets to {args.out}")


if __name__ == "__main__":
    main()
