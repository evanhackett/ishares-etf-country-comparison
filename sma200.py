#!/usr/bin/env python3
"""Print SMA200 data for ETFs defined in etfs.toml."""

import json
import math
import time
from pathlib import Path

import tomllib
import yfinance as yf

CONFIG_FILE = Path(__file__).parent / "etfs.toml"
CACHE_FILE = Path(__file__).parent / "sma200_cache.json"
CACHE_TTL = 60 * 60  # seconds
PRICE_HISTORY_DAYS = "300d"


def load_tickers() -> list[str]:
    with CONFIG_FILE.open("rb") as f:
        return list(tomllib.load(f)["etfs"].keys())


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def fetch_sma200(ticker: str) -> dict | None:
    hist = yf.Ticker(ticker).history(period=PRICE_HISTORY_DAYS)["Close"]
    if len(hist) < 200:
        print(f"  {ticker}: not enough history ({len(hist)} days), skipping")
        return None
    current = hist.iloc[-1]
    sma200 = hist.rolling(200).mean().iloc[-1]
    return {
        "ticker": ticker,
        "current": current,
        "sma200": sma200,
        "pct_of_sma": current / sma200,
    }


def is_valid(entry: dict) -> bool:
    return not any(math.isnan(entry[k]) for k in ("current", "sma200", "pct_of_sma"))


def get_sma200(tickers: list[str]) -> list[dict]:
    cache = load_cache()
    now = time.time()
    rows = []

    for ticker in tickers:
        entry = cache.get(ticker)
        if entry and (now - entry["timestamp"]) < CACHE_TTL and is_valid(entry):
            print(f"Using cache for {ticker}")
            rows.append({k: v for k, v in entry.items() if k != "timestamp"})
        else:
            reason = "NaN in cache" if (entry and not is_valid(entry)) else "fetching"
            print(f"{ticker}: {reason}")
            row = fetch_sma200(ticker)
            if row is None:
                continue
            cache[ticker] = {**row, "timestamp": now}
            save_cache(cache)
            rows.append(row)

    return rows


def print_table(rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda r: r["pct_of_sma"])
    header = f"{'Ticker':<8} {'Price':>8} {'SMA200':>8} {'% of SMA':>10}"
    print(header)
    print("-" * len(header))
    for r in rows:
        bar = "+" if r["pct_of_sma"] >= 1 else "-"
        print(
            f"{r['ticker']:<8}"
            f" {r['current']:>8.2f}"
            f" {r['sma200']:>8.2f}"
            f" {r['pct_of_sma']*100:>9.1f}% {bar}"
        )


if __name__ == "__main__":
    tickers = load_tickers()
    print(f"Fetching price history for {len(tickers)} ETFs...\n")
    rows = get_sma200(tickers)
    print_table(rows)
