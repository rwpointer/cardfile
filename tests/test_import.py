#!/usr/bin/env python3
"""Tests for import mode, run on a scratch copy of the inventory with a fake role and resume.

Run: python3 tests/test_import.py   (standard library only; the sample/ inventory is copied, never changed)
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable, "-I"]
SAMPLE_SRC = ROOT / "sample" / "sample_source.txt"

FAKE_ROLE = """---
title: Widget Analyst
org: Fakeco Industries
dates: 2015–2018
location: Nowhere, ZZ
section: Experience
order: 99
---

- id: zz-01
  text: Managed a team of 12 widget assemblers across two shifts at the Springfield plant.
  tags: widgets
  evidence: DOCUMENTED
  source: interview 2026-01-01

- id: zz-02
  text: Reduced widget defects by 30% through a weekly inspection checklist.
  tags: widgets
  evidence: DEFENSIBLE
  source: interview 2026-01-01
"""

FAKE_RESUME = """Jane Placeholder
EXPERIENCE
Widget Analyst, Fakeco Industries
March 2015 – June 2018
• Managed a team of 12 widget assemblers across two shifts at the Springfield plant.
• Supervised a team of 12 widget assemblers working two shifts at the Springfield plant.
• Reduced widget defects by 45% through a weekly inspection checklist.
• Negotiated supplier contracts for packaging materials worth $2 million annually.
Gadget Tester, Otherco
2012 – 2014
• Tested prototype gadgets against written safety standards every week.
"""


def run(script, *args, check=True):
    r = subprocess.run(PY + [str(ROOT / "scripts" / script), *map(str, args)], capture_output=True, text=True)
    if check and r.returncode:
        raise AssertionError(f"{script} failed: {r.stdout}{r.stderr}")
    return r


def digest(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(folder).glob("*.md"))}


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.inv = self.tmp / "inventory"
        shutil.copytree(ROOT / "sample" / "inventory", self.inv)
        (self.inv / "zz-fake.md").write_text(FAKE_ROLE, encoding="utf-8")
        self.old = self.tmp / "old-resumes"
        self.old.mkdir()
        self.txt = self.old / "fake.txt"
        self.txt.write_text(FAKE_RESUME, encoding="utf-8")

    @unittest.skipUnless(shutil.which("textutil"), "needs macOS textutil")
    def test_extract(self):
        self.assertEqual(run("extract_text.py", self.txt).stdout.strip(), str(self.txt))
        self.assertEqual(list(self.old.glob("*.txt")), [self.txt])  # .txt input writes nothing
        subprocess.run(["textutil", "-convert", "docx", str(self.txt), "-output", str(self.old / "fake.docx")], check=True)
        out = Path(run("extract_text.py", self.old / "fake.docx").stdout.strip())
        self.assertEqual(out.name, "fake.docx.txt")
        self.assertIn("Fakeco Industries", out.read_text(encoding="utf-8"))
        self.assertNotEqual(run("extract_text.py", self.old / "fake.xyz", check=False).returncode, 0)

    @unittest.skipUnless(shutil.which("cupsfilter"), "cupsfilter not available")
    def test_extract_pdf(self):
        pdf = self.old / "fake.pdf"
        with pdf.open("wb") as f:
            subprocess.run(["cupsfilter", "-m", "application/pdf", str(self.txt)], stdout=f, stderr=subprocess.DEVNULL, check=True)
        out = Path(run("extract_text.py", pdf).stdout.strip())
        self.assertEqual(out.name, "fake.pdf.txt")
        self.assertIn("Fakeco Industries", out.read_text(encoding="utf-8"))

    def test_compare_groups(self):
        before = digest(self.inv)
        out = run("import_compare.py", self.txt, "--inventory", self.inv).stdout
        for expect in ("ROLE 1 of 2", "ROLE 2 of 2", "inventory file: zz-fake.md", "inventory file: NONE",
                       "DATES UPDATE?: '2015–2018' -> 'March 2015 – June 2018'",
                       "ALREADY zz-01", "REWORDED zz-01", "CONFLICT zz-02", "numbers ['45'] vs ['30']",
                       "MISSING: Negotiated supplier contracts"):
            self.assertIn(expect, out)
        self.assertEqual(digest(self.inv), before)  # report only

    def test_write_replace_dates_and_check_source(self):
        spec = self.tmp / "spec.json"
        spec.write_text(json.dumps({"role": "zz-fake", "set_dates": "March 2015 – June 2018", "bullets": [
            {"text": "Negotiated supplier contracts for packaging materials worth $2 million annually.",
             "tags": "procurement", "evidence": "defensible", "note": "old resume", "source": "import fake.txt"},
            {"replaces": "hlb-02", "evidence": "DEFENSIBLE", "source": "import fake.txt",
             "text": "Managed nine bakers and counter staff across two shifts."}]}), encoding="utf-8")
        before = digest(self.inv)
        run("add_bullets.py", spec, "--inventory", self.inv, "--dry-run")
        self.assertEqual(digest(self.inv), before)  # dry run writes nothing
        self.assertEqual(run("check_source.py", SAMPLE_SRC, "--inventory", self.inv).returncode, 0)

        run("add_bullets.py", spec, "--inventory", self.inv)
        fake = (self.inv / "zz-fake.md").read_text(encoding="utf-8")
        self.assertIn("dates: March 2015 – June 2018", fake)
        self.assertIn("- id: zz-03\n  text: Negotiated supplier", fake)
        self.assertIn("source: import fake.txt", fake)
        self.assertIn("Reduced widget defects by 30%", fake)  # untouched bullet
        dtd = (self.inv / "harbor-lane-bakery.md").read_text(encoding="utf-8")
        block = dtd[dtd.index("- id: hlb-02"):dtd.index("- id: hlb-03")]
        self.assertIn("text: Managed nine bakers and counter staff across two shifts.", block)
        self.assertIn("note: Replaced: Managed a crew of nine bakers and counter staff", block)
        self.assertIn("source: import fake.txt", block)
        self.assertIn("- id: hlb-01", dtd)
        # the replaced bullet no longer matches the source text, but its import source makes check_source skip it
        self.assertEqual(run("check_source.py", SAMPLE_SRC, "--inventory", self.inv).returncode, 0)
        # control: the same rewrite without a source is reported as a mismatch
        (self.inv / "harbor-lane-bakery.md").write_text(dtd.replace("source: import fake.txt\n", "", 1), encoding="utf-8")
        control = run("check_source.py", SAMPLE_SRC, "--inventory", self.inv, check=False)
        self.assertEqual(control.returncode, 1)
        self.assertIn("hlb-02", control.stdout)

    def test_bad_input_is_refused(self):
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"bullets": [{"replaces": "nope-99", "text": "x", "source": "import f.txt"}]}), encoding="utf-8")
        before = digest(self.inv)
        self.assertNotEqual(run("add_bullets.py", bad, "--inventory", self.inv, check=False).returncode, 0)
        self.assertEqual(digest(self.inv), before)


class SampleTests(unittest.TestCase):
    inv = ROOT / "sample" / "inventory"

    def test_check_source_on_sample(self):
        out = run("check_source.py", SAMPLE_SRC, "--inventory", self.inv).stdout
        self.assertIn("0 mismatches", out)
        self.assertIn("1 approved resume lines", out)

    def test_check_source_reports_an_edited_bullet(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        shutil.copytree(self.inv, tmp / "inventory")
        f = tmp / "inventory" / "harbor-lane-bakery.md"
        f.write_text(f.read_text(encoding="utf-8").replace("nine bakers and counter staff", "ten bakers and counter staff", 1), encoding="utf-8")
        r = run("check_source.py", SAMPLE_SRC, "--inventory", tmp / "inventory", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("hlb-02", r.stdout)

    def test_sample_covers_every_evidence_level_and_an_exclusion(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in self.inv.glob("*.md"))
        self.assertEqual(set(re.findall(r"^  evidence: (\w+)", text, re.M)), {"DOCUMENTED", "DEFENSIBLE", "ESTIMATE", "VERIFY"})
        self.assertEqual(len(re.findall(r"^  exclude: ", text, re.M)), 1)

    def test_build_blocks_unverified_and_excluded(self):
        out = Path(tempfile.mkdtemp()) / "draft.txt"
        self.addCleanup(shutil.rmtree, out.parent, ignore_errors=True)
        self.assertEqual(run("build_resume.py", "hlb-01", "hlb-02", "bwc-01", "--inventory", self.inv, "--out", out).returncode, 0)
        for blocked in ("hlb-03", "hlb-04", "rfb-02"):
            r = run("build_resume.py", blocked, "--inventory", self.inv, "--out", out, check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Blocked", r.stderr)
        self.assertEqual(run("build_resume.py", "hlb-03", "--allow-unverified", "--inventory", self.inv, "--out", out).returncode, 0)
        r = run("build_resume.py", "hlb-07", "--allow-unverified", "--inventory", self.inv, "--out", out, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("excluded", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
