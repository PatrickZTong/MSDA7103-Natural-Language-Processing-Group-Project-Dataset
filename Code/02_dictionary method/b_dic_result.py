"""
Dictionary result reporting with cycle comparisons and timeline plots.

Outputs are written to:
``result/dictionary_method_results/``
"""

from __future__ import annotations

import argparse
import calendar
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MONTH_NUM = {calendar.month_abbr[i]: i for i in range(1, 13)}
SPEAKER_STYLES = {
    "Trump": {"color": "#d62728", "label": "Trump"},
    "Clinton": {"color": "#1f77b4", "label": "H. Clinton"},
    "Biden": {"color": "#5fa8ff", "label": "Biden"},
    "Harris": {"color": "#9ec9ff", "label": "Harris"},
}


@dataclass(frozen=True)
class CycleSpec:
    slug: str
    label: str
    start_year: int
    end_year: int
    election_year: int
    opponent_speaker: str
    opponent_label: str


CYCLES = [
    CycleSpec("2015_2016", "2015-2016", 2015, 2016, 2016, "Clinton", "H. Clinton"),
    CycleSpec("2019_2020", "2019-2020", 2019, 2020, 2020, "Biden", "Biden"),
    CycleSpec("2023_2024", "2023-2024", 2023, 2024, 2024, "Harris", "Harris"),
]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    default_xlsx = repo_root / "processed_data" / "processed_data_output.xlsx"
    default_out = repo_root / "result" / "dictionary_method_results"

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xlsx", type=Path, default=default_xlsx, help=f"input Excel file (default: {default_xlsx})")
    p.add_argument(
        "--output-dir",
        type=Path,
        default=default_out,
        help=f"output directory (default: {default_out})",
    )
    return p.parse_args()


def month_to_num(month: str) -> int:
    if month not in MONTH_NUM:
        raise ValueError(f"unknown month abbreviation: {month!r}")
    return MONTH_NUM[month]


def get_score_columns(df) -> list[str]:
    return [c for c in df.columns if c.endswith("_score")]


def ensure_required_columns(df, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def pretty_score_name(score_col: str) -> str:
    base = score_col.removesuffix("_score")
    if base.endswith("_gt"):
        base = base[:-3]
    words = [w.capitalize() for w in base.split("_") if w]
    return f"{' '.join(words)} Dictionary Score"


def clear_previous_outputs(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    for path in out_dir.rglob("*"):
        if path.is_file():
            path.unlink()


def make_monthly_series(pd, df, cycle: CycleSpec, score_cols: list[str]):
    cycle_df = df[
        (df["Year"] >= cycle.start_year)
        & (df["Year"] <= cycle.end_year)
        & (df["Speaker"].isin(["Trump", cycle.opponent_speaker]))
    ].copy()

    if cycle_df.empty:
        return cycle_df

    cycle_df["MonthNum"] = cycle_df["Month"].map(month_to_num)
    cycle_df["Date"] = pd.to_datetime(dict(year=cycle_df["Year"], month=cycle_df["MonthNum"], day=1))
    monthly = (
        cycle_df.groupby(["Speaker", "Date"], as_index=False)[score_cols]
        .mean(numeric_only=True)
        .sort_values(["Speaker", "Date"])
    )

    full_months = pd.date_range(start=f"{cycle.start_year}-01-01", end=f"{cycle.end_year}-12-01", freq="MS")

    frames = []
    for speaker in ["Trump", cycle.opponent_speaker]:
        sub = monthly[monthly["Speaker"] == speaker].copy()
        sub = sub.set_index("Date").reindex(full_months)
        sub["Speaker"] = speaker
        sub.index.name = "Date"
        sub = sub.reset_index()
        frames.append(sub)
    return pd.concat(frames, ignore_index=True)


def make_full_timeline_monthly_series(pd, df, score_cols: list[str]):
    keep_speakers = ["Trump", "Clinton", "Biden", "Harris"]
    work = df[df["Speaker"].isin(keep_speakers)].copy()
    work["MonthNum"] = work["Month"].map(month_to_num)
    work["Date"] = pd.to_datetime(dict(year=work["Year"], month=work["MonthNum"], day=1))
    monthly = (
        work.groupby(["Speaker", "Date"], as_index=False)[score_cols]
        .mean(numeric_only=True)
        .sort_values(["Speaker", "Date"])
    )

    full_months = pd.date_range(
        start=f"{int(work['Year'].min())}-01-01",
        end=f"{int(work['Year'].max())}-12-01",
        freq="MS",
    )

    frames = []
    for speaker in keep_speakers:
        sub = monthly[monthly["Speaker"] == speaker].copy()
        sub = sub.set_index("Date").reindex(full_months)
        sub["Speaker"] = speaker
        sub.index.name = "Date"
        sub = sub.reset_index()
        frames.append(sub)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    args = parse_args()
    xlsx_path = args.xlsx.resolve()
    out_dir = args.output_dir.resolve()

    if not xlsx_path.is_file():
        print(f"error: input Excel file not found: {xlsx_path}", file=sys.stderr)
        return 1

    try:
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
    except ImportError:
        print("error: need pandas openpyxl matplotlib numpy", file=sys.stderr)
        return 1

    df = pd.read_excel(xlsx_path)
    ensure_required_columns(df, ["Speaker", "Year", "SpeechIndex", "Month"])
    score_cols = get_score_columns(df)
    if not score_cols:
        print("error: no *_score columns found", file=sys.stderr)
        return 1

    clear_previous_outputs(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    trend_dir = out_dir / "trend_plots"
    bar_dir = out_dir / "bar_charts"
    trend_dir.mkdir(exist_ok=True)
    bar_dir.mkdir(exist_ok=True)

    cycle_rows = []
    election_year_rows = []

    for cycle in CYCLES:
        cycle_df = df[
            (df["Year"] >= cycle.start_year)
            & (df["Year"] <= cycle.end_year)
            & (df["Speaker"].isin(["Trump", cycle.opponent_speaker]))
        ].copy()

        cycle_means = (
            cycle_df.groupby("Speaker")[score_cols]
            .mean(numeric_only=True)
            .rename(index={cycle.opponent_speaker: cycle.opponent_label})
        )
        for score_col in score_cols:
            cycle_rows.append(
                {
                    "Cycle": cycle.label,
                    "Dictionary": score_col,
                    "TrumpMean": cycle_means.loc["Trump", score_col] if "Trump" in cycle_means.index else np.nan,
                    "Opponent": cycle.opponent_label,
                    "OpponentMean": cycle_means.loc[cycle.opponent_label, score_col] if cycle.opponent_label in cycle_means.index else np.nan,
                }
            )

        election_df = cycle_df[cycle_df["Year"] == cycle.election_year].copy()
        election_means = (
            election_df.groupby("Speaker")[score_cols]
            .mean(numeric_only=True)
            .rename(index={cycle.opponent_speaker: cycle.opponent_label})
        )
        for score_col in score_cols:
            election_year_rows.append(
                {
                    "ElectionYear": cycle.election_year,
                    "Cycle": cycle.label,
                    "Dictionary": score_col,
                    "TrumpMean": election_means.loc["Trump", score_col] if "Trump" in election_means.index else np.nan,
                    "Opponent": cycle.opponent_label,
                    "OpponentMean": election_means.loc[cycle.opponent_label, score_col] if cycle.opponent_label in election_means.index else np.nan,
                }
            )

        monthly = make_monthly_series(pd, df, cycle, score_cols)
        monthly.to_csv(out_dir / f"{cycle.slug}_monthly_scores.csv", index=False, encoding="utf-8-sig")

    cycle_comparison = pd.DataFrame(cycle_rows)
    cycle_comparison.to_csv(out_dir / "cycle_mean_comparison.csv", index=False, encoding="utf-8-sig")

    election_year_comparison = pd.DataFrame(election_year_rows)
    election_year_comparison.to_csv(out_dir / "election_year_mean_comparison.csv", index=False, encoding="utf-8-sig")

    full_timeline = make_full_timeline_monthly_series(pd, df, score_cols)
    full_timeline.to_csv(out_dir / "full_timeline_monthly_scores.csv", index=False, encoding="utf-8-sig")

    for score_col in score_cols:
        fig, ax = plt.subplots(figsize=(13, 5.5))
        for speaker in ["Trump", "Clinton", "Biden", "Harris"]:
            sub = full_timeline[full_timeline["Speaker"] == speaker].copy()
            if sub.empty:
                continue
            style = SPEAKER_STYLES[speaker]
            series = sub[score_col]
            ma = series.rolling(window=9, center=True, min_periods=1).mean()
            ax.plot(
                sub["Date"],
                series,
                linestyle=":",
                marker="o",
                markersize=3,
                linewidth=1.1,
                color=style["color"],
                alpha=0.75,
                label=f"{style['label']} monthly",
            )
            ax.plot(
                sub["Date"],
                ma,
                linestyle="-",
                linewidth=2.0,
                color=style["color"],
                label=f"{style['label']} 9-mo MA",
            )

        ax.set_title(f"{pretty_score_name(score_col)} | Trump vs Democratic opponents over time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Score (%)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(ncol=2)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(trend_dir / f"{safe_name(score_col)}__full_timeline_trend.png", dpi=200, bbox_inches="tight")
        plt.close(fig)

    for score_col in score_cols:
        sub = election_year_comparison[election_year_comparison["Dictionary"] == score_col].copy()
        fig, ax = plt.subplots(figsize=(8, 5))
        x = np.arange(len(sub))
        width = 0.34

        ax.bar(x - width / 2, sub["TrumpMean"], width, color="red", alpha=0.8, label="Trump")
        ax.bar(x + width / 2, sub["OpponentMean"], width, color="blue", alpha=0.8, label="Opponent")

        ax.set_xticks(x)
        ax.set_xticklabels([str(y) for y in sub["ElectionYear"]])
        ax.set_title(f"{pretty_score_name(score_col)} | Election-year mean comparison")
        ax.set_xlabel("Election year")
        ax.set_ylabel("Mean score (%)")
        ax.grid(True, axis="y", linestyle="--", alpha=0.4)
        ax.legend()
        fig.tight_layout()
        fig.savefig(bar_dir / f"{safe_name(score_col)}__election_year_bar.png", dpi=200, bbox_inches="tight")
        plt.close(fig)

    print(f"wrote: {out_dir / 'cycle_mean_comparison.csv'}")
    print(f"wrote: {out_dir / 'election_year_mean_comparison.csv'}")
    print(f"wrote monthly CSVs to: {out_dir}")
    print(f"wrote: {out_dir / 'full_timeline_monthly_scores.csv'}")
    print(f"wrote trend plots to: {trend_dir}")
    print(f"wrote bar charts to: {bar_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
