# scrape-etf-data

Scrapes P/E ratio, P/B ratio, and 12-month trailing yield from iShares ETF pages.

## Usage

```
python3 scrape_ishares.py
```

Results are printed to the terminal sorted by P/E ratio and written to `results.csv`.

Fetched pages are cached in `etf_cache.json` for 24 hours to avoid rate limiting.

## Adding ETFs

Add entries to the `ETFS` dict in `scrape_ishares.py`:

```python
"TICKER": "https://www.ishares.com/us/products/...",
```
