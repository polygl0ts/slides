#!/usr/bin/env python3
"""Build decks.json from the PDFs in decks/"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

REPO_ROOT = Path(__file__).resolve().parent.parent
DECKS_DIR = REPO_ROOT / "decks"
MANIFEST = REPO_ROOT / "decks.json"

# GitHub warns past 50 MB and refuses past 100 MB
MAX_BYTES = 50 * 1024 * 1024
MAX_RECORDING_BYTES = 100 * 1024 * 1024

FILENAME = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.pdf$"
)
RECORDING_SUFFIX = "-recording.mp4"


def title_from_slug(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.split("-"))


def describe(path: Path) -> dict[str, object]:
    """One manifest entry, or raise ValueError saying what's wrong with the file."""
    match = FILENAME.match(path.name)
    if not match:
        raise ValueError(
            f"{path.name}: name must look like YYYY-MM-DD-some-title.pdf "
            "(lowercase letters, digits and dashes only)"
        )

    try:
        date.fromisoformat(match["date"])
    except ValueError:
        raise ValueError(f"{path.name}: {match['date']} is not a real date") from None

    size = path.stat().st_size
    if size > MAX_BYTES:
        raise ValueError(
            f"{path.name}: {size / 1024 / 1024:.1f} MB is over the {MAX_BYTES // 1024 // 1024} MB limit"
        )

    try:
        pages = len(PdfReader(path).pages)
    except (PyPdfError, OSError) as exc:
        raise ValueError(f"{path.name}: not a readable PDF ({exc})") from None

    return {
        "id": path.stem,
        "title": title_from_slug(match["slug"]),
        "date": match["date"],
        "file": path.relative_to(REPO_ROOT).as_posix(),
        "pages": pages,
        "size_bytes": size,
    }


def build() -> list[dict[str, object]]:
    """Build the slide deck from the folder and skip unknown files. Fails if a PDF is unreadable"""
    if not DECKS_DIR.is_dir():
        raise ValueError(f"{DECKS_DIR.relative_to(REPO_ROOT)}/ does not exist")

    errors: list[str] = []
    decks: list[dict[str, object]] = []
    recordings: dict[str, Path] = {}
    for path in sorted(DECKS_DIR.iterdir()):
        if path.name.startswith(".") or not path.is_file():
            continue
        if path.name.endswith(RECORDING_SUFFIX):
            recordings[path.name.removesuffix(RECORDING_SUFFIX)] = path
            continue
        try:
            decks.append(describe(path))
        except ValueError as exc:
            errors.append(str(exc))

    by_id = {str(deck["id"]): deck for deck in decks}
    for deck_id, path in recordings.items():
        if deck_id not in by_id:
            errors.append(f"{path.name}: no {deck_id}.pdf next to it")
            continue
        size = path.stat().st_size
        if size > MAX_RECORDING_BYTES:
            errors.append(
                f"{path.name}: {size / 1024 / 1024:.1f} MB is over the "
                f"{MAX_RECORDING_BYTES // 1024 // 1024} MB limit, see README.md to compress it"
            )
            continue
        by_id[deck_id]["recording"] = path.relative_to(REPO_ROOT).as_posix()

    if errors:
        raise ValueError("\n".join(errors))

    decks.sort(key=lambda d: str(d["id"]), reverse=True)
    return decks


def main() -> int:
    """Main function initiating the deck build."""
    try:
        decks = build()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    MANIFEST.write_text(
        json.dumps(decks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {MANIFEST.relative_to(REPO_ROOT)} with {len(decks)} deck(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
