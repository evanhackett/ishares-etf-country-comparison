#!/usr/bin/env python3
"""Combined view: iShares fundamentals + SMA200 + RA Shiller P/E, per country ETF."""

import csv
from pathlib import Path

from scrape_ishares import scrape
from scrape_ra_shillerpe import get_shiller_pe
from sma200 import get_sma200

CSV_PATH = Path(__file__).parent / "results" / "combined_results.csv"

# ticker: (RA box name, iShares URL)
ETFS = {
    "IVV": (
        "US Large",
        "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf",
    ),
    "EWJ": (
        "Japan",
        "https://www.ishares.com/us/products/239665/ishares-msci-japan-etf",
    ),
    "EWL": ("Switzerland", "https://www.ishares.com/us/products/239685/"),
    "ENOR": ("Norway", "https://www.ishares.com/us/products/239673/"),
    "THD": ("Thailand", "https://www.ishares.com/us/products/239688/"),
    "TUR": ("Turkey", "https://www.ishares.com/us/products/239689/"),
    "EIS": ("Israel", "https://www.ishares.com/us/products/239663/"),
    "MCHI": ("China", "https://www.ishares.com/us/products/239619/"),
    "EWH": ("Hong Kong", "https://www.ishares.com/us/products/239657/"),
    "INDA": ("India", "https://www.ishares.com/us/products/239659/"),
    "EWQ": ("France", "https://www.ishares.com/us/products/239648/"),
    "EWU": ("United Kingdom", "https://www.ishares.com/us/products/239690/"),
    "EWC": ("Canada", "https://www.ishares.com/us/products/239615/"),
    "EWG": ("Germany", "https://www.ishares.com/us/products/239650/"),
    "EWY": ("South Korea", "https://www.ishares.com/us/products/239681/"),
    "EWT": ("Taiwan", "https://www.ishares.com/us/products/239686/"),
    "EWA": ("Australia", "https://www.ishares.com/us/products/239607/"),
    "EWD": ("Sweden", "https://www.ishares.com/us/products/239684/"),
    "EWN": ("Netherlands", "https://www.ishares.com/us/products/239671/"),
    "EZA": ("South Africa", "https://www.ishares.com/us/products/239680/"),
    "EWZ": ("Brazil", "https://www.ishares.com/us/products/239612/"),
    "EWP": ("Spain", "https://www.ishares.com/us/products/239683/"),
    "EWS": ("Singapore", "https://www.ishares.com/us/products/239678/"),
    "EWI": ("Italy", "https://www.ishares.com/us/products/239664/"),
    "EIDO": ("Indonesia", "https://www.ishares.com/us/products/239661/"),
    "EWM": ("Malaysia", "https://www.ishares.com/us/products/239669/"),
    "EWW": ("Mexico", "https://www.ishares.com/us/products/239670/"),
    "EWK": ("Belgium", "https://www.ishares.com/us/products/239610/"),
    "EPHE": ("Philippines", "https://www.ishares.com/us/products/239675/"),
    "EPOL": ("Poland", "https://www.ishares.com/us/products/239676/"),
    "ECH": ("Chile", "https://www.ishares.com/us/products/239618/"),
    "IDEV": ("Developed Markets Large", "https://www.ishares.com/us/products/286762/"),
    "IEMG": ("Emerging Markets", "https://www.ishares.com/us/products/244050/"),
    "ACWI": ("All Country", "https://www.ishares.com/us/products/239600/"),
    "AAXJ": ("Asia ex Japan", "https://www.ishares.com/us/products/239601/"),
    "EWO": ("Austria", "https://www.ishares.com/us/products/239609/"),
    "EDEN": ("Denmark", "https://www.ishares.com/us/products/239621/"),
    "WSML": ("Developed Markets Small", "https://www.ishares.com/us/products/342357/"),
    "IEV": ("Europe", "https://www.ishares.com/us/products/239736/"),
    "EFNL": ("Finland", "https://www.ishares.com/us/products/239647/"),
    "EIRL": ("Ireland", "https://www.ishares.com/us/products/239662/"),
    "ENZL": ("New Zealand", "https://www.ishares.com/us/products/239672/"),
    "EPU": ("Peru", "https://www.ishares.com/us/products/239606/"),
    "IJR": ("US Small", "https://www.ishares.com/us/products/239774/"),
    # "ticker": ("Colombia", ""),
    # "ticker": ("Czech Republic", ""),
    # "ticker": ("Dev ex US Large", ""),
    # "ticker": ("Dev ex US Small", ""),
    # "ticker": ("Egypt", ""),
    # "ticker": ("Hungary", ""),
    # "ticker": ("Portugal", ""),
}


def build_combined() -> list[dict]:
    ishares_url_map = {ticker: url for ticker, (_, url) in ETFS.items()}
    ra_name_map = {ticker: ra_name for ticker, (ra_name, _) in ETFS.items()}

    print("--- iShares ---")
    ishares_results = {r.ticker: r for r in scrape(ishares_url_map)}

    print("\n--- SMA200 ---")
    sma_results = {r["ticker"]: r for r in get_sma200(list(ETFS.keys()))}

    print("\n--- Shiller P/E ---")
    ra_by_name = {r["boxName"]: r for r in get_shiller_pe()}

    rows = []
    for ticker, ra_name in ra_name_map.items():
        ishares = ishares_results.get(ticker)
        sma = sma_results.get(ticker)
        ra = ra_by_name.get(ra_name)
        rows.append(
            {
                "ticker": ticker,
                "ra_name": ra_name,
                "pe": ishares.pe_ratio if ishares else None,
                "pb": ishares.pb_ratio if ishares else None,
                "yield": ishares.dividend_yield_12m if ishares else None,
                "sma_pct": sma["pct_of_sma"] if sma else None,
                "shiller_pe": ra["currentValue"] if ra else None,
                "shiller_pct": ra["currentValuePercentile"] if ra else None,
            }
        )
    return rows


def fmt(val, fmt_spec, fallback="N/A"):
    if val is None:
        return fallback
    try:
        return format(val, fmt_spec)
    except (ValueError, TypeError):
        return str(val)


def print_table(rows: list[dict]) -> None:
    rows = sorted(
        rows,
        key=lambda r: r["shiller_pct"]
        if r["shiller_pct"] is not None
        else float("inf"),
    )

    header = (
        f"{'Ticker':<6} {'Country':<24}"
        f" {'P/E':>6} {'P/B':>5} {'Yield':>6}"
        f" {'SMA%':>6}"
        f" {'Shiller':>8} {'%ile':>5}"
    )
    print("\n" + header)
    print("-" * len(header))
    for r in rows:
        sma_pct = f"{r['sma_pct']*100:.1f}%" if r["sma_pct"] is not None else "N/A"
        shiller_pct = (
            f"{r['shiller_pct']*100:.0f}%" if r["shiller_pct"] is not None else "N/A"
        )
        print(
            f"{r['ticker']:<6} {r['ra_name']:<24}"
            f" {fmt(r['pe'], '>6')}"
            f" {fmt(r['pb'], '>5')}"
            f" {fmt(r['yield'], '>6')}"
            f" {sma_pct:>6}"
            f" {fmt(r['shiller_pe'], '>8.1f')}"
            f" {shiller_pct:>5}"
        )


def write_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(exist_ok=True)
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "ticker",
                "country",
                "pe_ratio",
                "pb_ratio",
                "dividend_yield_12m",
                "sma_pct",
                "shiller_pe",
                "shiller_pct",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r["ticker"],
                    r["ra_name"],
                    r["pe"],
                    r["pb"],
                    r["yield"],
                    f"{r['sma_pct']*100:.2f}" if r["sma_pct"] is not None else "",
                    f"{r['shiller_pe']:.4f}" if r["shiller_pe"] is not None else "",
                    f"{r['shiller_pct']*100:.2f}"
                    if r["shiller_pct"] is not None
                    else "",
                ]
            )
    print(f"Wrote {CSV_PATH}")


if __name__ == "__main__":
    rows = build_combined()
    write_csv(rows)
    print_table(rows)
