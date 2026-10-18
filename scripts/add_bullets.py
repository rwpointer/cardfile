#!/usr/bin/env python3
"""Write user-approved bullets into inventory/ in the CardFile format.

Usage: add_bullets.py SPEC.json [--inventory DIR] [--dry-run]
SPEC: {"role": "file-name", "prefix": "new-files-only", "meta": {title, org, dates,
location, section, order}, "set_dates"/"set_note"/"set_title": new header values,
"bullets": [{"text", "tags", "evidence", "note", "source", "replaces": "bullet id"}],
"add_notes": {"bullet id": "text appended to that bullet's note"}}
New bullets append to the role file (created from meta if missing). A bullet with
"replaces" rewrites that bullet's text in place and keeps the old text in its note.
source defaults to "interview <date>". --dry-run prints a diff. Standard library only.
"""
import argparse
import difflib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_resume import load_inventory  # noqa: E402
from edit_inventory import edit_bullets, set_meta  # noqa: E402

LEVELS = ("DOCUMENTED", "DEFENSIBLE", "ESTIMATE", "VERIFY")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("--inventory", type=Path, default=Path(__file__).resolve().parent.parent / "inventory")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    _, by_id = load_inventory(args.inventory)
    files, report = {}, []

    def cur(p):
        files.setdefault(p, p.read_text(encoding="utf-8") if p.exists() else "")
        return files[p]

    for b in spec.get("bullets", []):
        ev = b.get("evidence", "").upper()
        if not b.get("text", "").strip() or (ev not in LEVELS and (ev or not b.get("replaces"))):
            sys.exit(f"Bullet needs text and evidence in {LEVELS}: {b}")
    new = [b for b in spec.get("bullets", []) if not b.get("replaces")]
    path = args.inventory / (re.sub(r"\.md$", "", spec.get("role", "")) + ".md") if spec.get("role") else None
    if path and path.name.startswith("_"):
        sys.exit("Role file names may not start with '_'")
    keys = [k for k in ("set_dates", "set_note", "set_title") if spec.get(k)]
    if (new or keys) and not path:
        sys.exit("SPEC needs a role")
    for key in keys:
        if not path.exists():
            sys.exit(f"{key} needs an existing role file")
        files[path] = set_meta(cur(path), key[4:], spec[key])
        report.append(key[4:] + " updated")
    if new:
        if path.exists():
            prefixes = {i.rsplit("-", 1)[0] for i, (_, b) in by_id.items() if b["file"] == path.name}
            if len(prefixes) != 1:
                sys.exit(f"Cannot tell which id prefix {path.name} uses: {sorted(prefixes)}")
            prefix, out = prefixes.pop(), ""
        else:
            prefix, meta = spec.get("prefix", ""), spec.get("meta", {})
            if not prefix or any(i.rsplit("-", 1)[0] == prefix for i in by_id):
                sys.exit(f"New role file needs an unused id prefix (got {prefix!r})")
            out = "---\n" + "".join(f"{k}: {meta.get(k, '')}\n" for k in ("title", "org", "dates", "location", "section", "order")) + "---\n"
        n = max([int(i.rsplit("-", 1)[1]) for i in by_id if i.rsplit("-", 1)[0] == prefix and i.rsplit("-", 1)[1].isdigit()] + [0])
        for b in new:
            n += 1
            lines = [f"- id: {prefix}-{n:02d}", f"  text: {b['text'].strip()}", f"  tags: {b.get('tags', '')}", f"  evidence: {b['evidence'].upper()}"]
            lines += [f"  note: {b['note']}"] if b.get("note") else []
            lines.append(f"  source: {b.get('source') or 'interview ' + date.today().isoformat()}")
            out += "\n" + "\n".join(lines) + "\n"
            report.append(f"{prefix}-{n:02d}")
        files[path] = cur(path) + out
    report += edit_bullets(spec, by_id, args.inventory, cur, files, date.today().isoformat())
    for p, text in files.items():
        if args.dry_run:
            old = p.read_text(encoding="utf-8") if p.exists() else ""
            print("\n".join(difflib.unified_diff(old.splitlines(), text.splitlines(), f"a/{p.name}", f"b/{p.name}", lineterm="")))
        else:
            p.write_text(text, encoding="utf-8")
    print(f"{'[dry run] ' if args.dry_run else ''}{', '.join(f'{p.name}' for p in files)}: {', '.join(report)}")


if __name__ == "__main__":
    main()
