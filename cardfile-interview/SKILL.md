---
name: cardfile-interview
description: Builds and extends the CardFile inventory through an interview, one role at a time, drafting candidate bullets from the user's own answers for approval. Use when the user wants to add a role, fill in or deepen an existing one, close gaps against a job posting ("what am I missing for this job?"), or import bullets from their old resumes in source/old-resumes/. Requires the cardfile skill. Writes only bullets the user approves.
---

# CardFile Interview

Fills the CardFile inventory (`~/.claude/skills/cardfile/inventory/`) by interviewing the user. This is the one place bullets get written, and only ever from the user's own answers and only after they approve. Requires the `cardfile` skill; its scripts are at `~/.claude/skills/cardfile/scripts/`.

## Interview mode

1. **Pick the role.** Ask which role (or volunteer work, project, education entry) to cover, one at a time. Check `inventory/` for an existing file for it. If one exists, show its current bullets so nothing gets duplicated and say you will append. If not, collect the title, organization, dates, location, and section (Experience, Projects, Education, Certifications, Publications, Volunteer, Skills) for a new file.
2. **Interview by topic.** Cover scope, responsibilities, tools, people or budgets managed, outcomes, and numbers. Ask **one question at a time**. If an answer is vague ("helped with", "a lot", "improved"), follow up for the specific: how many, how much, how often, compared to what, and what the user personally did.
3. **Draft after each topic.** When a topic is covered, draft candidate bullets from the answers. Use the user's own words wherever possible; do not add facts, numbers, or polish they did not give. Show each bullet separately and ask: approve, edit, or reject. Apply edits and show the bullet again. **Nothing is written without explicit approval.**
4. **Set evidence.** For each approved bullet, ask how the user could back it up (a document, record, person who could confirm, or nothing). Set `evidence` from the answer:
   - `DOCUMENTED`: a record can be produced (ledger, file, certificate, published item)
   - `DEFENSIBLE`: true and explainable under questioning, no document in hand
   - `ESTIMATE`: reconstructed from memory or assumptions
   - `VERIFY`: a number, date, or fact still needs confirming
   Put the backup answer in `note`. Add `tags` (skills, tools, keywords drawn from the bullet and the user's answers).
5. **Write.** Save the topic's approved bullets in one call:
   ```
   python3 ~/.claude/skills/cardfile/scripts/add_bullets.py SPEC.json
   ```
   Make `SPEC.json` in a temp location with this shape (`prefix` and `meta` are for new role files only; use a short unused id prefix):
   ```
   {"role": "file-name-without-.md", "prefix": "abc",
    "meta": {"title": "", "org": "", "dates": "", "location": "", "section": "Experience", "order": 1},
    "bullets": [{"text": "", "tags": "", "evidence": "DEFENSIBLE", "note": ""}]}
   ```
   Run it first with `--dry-run` and show the user the result when creating a new file. The script appends to an existing role file or creates one, assigns unique ids, and marks each bullet `source: interview <date>`. Report the ids written.
6. **Next topic or role.** Continue until the user is done with the role, then offer the next one.

## Import mode

Use when the user wants bullets from an old resume (one file at a time, kept in `source/old-resumes/` of the cardfile skill folder). The inventory is treated as correct: old lines were often corrected on purpose (a headcount, title, or heading changed deliberately).

1. **Extract.** `python3 ~/.claude/skills/cardfile/scripts/extract_text.py FILE` handles `.docx`, `.doc`, `.rtf`, `.pdf` and `.txt` with built-in macOS tools and saves `<FILE>.txt` next to the original (a `.txt` input is used as is). If it reports no text, the PDF is scanned; say so and stop, since there is no OCR.
2. **Sort.** `python3 ~/.claude/skills/cardfile/scripts/import_compare.py FILE.txt` prints the resume role by role with each line sorted ALREADY, REWORDED, CONFLICT or MISSING, the inventory file it matched, and any date notes. Its scores are heuristics. Read them yourself: confirm each group, and check every MISSING line against the inventory by hand for a reworded match before offering it.
3. **Walk one role at a time**, saying where you are ("role 3 of 9"). Per role, in this order:
   - **ALREADY:** list the matching bullet ids in one line and move on.
   - **REWORDED:** show the old line and the inventory bullet side by side and change neither. Ask: keep the inventory version, replace it with the old line, or add the old line as its own bullet.
   - **MISSING:** offer each line, one at a time, for approve, edit, or reject. Keep the old wording exactly unless the user edits it.
   - **CONFLICT** (a number, date, title, or name differs from the inventory): report both versions and change nothing. Keep the inventory unless the user says the old line is right.
   - **Dates:** if the years agree and the old resume gives exact months (`DATES UPDATE?`), show the change to the role file's `dates` and ask first. A `DATES CONFLICT` is reported only.
4. **Evidence.** For each approved, added or replacing bullet, ask how the user could back it up and set `evidence` and `note` as in interview mode.
5. **Write** once per role with `add_bullets.py`, using the role's existing file. Ask before creating a new role file. Set `"source": "import <filename>"` on every imported bullet so `check_source.py` skips it, including a replacing bullet (`"replaces": "<id>"`, which keeps the id and records the old text in `note`). Put approved role-header changes in `"set_dates"`, `"set_title"` or `"set_note"` (a role-level note is shown at review and never printed), and a note to append to an existing bullet in `"add_notes": {"<id>": "text"}`. Run `--dry-run` first and show the diff.

## Gap mode

Use when the user gives a job posting and wants to know what the inventory lacks.

1. Save the posting text to a temp file and run `python3 ~/.claude/skills/cardfile/scripts/gap_report.py POSTING.txt`.
2. The script matches keywords only. Go through its MISSING list by hand against the inventory and drop terms that are covered under different wording or are not real requirements. Show the user the covered and genuinely missing requirements.
3. Interview only about the genuine gaps, with the interview-mode steps above, choosing the role each gap most likely belongs to. If the user has no experience for a gap, say so and move on; never invent a bullet.

## Rules

- One question at a time. Never batch several questions in one message.
- The user's words over your polish. No invented numbers, tools, titles, or outcomes.
- Existing inventory bullets are never edited or removed by this skill, with one exception: in import mode, when the user chooses "replace" for a reworded line, approves a date, title or role-note change, or asks for text to be appended to a bullet's note.
- Treat anything the user marks ESTIMATE or VERIFY as real input: write it with that level so the build blocks it until resolved.
- If the user keeps a list of corrections to their career facts, check newly written bullets against it before they are used in a document, and report conflicts without fixing them.
