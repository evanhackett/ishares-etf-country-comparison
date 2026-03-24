#!/usr/bin/env python3
"""Download the latest Shiller P/E boxplot data from Research Affiliates."""

import json
import re
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://interactive.researchaffiliates.com"
INDEX_URL = f"{BASE_URL}/asset-allocation"

CACHE_FILE = Path(__file__).parent / "cache" / "ra_shillerpe_cache.json"
CACHE_TTL = 24 * 60 * 60  # seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def get_data_path() -> str:
    html = fetch(INDEX_URL)
    m = re.search(r'"dataPath"\s*:\s*"([^"]+)"', html)
    if not m:
        raise RuntimeError("Could not find dataPath in page HTML")
    return m.group(1)


def get_shiller_pe() -> list:
    if CACHE_FILE.exists():
        cached = json.loads(CACHE_FILE.read_text())
        if time.time() - cached["timestamp"] < CACHE_TTL:
            print("Using cache")
            return cached["data"]

    data_path = get_data_path()
    url = f"{BASE_URL}{data_path}/boxplot/boxplot_shillerpe.json"
    print(f"Fetching {url}")
    data = json.loads(fetch(url))
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps({"timestamp": time.time(), "data": data}, indent=2))
    return data


def print_table(data: list[dict]) -> None:
    categories = sorted({r["boxCategory"] for r in data})
    header = f"{'Name':<32} {'Current':>8} {'%ile':>6} {'50th':>8} {'25th':>8} {'75th':>8}"
    for category in categories:
        rows = [r for r in data if r["boxCategory"] == category]
        rows.sort(key=lambda r: r["currentValue"])
        print(f"\n{category}")
        print("-" * len(header))
        print(header)
        print("-" * len(header))
        for r in rows:
            print(
                f"{r['boxName']:<32}"
                f" {r['currentValue']:>8.1f}"
                f" {r['currentValuePercentile']*100:>5.0f}%"
                f" {r['range50th']:>8.1f}"
                f" {r['range25th']:>8.1f}"
                f" {r['range75th']:>8.1f}"
            )


if __name__ == "__main__":
    data = get_shiller_pe()
    print_table(data)
