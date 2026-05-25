# Data Sources — all free

## Public market data
| Source | Library / Method | Use | Notes |
|--------|------------------|-----|-------|
| Yahoo Finance | `yfinance` | US + India public co. financials & prices | Suffix `.NS` for NSE, `.BO` for BSE, plain ticker for US |
| NSE direct | `nsepython` | NSE quotes, corporate actions, indices | Rate-limited — cache responses |
| BSE | `bsedata` | BSE quotes | Less complete than NSE |
| SEC EDGAR | `requests` (raw API) | US filings, full financials JSON | Free JSON API at `data.sec.gov`. Requires `User-Agent: name email@x.com` header |

## Reference / industry data
| Source | Use | Format |
|--------|-----|--------|
| Damodaran NYU | Industry betas, ERPs, regional risk premiums, multiples | Monthly Excel downloads from pages.stern.nyu.edu/~adamodar — parse with pandas |
| FRED | Risk-free rates, CPI, GDP, macro indicators | Free API key, no cost |

## Required Python packages
```
yfinance>=0.2.40
nsepython>=2.95
pandas>=2.2
numpy>=1.26
requests>=2.31
pyyaml>=6.0
pytest>=8.0
fredapi>=0.5
```

## Keys needed (all free)
- **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html — free signup, store in `.env`
- **SEC EDGAR**: no key, but requires `User-Agent` header with name + email
- **Yahoo Finance / NSE**: no key

## Caching
All API responses should be cached to `~/.sidwell/cache/` with a TTL of 24 hours for prices, 7 days for financials, 30 days for Damodaran data. Reason: rate limits + offline running.
