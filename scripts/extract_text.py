#!/usr/bin/env python3
"""Extract text from an old resume (.docx, .doc, .rtf, .pdf, .txt) with built-in macOS tools.

Usage: extract_text.py FILE
Writes <FILE>.txt next to the original (e.g. resume.pdf.txt, so a .docx and a .pdf of the
same resume do not collide) and prints its path. A .txt input is used as is.
Word files use textutil; PDFs use PDFKit through /usr/bin/swift. No OCR: scanned PDFs fail.
"""
import subprocess
import sys
from pathlib import Path

PDF_SWIFT = """import PDFKit
let d = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
for i in 0..<d.pageCount { print(d.page(at: i)?.string ?? "") }
"""


def extract(path):
    ext = path.suffix.lower()
    if ext in (".docx", ".doc", ".rtf"):
        run = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)], capture_output=True, text=True)
    elif ext == ".pdf":
        run = subprocess.run(["/usr/bin/swift", "-", str(path)], input=PDF_SWIFT, capture_output=True, text=True)
    else:
        sys.exit(f"Unsupported file type {ext!r}; use .docx, .doc, .rtf, .pdf or .txt")
    if run.returncode:
        sys.exit(f"Extraction failed: {run.stderr.strip()}")
    return run.stdout


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1]).expanduser()
    if not path.is_file():
        sys.exit(f"No such file: {path}")
    if path.suffix.lower() == ".txt":
        print(path)
        return
    text = extract(path)
    if not text.strip():
        sys.exit("No text found. A scanned PDF has no text layer and the built-in tools cannot OCR it.")
    out = path.with_name(path.name + ".txt")
    out.write_text(text, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
