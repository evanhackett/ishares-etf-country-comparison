#!/usr/bin/env python3
"""Scrape P/E ratio, P/B ratio, and 12-month trailing yield from iShares ETF pages."""

import csv
import json
import re
import time
import tomllib
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "etfs.toml"


def load_etfs() -> dict[str, str]:
    with CONFIG_FILE.open("rb") as f:
        return tomllib.load(f)["etfs"]


ETFS = load_etfs()

CACHE_FILE = Path(__file__).parent / "cache" / "etf_cache.json"
CACHE_TTL = 24 * 60 * 60  # seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

FIELDS = {
    "priceEarnings": "pe_ratio",
    "priceBook": "pb_ratio",
    "twelveMonTrlYld": "dividend_yield_12m",
}


@dataclass
class ETFMetrics:
    ticker: str
    url: str
    name: str | None
    pe_ratio: str | None
    pb_ratio: str | None
    dividend_yield_12m: str | None


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_metrics(html: str, ticker: str, url: str) -> ETFMetrics:
    name_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    name = re.sub(r"<[^>]+>", "", name_match.group(1)).strip() if name_match else None

    values = {}
    for col, field in FIELDS.items():
        pattern = (
            rf'col-{col}\s*">\s*<div class="caption">.*?<div class="data">(.*?)</div>'
        )
        m = re.search(pattern, html, re.DOTALL)
        if m:
            values[field] = re.sub(r"<[^>]+>", "", m.group(1)).strip() or None
        else:
            values[field] = None
    return ETFMetrics(ticker=ticker, url=url, name=name, **values)


def scrape(etfs: dict[str, str], delay: float = 1.0) -> list[ETFMetrics]:
    """
    Args:
        etfs: dict of {ticker: ishares_url}
        delay: seconds to wait between requests
    """
    cache = load_cache()
    now = time.time()
    results = []
    fetched = 0

    for ticker, url in etfs.items():
        entry = cache.get(ticker)
        if entry and (now - entry["timestamp"]) < CACHE_TTL:
            print(f"Using cache for {ticker}")
            metrics = ETFMetrics(**{k: v for k, v in entry.items() if k != "timestamp"})
        else:
            if fetched > 0:
                time.sleep(delay)
            print(f"Fetching {ticker}...")
            html = fetch_html(url)
            metrics = parse_metrics(html, ticker, url)
            cache[ticker] = {**asdict(metrics), "timestamp": now}
            save_cache(cache)
            fetched += 1
            print(
                f"  {metrics.name}  P/E: {metrics.pe_ratio}  P/B: {metrics.pb_ratio}  Yield: {metrics.dividend_yield_12m}"
            )

        results.append(metrics)
    return results


def display_name(name: str | None) -> str:
    if not name:
        return "N/A"
    for prefix in ("iShares Core MSCI ", "iShares MSCI "):
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    return name.removesuffix(" ETF")


def pe_sort_key(r: ETFMetrics) -> float:
    try:
        return float(r.pe_ratio)
    except (TypeError, ValueError):
        return float("inf")


if __name__ == "__main__":
    results = scrape(ETFS)
    results.sort(key=pe_sort_key)

    csv_path = Path(__file__).parent / "results" / "scrape_ishares_results.csv"
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["ticker", "name", "pe_ratio", "pb_ratio", "dividend_yield_12m"]
        )
        for r in results:
            writer.writerow(
                [r.ticker, r.name, r.pe_ratio, r.pb_ratio, r.dividend_yield_12m]
            )
    print(f"\nWrote {csv_path}")

    print("\nResults:")
    print(f"{'Ticker':<8} {'Name':<40} {'P/E':>8} {'P/B':>8} {'Yield (12m)':>12}")
    print("-" * 80)
    for r in results:
        print(
            f"{r.ticker:<8} {display_name(r.name):<40} {r.pe_ratio or 'N/A':>8} {r.pb_ratio or 'N/A':>8} {r.dividend_yield_12m or 'N/A':>12}"
        )
