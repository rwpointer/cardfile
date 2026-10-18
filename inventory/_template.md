---
title: <Job Title>
org: <Company or Organization>
dates: <Start> – <End>
location: <City, State>
section: Experience
order: 1
---

<!--
One file per job or role. Copy this file, rename it (e.g. company-role.md),
and fill it in. Files whose names start with "_" are ignored by the script.

Frontmatter:
  section  Resume section this role belongs to (Experience, Projects, Education, ...)
  order    Sort position within its section (1 = top)
  note     Optional: a note about the role itself (shown at review, never printed)

Bullets: each is a list item with three fields.
  id    Unique across the whole inventory. Never reuse or renumber an id.
  text  The bullet exactly as it should appear on the resume.
  tags  Comma-separated skills and keywords, used to match target jobs.
  evidence  Optional: DOCUMENTED, DEFENSIBLE, ESTIMATE or VERIFY. The build
            refuses ESTIMATE/VERIFY bullets unless --allow-unverified is passed.
  note  Optional: warnings and interview prep, shown at review, never printed.
  exclude  Optional: a reason. Bullets with it are left out of builds, gap reports and imports (the
           scripts cannot delete a bullet).
  source  Optional: set by cardfile-interview ("interview <date>") on bullets it writes.
-->

- id: <role-01>
  text: <Bullet text>
  tags: <skill>, <skill>, <keyword>
  evidence: <DOCUMENTED | DEFENSIBLE | ESTIMATE | VERIFY>
  note: <optional warning or interview prep>

- id: <role-02>
  text: <Bullet text>
  tags: <skill>, <keyword>

- id: <role-03>
  text: <Bullet text>
  tags: <skill>, <keyword>, <keyword>
