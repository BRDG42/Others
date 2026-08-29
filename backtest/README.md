# SPY 50/200 SMA crossover — backtest + audit

Run it:

```bash
pip install yfinance pandas numpy requests
python backtest.py
```

## What it does

Long SPY when the 50-day SMA is above the 200-day SMA, flat otherwise.
Long only, no leverage, no shorting, full position or flat.
Signals are read off daily closes; **fills happen at the next bar's open.**
Costs: 0.05% slippage per side, $1 per fill. Starting capital $100,000.

Window 2010-01-04 .. 2024-12-31 (3,774 trading days). Prices are loaded from
2009-01-02 so the 200-day SMA is already full on the first day of the window —
the backtest never trades off a partially-formed average.

## Results

|                   | SMA 50/200 | Buy & hold SPY |
|-------------------|-----------:|---------------:|
| Total return      |    250.12% |        581.84% |
| CAGR              |      8.72% |         13.66% |
| Max drawdown      |    -33.70% |        -33.70% |
| Sharpe (rf=0)     |       0.66 |           0.84 |
| Annualised vol    |     14.24% |         17.05% |
| Round-trip trades |          8 |              0 |
| Win rate          |      62.5% |              — |
| Time in market    |      82.5% |         100.0% |

The strategy loses to buy-and-hold on return, on Sharpe, and it does not even
buy protection: both peak on 2020-02-19 and trough on 2020-03-23 at the same
-33.70%, because the 200-day SMA did not break until after the COVID bottom.
Lower volatility is the only thing it delivers, and not enough of it.

## Lookahead variant

`run(..., execution="signal_close")` fills at the close of the bar that
generated the signal. That is not implementable — you cannot know a close is a
crossover until it has printed. It is included only to quantify the bias.

|                   | Clean (next open) | Lookahead (signal close) |
|-------------------|------------------:|-------------------------:|
| Total return      |           250.12% |                  273.51% |
| CAGR              |             8.72% |                    9.19% |
| Sharpe (rf=0)     |              0.66 |                     0.69 |

+47 bps of CAGR from one missing `.shift(1)`. It is small here only because
the strategy trades 8 times in 15 years. The identical bug in a daily- or
weekly-rebalanced strategy compounds over hundreds of fills and routinely
manufactures Sharpe ratios above 2.

## Data source

`data.py` calls yfinance first, as specified. Yahoo Finance returns HTTP 429 to
this container's egress IP on every endpoint and every retry, so the module
falls back to stockanalysis.com's daily history API and caches it to
`spy_raw.csv`. Both paths return split- and dividend-adjusted OHLC (the
fallback scales open/high/low by `adj_close / close`, which is what yfinance's
`auto_adjust=True` does internally).

Spot-checked against known SPY prints: 2010-01-04 close 113.33, 2024-12-31
close 586.08. Delete `spy_raw.csv` and run on a machine that can reach Yahoo to
reproduce through yfinance itself.
