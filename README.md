# scrape-etf-data

Tools for comparing country-level equity valuations across ETFs. It is surprisingly difficult to find country comparisons of P/E ratio, P/B ratio, and dividend yield in one place. Many sites have P/E comparisons, but to get P/B and yield you have to dig into individual ETF pages. This project scrapes iShares ETF pages, pulls Shiller P/E data from Research Affiliates, and fetches price history via yfinance to produce combined valuation tables.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scripts

### `scrape_ishares.py`
Scrapes P/E ratio, P/B ratio, and 12-month trailing yield from iShares ETF pages. Results are sorted by P/E ratio, printed to the terminal, and written to `results/scrape_ishares_results.csv`. Pages are cached in `cache/etf_cache.json` for 24 hours to avoid rate limiting.

```
python3 scrape_ishares.py
```

### `scrape_ra_shillerpe.py`
Downloads the latest Shiller P/E boxplot data from Research Affiliates' asset allocation tool. Automatically detects the current data URL from the page HTML. Results are grouped by market category (Developed, Emerging, Multi-Country) and sorted by current Shiller P/E within each group. Data is cached in `cache/ra_shillerpe_cache.json` for 24 hours.

```
python3 scrape_ra_shillerpe.py
```

### `sma200.py`
Fetches 200-day simple moving average data for each ETF via yfinance. Results are sorted by price as a percentage of the SMA200, indicating which markets are most extended or oversold relative to trend. Data is cached in `cache/sma200_cache.json`; tickers that return NaN are re-fetched on every run until valid data is returned.

```
.venv/bin/python3 sma200.py
```

### `combined.py`
Joins data from all three sources into a single table sorted by Shiller P/E percentile (cheapest first). Only includes ETFs that have a corresponding country entry in the Research Affiliates dataset. Results are written to `results/combined_results.csv`.

```
.venv/bin/python3 combined.py
```

## Configuration

### `etfs.toml`
Defines the ETF list used by `scrape_ishares.py` and `sma200.py` as a `ticker = "ishares_url"` mapping. Add or remove ETFs here without touching any Python code.

`combined.py` has its own `ETFS` dict at the top of the file mapping each ticker to its Research Affiliates country name and iShares URL, since only ETFs with a matching RA entry are relevant there.
