#!/usr/bin/env python3
"""
Value + trend strategy filter.

Keeps ETFs that are:
  - Above their 200-day SMA (trend filter)
  - At or below the 50th historical percentile on Shiller P/E (value filter)

Sorted by Shiller P/E percentile ascending (cheapest first).

Reads from results/combined_results.csv, regenerating it via combined.py
if the file is missing or more than 1 hour old.
"""

import csv
import subprocess
import sys
import time
from pathlib import Path

RESULTS_CSV = Path(__file__).parent / "results" / "combined_results.csv"
MAX_AGE = 60 * 60  # 1 hour in seconds
CAPE_THRESHOLD = 50.0  # percentile


def ensure_fresh_results() -> None:
    if RESULTS_CSV.exists():
        age = time.time() - RESULTS_CSV.stat().st_mtime
        if age < MAX_AGE:
            return
        print(f"Results file is {age/60:.0f} minutes old, regenerating...")
    else:
        print("No results file found, generating...")

    result = subprocess.run(
        [sys.executable, Path(__file__).parent / "combined.py"],
        check=True,
    )


def load_results() -> list[dict]:
    rows = []
    with RESULTS_CSV.open() as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def parse_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def apply_filters(rows: list[dict]) -> list[dict]:
    filtered = []
    for r in rows:
        sma_pct = parse_float(r["sma_pct"])
        shiller_pct = parse_float(r["shiller_pct"])

        if sma_pct is None or shiller_pct is None:
            continue
        if sma_pct < 100.0:
            continue
        if shiller_pct > CAPE_THRESHOLD:
            continue

        filtered.append({**r, "_sma_pct": sma_pct, "_shiller_pct": shiller_pct})

    return sorted(filtered, key=lambda r: r["_shiller_pct"])


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("No ETFs pass both filters.")
        return

    header = (
        f"{'Ticker':<6} {'Country':<24}"
        f" {'P/E':>6} {'P/B':>5} {'Yield':>6}"
        f" {'SMA%':>7}"
        f" {'Shiller':>8} {'%ile':>5}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['ticker']:<6} {r['country']:<24}"
            f" {r['pe_ratio'] or 'N/A':>6}"
            f" {r['pb_ratio'] or 'N/A':>5}"
            f" {r['dividend_yield_12m'] or 'N/A':>6}"
            f" {r['_sma_pct']:>6.1f}%"
            f" {float(r['shiller_pe']):>8.1f}"
            f" {r['_shiller_pct']:>4.0f}%"
        )


if __name__ == "__main__":
    ensure_fresh_results()
    rows = load_results()
    filtered = apply_filters(rows)
    print(f"\nValue + trend filter: {len(filtered)} of {len(rows)} ETFs pass\n")
    print_table(filtered)
