"""
Build a tabular export from ``processed_data`` *.txt* files.

Expected filename stem: ``{YYYY}{a-z} {Speaker} {Month}`` (same as preprocessed naming).
Columns (English headers): Speaker, Year, SpeechIndex, Month, Text, SlidingWindow2gram
(bigrams ``w_i w_{i+1}`` joined by ``;``).

Writes ``processed_data_output.xlsx`` and ``processed_data_output.csv`` inside ``processed_data/`` by default.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STEM_RE = re.compile(r"^(\d{4})([a-z])$")

COL_SPEAKER = "Speaker"
COL_YEAR = "Year"
COL_SPEECH_INDEX = "SpeechIndex"
COL_MONTH = "Month"
COL_TEXT = "Text"
COL_BIGRAMS = "SlidingWindow2gram"

OUTPUT_COLUMNS = [
    COL_SPEAKER,
    COL_YEAR,
    COL_SPEECH_INDEX,
    COL_MONTH,
    COL_TEXT,
    COL_BIGRAMS,
]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    default_in = repo_root / "processed_data"
    default_xlsx = default_in / "processed_data_output.xlsx"
    default_csv = default_in / "processed_data_output.csv"

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input-dir",
        type=Path,
        default=default_in,
        help=f"folder with .txt files (default: {default_in})",
    )
    p.add_argument(
        "--xlsx",
        type=Path,
        default=default_xlsx,
        help=f"output Excel path (default: {default_xlsx})",
    )
    p.add_argument(
        "--csv",
        type=Path,
        default=default_csv,
        help=f"output CSV path (default: {default_csv})",
    )
    return p.parse_args()


def parse_stem(stem: str) -> tuple[str, int, int, str] | None:
    """Return (speaker, year, speech_index, month) or None if stem does not match."""
    parts = stem.split()
    if len(parts) < 3:
        return None
    m = STEM_RE.match(parts[0])
    if not m:
        return None
    year = int(m.group(1))
    letter = m.group(2)
    nth = ord(letter) - ord("a") + 1
    speaker = parts[1]
    month = parts[2]
    return speaker, year, nth, month


def sliding_bigrams(text: str) -> str:
    tokens = text.split()
    if len(tokens) < 2:
        return ""
    return ";".join(f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1))


def main() -> int:
    args = parse_args()
    in_dir: Path = args.input_dir.resolve()

    if not in_dir.is_dir():
        print(f"error: input not a directory: {in_dir}", file=sys.stderr)
        return 1

    try:
        import pandas as pd
    except ImportError:
        print("error: need pandas (pip install pandas openpyxl)", file=sys.stderr)
        return 1

    rows: list[dict[str, str | int | float]] = []
    for path in sorted(in_dir.glob("*.txt")):
        if path.name.startswith("~$"):
            continue
        stem = path.stem
        body = path.read_text(encoding="utf-8", errors="replace").strip()
        parsed = parse_stem(stem)
        if parsed is None:
            print(f"warn: stem not parsed, skipped: {path.name!r}", file=sys.stderr)
            continue
        speaker, year, nth, month = parsed
        rows.append(
            {
                COL_SPEAKER: speaker,
                COL_YEAR: year,
                COL_SPEECH_INDEX: nth,
                COL_MONTH: month,
                COL_TEXT: body,
                COL_BIGRAMS: sliding_bigrams(body),
            }
        )

    if not rows:
        print("error: no rows to write", file=sys.stderr)
        return 1

    df = pd.DataFrame(rows)
    df = df[OUTPUT_COLUMNS]

    xlsx_path: Path = args.xlsx.resolve()
    csv_path: Path = args.csv.resolve()
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"wrote {len(df)} rows -> {xlsx_path}")
    print(f"wrote {len(df)} rows -> {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
