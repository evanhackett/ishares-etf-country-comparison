# scrape-etf-data

Scrapes P/E ratio, P/B ratio, and 12-month trailing yield from iShares ETF pages.

It is surprisingly difficult to find country comparisons of pe ratio, pb ratio, and dividend yield. Many sites have pe comparisons across countries, but to get pb and yield you have to go to specific ETF pages. iShares has ETFs for many countries, making it a useful resource. The script herein scrapes iShares' public ETF pages and outputs the aforementioned data in a table.

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
