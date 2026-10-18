#!/usr/bin/env python3
"""In-place edits to existing inventory files, used by add_bullets.py.

Standard library only. Imported by add_bullets.py; not run directly.
"""
import sys


def set_meta(text, key, value):
    """Set a frontmatter line (title, dates, note, ...), in place if present, else appended."""
    head, sep, rest = text.partition("\n---\n")
    lines, line = head.split("\n"), f"{key}: {value}"
    hit = [n for n, l in enumerate(lines) if l.startswith(f"{key}:")]
    if hit:
        lines[hit[0]] = line
    else:
        lines.append(line)
    return "\n".join(lines) + sep + rest


def _find(text, bid):
    lines = text.split("\n")
    start = lines.index(f"- id: {bid}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("- id:")), len(lines))
    return lines, start, end


def get_field(text, bid, key):
    lines, start, end = _find(text, bid)
    return next((l[len(key) + 4:] for l in lines[start:end] if l.startswith(f"  {key}:")), "")


def set_fields(text, bid, new):
    """Set field lines inside one bullet block, in place if present, else after its last line."""
    lines, start, end = _find(text, bid)
    block = lines[start:end]
    for k, v in new.items():
        for i, l in enumerate(block):
            if l.startswith(f"  {k}:"):
                block[i] = f"  {k}: {v}"
                break
        else:
            block.insert(max(i for i, l in enumerate(block) if l.strip()) + 1, f"  {k}: {v}")
    return "\n".join(lines[:start] + block + lines[end:])


def replace_bullet(text, bid, b, src):
    kept = b["note"] if "note" in b else get_field(text, bid, "note")  # a note in the spec replaces the old one
    new = {"text": b["text"].strip(), "source": src, "note": "Replaced: " + get_field(text, bid, "text") + (" | " + kept if kept else "")}
    if b.get("evidence"):
        new["evidence"] = b["evidence"].upper()
    return set_fields(text, bid, new)


def edit_bullets(spec, by_id, inv_dir, cur, files, today):
    """Apply the spec's "replaces" bullets and "add_notes" ({id: text}); return report lines."""
    edits = [(b["replaces"], b) for b in spec.get("bullets", []) if b.get("replaces")]
    edits += [(bid, None) for bid in spec.get("add_notes", {})]
    report = []
    for bid, b in edits:
        if bid not in by_id:
            sys.exit(f"Unknown bullet id {bid}")
        bp = inv_dir / by_id[bid][1]["file"]
        if b:
            files[bp] = replace_bullet(cur(bp), bid, b, b.get("source") or "interview " + today)
        else:
            old = get_field(cur(bp), bid, "note")
            files[bp] = set_fields(cur(bp), bid, {"note": (old + " | " if old else "") + spec["add_notes"][bid]})
        report.append(f"{bid} {'replaced' if b else 'note added'}")
    return report
