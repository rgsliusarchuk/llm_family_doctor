#!/usr/bin/env python
"""Batch-download clinical protocols (PDF) from a web page.

Usage examples
--------------
# default CSS selector (links that start with /documents/)
python scripts/download_protocols.py --url "https://your-website.com/page-with-documents"

# custom selector (e.g. any link that ends with .pdf)
python scripts/download_protocols.py --url "https://example.com/list" \
                                     --selector "a[href$='.pdf']"

# change destination folder
python scripts/download_protocols.py --url https://… --out data/raw_pdfs
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

DEFAULT_SELECTOR = "a[href^='/documents/']"  # customise per site
DEFAULT_OUT_DIR = Path("data/raw_pdfs")
CHUNK = 2 ** 14  # 16 KB

def fetch_links(base_url: str, selector: str) -> list[str]:
    """Return absolute URLs of all matching <a> tags."""
    resp = requests.get(base_url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tags = soup.select(selector)
    if not tags:
        sys.stderr.write("⚠️  No links matched the selector — check the CSS selector or page structure.\n")
    return [urljoin(base_url, tag["href"]) for tag in tags]


def download_file(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK):
                if chunk:
                    f.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download PDF protocols from a web page")
    parser.add_argument("--url", required=True, help="Page that lists the protocol links")
    parser.add_argument("--selector", default=DEFAULT_SELECTOR, help="CSS selector for <a> tags (default: %(default)s)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="Destination folder (default: %(default)s)")
    args = parser.parse_args()

    links = fetch_links(args.url, args.selector)
    if not links:
        return

    print(f"Found {len(links)} links. Downloading…")
    for link in tqdm(links, unit="file"):
        filename = link.split("/")[-1]
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        out_path = args.out / filename
        try:
            download_file(link, out_path)
        except Exception as e:
            sys.stderr.write(f"⚠️  {link} — {e}\n")
    print("✔️  Done. PDFs saved to", args.out.resolve())


if __name__ == "__main__":
    main() 