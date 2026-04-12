"""
Standardize filenames under ``original_ data`` (or a chosen folder).

分类讨论（两类互斥，按顺序只命中其一）：

**第一类 — 文件名以数字开头**（去掉首尾空白后，第一个字符是数字）  
  ① 从**整个主文件名**最右端开始，连续去掉数字，再去掉尾部空格。  
  ② 若**最后一个 sec** 能识别为月份（与第二类同一套表），则改为**三字母英文缩写**（如 ``December``/``oct`` → ``Dec``/``Oct``）。  
  例：``2023a Harris Feb3`` → ``2023a Harris Feb``；``2024j Harris oct31`` → ``2024j Harris Oct``。  
  **不会**再按「人名 + 篇号 + 月 + 年」做第二类解析。

**第二类 — 文件名以人名为第一 sec**（且**不属于**第一类）  
  第一个空格分段必须是 Biden / Trump / Clinton / Harris（大小写不敏感）。  
  共 4 个 sec：演讲者、同字母重复（个数 = 该年第几篇）、月份、两位年份（20xx）。  
  重命名为 ``{YYYY}{a-z} {Speaker} {Mon}``。  
  例：``Biden dd feb 20`` → ``2020b Biden Feb``。
"""

from __future__ import annotations

import argparse
import re
import string
import sys
from enum import Enum
from pathlib import Path

SPEAKERS = frozenset({"biden", "trump", "clinton", "harris"})

MONTH_TO_ABBR = {
    "jan": "Jan",
    "january": "Jan",
    "feb": "Feb",
    "february": "Feb",
    "mar": "Mar",
    "march": "Mar",
    "apr": "Apr",
    "april": "Apr",
    "may": "May",
    "jun": "Jun",
    "june": "Jun",
    "jul": "Jul",
    "july": "Jul",
    "aug": "Aug",
    "august": "Aug",
    "sep": "Sep",
    "sept": "Sep",
    "september": "Sep",
    "oct": "Oct",
    "october": "Oct",
    "nov": "Nov",
    "november": "Nov",
    "dec": "Dec",
    "december": "Dec",
}


class FilenameKind(Enum):
    """Which renaming branch applies (mutually exclusive)."""

    DIGIT_PREFIX = "digit_prefix"
    SPEAKER_PREFIX = "speaker_prefix"
    OTHER = "other"


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


def split_stem_sections(stem: str) -> list[str]:
    return [p for p in re.split(r"\s+", stem.strip()) if p]


def classify_stem(stem: str) -> tuple[FilenameKind, list[str]]:
    """
    先判断是否「以数字开头」；只有不是第一类时，才看第一 sec 是否为人名。
    """
    parts = split_stem_sections(stem)
    head = stem.lstrip()
    if not head:
        return FilenameKind.OTHER, parts
    if head[0].isdigit():
        return FilenameKind.DIGIT_PREFIX, parts
    if parts and parts[0].lower() in SPEAKERS:
        return FilenameKind.SPEAKER_PREFIX, parts
    return FilenameKind.OTHER, parts


def strip_trailing_digits_from_stem(stem: str) -> str:
    s = stem.rstrip()
    while s and s[-1].isdigit():
        s = s[:-1]
    return s.rstrip()


def abbreviate_last_month_if_known(parts: list[str]) -> list[str]:
    """若最后一段是已知月份，换成三字母缩写（与 MONTH_TO_ABBR 一致）。"""
    if not parts:
        return parts
    key = parts[-1].lower()
    if key not in MONTH_TO_ABBR:
        return parts
    out = list(parts)
    out[-1] = MONTH_TO_ABBR[key]
    return out


def rule_digit_prefix(stem: str, suffix: str) -> str | None:
    """第一类：去末尾数字；再把末尾月份规范为三字母缩写。"""
    after_digits = strip_trailing_digits_from_stem(stem)
    parts = abbreviate_last_month_if_known(split_stem_sections(after_digits))
    final_stem = " ".join(parts)
    if final_stem == stem:
        return None
    return f"{final_stem}{suffix}"


def is_letter_run(token: str) -> bool:
    if not token or not token.isalpha() or not token.islower():
        return False
    return len(set(token)) == 1


def index_to_letter(n: int) -> str:
    if n < 1 or n > len(string.ascii_lowercase):
        raise ValueError(f"speech index out of a-z range: {n}")
    return string.ascii_lowercase[n - 1]


def normalize_month(token: str) -> str:
    key = token.lower()
    if key not in MONTH_TO_ABBR:
        raise ValueError(f"unknown month token: {token!r}")
    return MONTH_TO_ABBR[key]


def parse_two_digit_year(token: str) -> int:
    if not re.fullmatch(r"\d{2}", token):
        raise ValueError(f"expected 2-digit year, got {token!r}")
    return 2000 + int(token)


def rule_speaker_prefix(parts: list[str], suffix: str) -> str:
    """第二类：按 4 sec 规则生成新主文件名。"""
    if len(parts) != 4:
        raise ValueError(f"expected 4 sections, got {len(parts)}: {parts!r}")

    speaker_raw, letters, month_raw, yy = parts
    speaker_key = speaker_raw.lower()
    if speaker_key not in SPEAKERS:
        raise ValueError(f"unknown speaker: {speaker_raw!r}")

    if not is_letter_run(letters):
        raise ValueError(f"invalid speech index token: {letters!r}")

    n = len(letters)
    letter = index_to_letter(n)
    year = parse_two_digit_year(yy)
    month_abbr = normalize_month(month_raw)

    speaker_title = speaker_raw[:1].upper() + speaker_raw[1:].lower()
    new_stem = f"{year}{letter} {speaker_title} {month_abbr}"
    return f"{new_stem}{suffix}"


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

        stem = path.stem
        suffix = path.suffix
        kind, parts = classify_stem(stem)

        new_name: str | None = None

        if kind is FilenameKind.DIGIT_PREFIX:
            new_name = rule_digit_prefix(stem, suffix)

        elif kind is FilenameKind.SPEAKER_PREFIX:
            try:
                new_name = rule_speaker_prefix(parts, suffix)
            except ValueError as e:
                print(f"skip [第二类 invalid] ({e}): {path.name!r}", file=sys.stderr)
                continue

        else:
            # 两类都不属于：不改名
            continue

        if new_name is None or new_name == path.name:
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
