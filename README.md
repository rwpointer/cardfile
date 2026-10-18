# CardFile

**The Character Sheet for Your Career.**

CardFile was inspired by the career counselors of the 1980s, who sat clients down for long interviews and drew out a full inventory of their accomplishments. I wanted that kind of complete record so I could tailor a resume to each job quickly, and I wanted a free tool that could do the interviewing itself. CardFile builds the inventory from two sources: a guided interview with Claude and the resumes you wrote before AI.

Built with Claude Code, CardFile has two parts. The interview tool, like a Dungeon Master running a one-player one-shot, walks you through character creation, turning your career history into an evidence-graded inventory of accomplishments, the character sheet of your career. The builder then assembles resumes, cover letters, and bios by selecting bullets you've already approved, not by generating new text. Every claim traces back to your interview answers or your old resumes, and nothing enters the inventory until you approve it.

## What you need

- [Claude Code](https://claude.com/claude-code)
- Python 3 (standard library only, nothing to install)
- macOS to import `.docx`, `.doc`, `.rtf` and `.pdf` resumes (text extraction uses the built-in `textutil` and PDFKit through `/usr/bin/swift`). Everything else, and `.txt` imports, works anywhere Python does.

## Setup

```
git clone https://github.com/rwpointer/cardfile.git
cd cardfile
ln -s "$(pwd)" ~/.claude/skills/cardfile
ln -s "$(pwd)/cardfile-interview" ~/.claude/skills/cardfile-interview
```

Start a new Claude Code session so it picks up the two skills, `cardfile` and `cardfile-interview`.

Your career data stays local. `.gitignore` excludes `inventory/*.md` (except the template) and `source/`, so the files you create are never committed by accident.

To look around first, use the fictional inventory in `sample/`:

```
python3 scripts/build_resume.py hlb-01 hlb-02 bwc-01 ccp-01 --inventory sample/inventory
python3 scripts/check_source.py sample/sample_source.txt --inventory sample/inventory
```

## Usage

**1. Build your inventory.** The inventory is one markdown file per role in `inventory/` (copy `inventory/_template.md`). Fill it in with the interview tool, which writes only what you approve:

- **Interview.** Ask Claude to use `cardfile-interview` to add a role. It asks one question at a time (scope, responsibilities, tools, people or budgets managed, outcomes, numbers), follows up on vague answers, drafts candidate bullets in your own words, and shows each for approve, edit, or reject. For each approved bullet it asks how you could back it up and sets the evidence level.
- **Import.** Put an old resume (`.docx`, `.doc`, `.rtf`, `.pdf` or `.txt`) in `source/old-resumes/` and ask Claude to import it. Each line is sorted against your inventory as already there, reworded, missing, or in conflict. The inventory is treated as correct, nothing changes without your say-so, and every imported bullet is marked with where it came from.
- **Gap mode.** Give Claude a job posting. It compares the posting to your inventory and interviews you only about what is missing.

**2. Build a document.** Tell Claude the job and the document you want (resume, cover letter, bio, or application). The `cardfile` skill shows you each bullet, with its evidence level and notes, for a yes or no, then runs `scripts/build_resume.py` on the ids you chose and writes `cardfile_draft.txt` in section order. For a resume the bullets are used word for word. For a cover letter or bio, connecting prose may not add facts, numbers, or claims that are not in the selected bullets.

**3. Keep it honest.** `scripts/check_source.py SOURCE.txt` confirms that imported bullets still match the text they came from, word for word.

## Evidence levels

Every bullet carries one of four levels, set from your own account of how you could back it up.

| Level | Meaning | In builds |
|---|---|---|
| `DOCUMENTED` | A record exists that you can produce: a ledger, file, certificate, or published item. | Allowed |
| `DEFENSIBLE` | True and explainable under questioning, but no document in hand. | Allowed |
| `ESTIMATE` | Reconstructed from memory or assumptions. For orientation, never a hard figure. | Blocked unless you pass `--allow-unverified` |
| `VERIFY` | A number, date, or fact that still needs confirming. | Blocked unless you pass `--allow-unverified` |

A bullet with an `exclude:` reason is left out of builds entirely (the scripts never delete a bullet).

## Inventory format

```
---
title: Bakery Operations Manager
org: Harbor Lane Bakery
dates: March 2019 – present
location: Marlow Bay, OR
section: Experience
order: 1
---

- id: hlb-01
  text: Grew weekly wholesale revenue from $4,200 to $9,800 over two years ...
  tags: sales, wholesale, revenue growth
  evidence: DOCUMENTED
  note: Backed by monthly invoices and the 2019-2021 sales ledger.
```

`note` is for warnings and interview prep and is never printed. `source` records where a bullet came from. `inventory/_template.md` documents every field.

## Scripts

| Script | Purpose |
|---|---|
| `build_resume.py` | Assemble chosen bullet ids into a plain-text draft |
| `add_bullets.py` | Write approved bullets, replacements, and note changes into `inventory/` (`--dry-run` shows a diff) |
| `gap_report.py` | Compare a job posting to the inventory |
| `extract_text.py` | Extract text from an old resume (macOS built-in tools) |
| `import_compare.py` | Sort an old resume's lines against the inventory (report only) |
| `check_source.py` | Verify imported bullets against their source text |

Each script is standard library only and has `--help`.

## Tests

```
python3 tests/test_import.py
```

The tests run against the fictional `sample/` inventory, so they pass without any of your data.

## License

MIT. Copyright (c) 2026 Richard Pointer.
