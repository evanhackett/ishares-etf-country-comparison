#!/usr/bin/env python3
"""Scrape P/E ratio, P/B ratio, and 12-month trailing yield from iShares ETF pages."""

import csv
import json
import re
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

ETFS = [
    "https://www.ishares.com/us/products/239665/ishares-msci-japan-etf",
    "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf",
    "https://www.ishares.com/us/products/239685/",
    "https://www.ishares.com/us/products/239673/",
    "https://www.ishares.com/us/products/239688/",
    "https://www.ishares.com/us/products/239689/",
    "https://www.ishares.com/us/products/239663/",
    "https://www.ishares.com/us/products/239619/",
    "https://www.ishares.com/us/products/239657/",
    "https://www.ishares.com/us/products/239659/",
    "https://www.ishares.com/us/products/239648/",
    "https://www.ishares.com/us/products/239690/",
    "https://www.ishares.com/us/products/239615/",
    "https://www.ishares.com/us/products/271542/",
    "https://www.ishares.com/us/products/239650/",
    "https://www.ishares.com/us/products/239681/",
    "https://www.ishares.com/us/products/239686/",
    "https://www.ishares.com/us/products/239607/",
    "https://www.ishares.com/us/products/239684/",
    "https://www.ishares.com/us/products/239671/",
    "https://www.ishares.com/us/products/239680/",
    "https://www.ishares.com/us/products/239612/",
    "https://www.ishares.com/us/products/239683/",
    "https://www.ishares.com/us/products/239678/",
    "https://www.ishares.com/us/products/239664/",
    "https://www.ishares.com/us/products/239661/",
    "https://www.ishares.com/us/products/239669/",
    "https://www.ishares.com/us/products/239670/",
    "https://www.ishares.com/us/products/239610/",
    "https://www.ishares.com/us/products/264275/",
    "https://www.ishares.com/us/products/239675/",
    "https://www.ishares.com/us/products/239676/",
    "https://www.ishares.com/us/products/239761/ishares-latin-america-40-etf",
    "https://www.ishares.com/us/products/244048/",
    "https://www.ishares.com/us/products/286762/",
    "https://www.ishares.com/us/products/244050/",
    "https://www.ishares.com/us/products/239618/",
]

CACHE_FILE = Path(__file__).parent / "etf_cache.json"
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
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_metrics(html: str, url: str) -> ETFMetrics:
    name_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    name = re.sub(r"<[^>]+>", "", name_match.group(1)).strip() if name_match else None

    title_match = re.search(r"<title>[^|]+\|\s*([A-Z]+)\s*</title>", html)
    ticker = (
        title_match.group(1) if title_match else url.rstrip("/").split("/")[-1].upper()
    )

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


def scrape(urls: list[str], delay: float = 1.0) -> list[ETFMetrics]:
    """
    Args:
        urls: list of iShares ETF URLs
        delay: seconds to wait between requests
    """
    cache = load_cache()
    now = time.time()
    results = []
    fetched = 0

    for url in urls:
        # Check cache by URL
        entry = next((e for e in cache.values() if e.get("url") == url), None)
        if entry and (now - entry["timestamp"]) < CACHE_TTL:
            ticker = entry["ticker"]
            print(f"Using cache for {ticker}")
            metrics = ETFMetrics(**{k: v for k, v in entry.items() if k != "timestamp"})
        else:
            if fetched > 0:
                time.sleep(delay)
            print(f"Fetching {url}...")
            html = fetch_html(url)
            metrics = parse_metrics(html, url)
            cache[metrics.ticker] = {**asdict(metrics), "timestamp": now}
            save_cache(cache)
            fetched += 1
            print(
                f"  {metrics.ticker}: {metrics.name}  P/E: {metrics.pe_ratio}  P/B: {metrics.pb_ratio}  Yield: {metrics.dividend_yield_12m}"
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

    csv_path = Path(__file__).parent / "results.csv"
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
