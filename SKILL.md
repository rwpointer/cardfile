---
name: cardfile
description: CardFile, the Character Sheet for Your Career. Builds a tailored document from the user's existing bullet inventory by having them approve bullets one at a time. Use when the user names a target job, role, posting, or application and wants a resume, cover letter, bio, or application answers drafted from their inventory. Selects from inventory/ and never writes or rewrites bullets; to add or fill gaps in the inventory use cardfile-interview.
---

# CardFile: The Character Sheet for Your Career

CardFile keeps a career as an inventory of approved bullets, each with an id, tags, and an evidence level. For any target job or application, the user selects bullets from the inventory and a script assembles the draft. A resume is the first use; cover letters, bios, and applications draw on the same inventory. The inventory is the single source of truth: do not generate, rewrite, merge, or "improve" bullets.

## Inventory format

One markdown file per job or role in `inventory/` (see `inventory/_template.md`). Frontmatter gives `title`, `org`, `dates`, `location`, `section`, and `order`. Each bullet is a list item with `id`, `text`, and `tags`, plus optional `evidence` (DOCUMENTED, DEFENSIBLE, ESTIMATE or VERIFY), `note` (warnings and interview prep, never printed), `source` (set on bullets written by cardfile-interview), and `exclude` (a reason; the bullet is left out of builds, so skip it when presenting bullets). Files starting with `_` are ignored. Bullets imported from a document keep that document's extracted text in `source/`, and `python3 scripts/check_source.py SOURCE.txt` confirms every imported bullet still matches it word for word (bullets with a `source:` field are skipped).

## Workflow

1. **Get the target.** Ask the user to name the target (job title, company, posting text if they have it) and which document they want: resume, cover letter, bio, or application. Note the key skills and keywords it calls for.
2. **Read the inventory.** Read every non-template file in `inventory/`. If it is empty or only holds the template, stop and point the user to cardfile-interview.
3. **Present bullets for yes/no.** Go role by role, in section and `order` order. For each bullet show its id, its text verbatim, its tags, its `evidence` level, and its `note` if it has one (notes carry the caveats that decide whether a claim is safe on paper), plus a one-line remark if its tags match the target. Skip bullets that have an `exclude` field. Offer ESTIMATE and VERIFY bullets as unavailable until the user resolves them. Ask for yes or no. Present a few at a time if the inventory is long, but always get an explicit answer for each bullet. Do not pre-select or skip bullets on the user's behalf.
4. **Confirm the selection.** List the ids marked yes and let the user change any answers.
5. **Build the draft.** Run:
   ```
   python3 ~/.claude/skills/cardfile/scripts/build_resume.py <id> <id> ... --out cardfile_draft.txt
   ```
   The script reads the `inventory/` folder in this skill's directory no matter where it is run from; `--out` is relative to the current directory. It groups bullets by section and role, keeps inventory order, and errors on unknown or duplicate ids. It also refuses any bullet with ESTIMATE or VERIFY evidence; add `--allow-unverified` only if the user explicitly asks for it. Report the output path.
6. **Other documents.** For a resume, the draft is the deliverable. For a cover letter, bio, or application answer, the selected bullets are the only source of facts: write connecting prose around them, add no claim that is not in a selected bullet, show the draft, and let the user edit it.

## Rules

- Bullet text comes only from the inventory, verbatim. If the user wants a bullet changed, they edit the inventory file or use cardfile-interview; do not edit it in the draft.
- If no bullet fits a requirement of the target, say so and offer cardfile-interview's gap mode; do not write one to fill the gap.
- If the user keeps a list of corrections to their career facts, check the selected bullets against it before building and report any conflicts; do not fix wording yourself.
- Connecting prose in cover letters and bios may not add facts, numbers, or claims that are not in the selected bullets.
- Don't reuse a yes/no answer from an earlier target without asking.
