"""
Fix filename letters in ``processed_data``.

For files named like ``2015a Clinton Apr.txt``, the letter after the year should
mean the chronological speech index for that speaker within that year:

- first speech in that speaker-year -> ``a``
- second speech in that speaker-year -> ``b``
- ...

The script groups files by ``(speaker, year)``, sorts them by month order
(``Jan``..``Dec``), and renames them accordingly. Non-matching files such as
summary tables are skipped.
"""

from __future__ import annotations

import argparse
import string
import sys
from dataclasses import dataclass
from pathlib import Path

MONTH_ORDER = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    year: int
    original_letter: str
    speaker: str
    month: str


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    default_dir = repo_root / "processed_data"

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=default_dir,
        help=f"folder containing processed text files (default: {default_dir})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned renames without changing anything",
    )
    return p.parse_args()


def parse_file(path: Path) -> ParsedFile | None:
    if path.suffix.lower() != ".txt":
        return None

    parts = path.stem.split()
    if len(parts) != 3:
        return None

    year_letter, speaker, month = parts
    if len(year_letter) != 5 or not year_letter[:4].isdigit():
        return None
    if year_letter[4] not in string.ascii_lowercase:
        return None
    if month not in MONTH_ORDER:
        return None

    return ParsedFile(
        path=path,
        year=int(year_letter[:4]),
        original_letter=year_letter[4],
        speaker=speaker,
        month=month,
    )


def target_name(item: ParsedFile, new_index: int) -> str:
    if not 1 <= new_index <= 26:
        raise ValueError(f"speech index out of range for {item.path.name!r}: {new_index}")
    new_letter = string.ascii_lowercase[new_index - 1]
    return f"{item.year}{new_letter} {item.speaker} {item.month}{item.path.suffix}"


def main() -> int:
    args = parse_args()
    root = args.directory.resolve()

    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    parsed_files: list[ParsedFile] = []
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.name.startswith("~$"):
            continue
        parsed = parse_file(path)
        if parsed is not None:
            parsed_files.append(parsed)

    groups: dict[tuple[str, int], list[ParsedFile]] = {}
    for item in parsed_files:
        groups.setdefault((item.speaker, item.year), []).append(item)

    renames: list[tuple[Path, Path]] = []
    for _, items in sorted(groups.items()):
        ordered = sorted(
            items,
            key=lambda x: (MONTH_ORDER[x.month], x.original_letter, x.path.name),
        )
        for idx, item in enumerate(ordered, start=1):
            new_name = target_name(item, idx)
            if new_name == item.path.name:
                continue
            dest = item.path.with_name(new_name)
            if dest.exists() and dest != item.path:
                print(f"skip (target exists): {item.path.name!r} -> {new_name!r}", file=sys.stderr)
                continue
            renames.append((item.path, dest))

    for src, dst in renames:
        print(f"{src.name!r} -> {dst.name!r}")
        if not args.dry_run:
            src.rename(dst)

    if args.dry_run:
        print(f"(dry-run: {len(renames)} file(s), no changes written)")
    else:
        print(f"renamed {len(renames)} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
