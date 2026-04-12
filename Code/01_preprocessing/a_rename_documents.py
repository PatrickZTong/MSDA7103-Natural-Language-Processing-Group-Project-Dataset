"""
Rename files so every underscore in the filename becomes a space.

Default target directory: <repo_root>/original_ data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    default_dir = repo_root / "original_ data"

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=default_dir,
        help=f"folder containing files to rename (default: {default_dir})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned renames without changing anything",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root: Path = args.directory.resolve()

    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    renames: list[tuple[Path, Path]] = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        old_name = path.name
        new_name = old_name.replace("_", " ")
        if new_name == old_name:
            continue
        dest = path.with_name(new_name)
        if dest.exists() and dest != path:
            print(f"skip (target exists): {path.name!r} -> {new_name!r}", file=sys.stderr)
            continue
        renames.append((path, dest))

    for src, dst in renames:
        print(f"{src.name!r} -> {dst.name!r}")
        if not args.dry_run:
            src.rename(dst)

    if args.dry_run and renames:
        print(f"(dry-run: {len(renames)} file(s), no changes written)")
    elif not args.dry_run and renames:
        print(f"renamed {len(renames)} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
