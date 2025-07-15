#!/usr/bin/env python
"""CLI: convert clinical protocol PDFs → Markdown files.

Typical workflow
----------------
1. Download or collect PDFs into **data/raw_pdfs/** (or any folder).
2. Run this script to extract text and save cleaned Markdown copies
   into **data/protocols/**.  Those `.md` files are used later for
   embedding + FAISS indexing.

Examples
--------
# Ingest **one** file
python scripts/ingest_protocol.py path/to/file.pdf

# Ingest **all** PDFs in a directory (non‑recursive)
python scripts/ingest_protocol.py --dir data/raw_pdfs

# Ingest **all** PDFs in a directory and sub‑directories
python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pdfplumber
from tqdm import tqdm

from ..utils.transliteration import transliterate_ukrainian

# ---------- config -----------------------------------------------------------
RAW_DIR = Path("data/raw_pdfs")      # default source
OUT_DIR = Path("data/protocols")     # default target for markdown

# -----------------------------------------------------------------------------

def pdf_to_markdown(pdf_path: Path, out_dir: Path = OUT_DIR) -> Path:
    """Read *pdf_path* and write `out_dir/<slug>.md`; return markdown path."""
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    out_dir.mkdir(parents=True, exist_ok=True)

    # ── extract text ──────────────────────────────────────────────────────────
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]
    raw_text = "\n".join(pages_text)

    if not raw_text.strip():
        raise ValueError(f"No extractable text in {pdf_path}")

    # ── derive title and slug ────────────────────────────────────────────────
    first_line = next((ln.strip() for ln in raw_text.splitlines() if ln.strip()), "untitled protocol")
    
    # Transliterate the first line
    transliterated = transliterate_ukrainian(first_line)
    
    slug = (
        re.sub(r"[^a-zA-Z0-9]+", "_", transliterated)
        .strip("_")
        .lower()[:60]
    )

    # ── clean trivial whitespace ─────────────────────────────────────────────
    cleaned = re.sub(r"\n{3,}", "\n\n", raw_text).strip()

    md_path = out_dir / f"{slug}.md"
    md_path.write_text(f"# {first_line}\n\n{cleaned}\n", encoding="utf-8")
    return md_path


def ingest_path(target: Path, recursive: bool = False):
    """Ingest a single PDF or all PDFs inside *target* directory."""
    if target.is_file():
        if target.suffix.lower() != ".pdf":
            sys.stderr.write(f"⚠️  {target} is not a PDF — skipped.\n")
            return
        try:
            out_md = pdf_to_markdown(target)
            try:
                relative_path = out_md.relative_to(Path.cwd())
                print(f"✔️  {target.name} → {relative_path}")
            except ValueError:
                # If paths don't share common parent, just show the filename
                print(f"✔️  {target.name} → {out_md.name}")
        except Exception as e:
            sys.stderr.write(f"⚠️  {target}: {e}\n")
    elif target.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = sorted(target.glob(pattern))
        if not pdf_files:
            sys.stderr.write("(no PDFs found)\n")
            return
        for pdf in tqdm(pdf_files, desc="Converting", unit="file"):
            try:
                pdf_to_markdown(pdf)
            except Exception as e:
                sys.stderr.write(f"⚠️  {pdf}: {e}\n")
    else:
        sys.stderr.write("Error: path must be a PDF file or directory.\n")


# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convert PDF protocols into Markdown files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("pdf", nargs="?", type=Path, help="Single PDF file to ingest")
    group.add_argument("--dir", "-d", type=Path, help="Directory containing PDFs")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into sub‑directories when using --dir")
    args = parser.parse_args()

    target = args.dir if args.dir else args.pdf
    ingest_path(target, recursive=args.recursive)
    print("Done.")


if __name__ == "__main__":
    main()
