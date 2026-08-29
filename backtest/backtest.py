"""
50/200-day SMA crossover on SPY, 2010-01-01 .. 2024-12-31.

Long only, no leverage, no shorting, full position or flat.
Signals come from closes; fills happen at the NEXT bar's open.

The same engine can be run with execution="signal_close", which fills at the
close of the bar that generated the signal. That is lookahead bias -- you
cannot know the close is a crossover until the close has already printed.
It exists here only so the audit can quantify what the bias is worth.
"""

import numpy as np
import pandas as pd

from data import load_prices

# ---------------------------------------------------------------- parameters
TICKER = "SPY"
START = "2010-01-01"
END = "2024-12-31"
FAST, SLOW = 50, 200
SLIPPAGE = 0.0005          # 5 bps, paid on both sides of every fill
COMMISSION = 1.00          # dollars per fill
CAPITAL = 100_000.0
TRADING_DAYS = 252


# ---------------------------------------------------------------- signals
def build_signals(px):
    """
    px: adjusted OHLCV, with enough history BEFORE START to warm up the 200-SMA.

    Returns a frame with the raw regime flag and the tradeable target weight.
    """
    out = pd.DataFrame(index=px.index)
    out["close"] = px["close"]
    out["open"] = px["open"]

    # Trailing means: .rolling(n) uses bars t-n+1 .. t inclusive. It never
    # reaches forward. min_periods=n means no value exists until the window
    # is genuinely full, so no SMA is computed from a partial sample.
    out["sma_fast"] = px["close"].rolling(FAST, min_periods=FAST).mean()
    out["sma_slow"] = px["close"].rolling(SLOW, min_periods=SLOW).mean()

    # Regime known as of bar t's close: long while fast > slow.
    # Crossing up == regime flips 0->1, crossing down == 1->0, so the level
    # and the crossover formulation give identical positions.
    out["regime"] = (out["sma_fast"] > out["sma_slow"]).astype(float)
    out.loc[out["sma_slow"].isna(), "regime"] = np.nan

    return out


# ---------------------------------------------------------------- engine
def run(sig, start, end, execution="next_open"):
    """
    execution="next_open"    -> decide on bar t's close, fill at bar t+1's open. Clean.
    execution="signal_close" -> decide on bar t's close, fill at bar t's close. Lookahead.
    """
    if execution == "next_open":
        # THE LINE THAT PREVENTS LOOKAHEAD. The regime observed at the close of
        # bar t-1 is what we are allowed to act on during bar t. shift(1) moves
        # every signal one bar into the future; nothing on bar t's own row can
        # influence the position we hold into bar t's open.
        target = sig["regime"].shift(1)
        fill_price = sig["open"]
    elif execution == "signal_close":
        # No shift: we act on bar t using bar t's own close, and fill at that
        # same close. Both halves are impossible in real time.
        target = sig["regime"]
        fill_price = sig["close"]
    else:
        raise ValueError(execution)

    df = pd.DataFrame(
        {"target": target, "fill": fill_price, "close": sig["close"]}
    ).loc[start:end]
    df = df.dropna(subset=["target"])

    cash, shares = CAPITAL, 0.0
    equity, trades = [], []
    open_trade = None

    for ts, row in df.iterrows():
        want = int(row["target"])
        have = 1 if shares > 0 else 0

        if want != have:
            if want == 1:
                px = row["fill"] * (1 + SLIPPAGE)      # pay up to get filled
                shares = (cash - COMMISSION) / px
                cash = 0.0
                open_trade = {"entry_date": ts, "entry_px": px, "shares": shares}
            else:
                px = row["fill"] * (1 - SLIPPAGE)      # sell into the spread
                cash = shares * px - COMMISSION
                open_trade.update(exit_date=ts, exit_px=px)
                open_trade["pnl"] = (
                    open_trade["shares"] * (px - open_trade["entry_px"]) - 2 * COMMISSION
                )
                trades.append(open_trade)
                shares, open_trade = 0.0, None

        # Mark to market on the close of the bar we are living through.
        equity.append(cash + shares * row["close"])

    eq = pd.Series(equity, index=df.index, name="equity")

    if open_trade is not None:                          # still long on the last bar
        last = df["close"].iloc[-1]
        open_trade.update(
            exit_date=df.index[-1], exit_px=last, still_open=True,
            pnl=open_trade["shares"] * (last - open_trade["entry_px"]) - COMMISSION,
        )
        trades.append(open_trade)

    return eq, pd.DataFrame(trades), df


def buy_and_hold(sig, start, end):
    df = sig.loc[start:end]
    entry = df["open"].iloc[0] * (1 + SLIPPAGE)
    shares = (CAPITAL - COMMISSION) / entry
    return pd.Series(shares * df["close"].values, index=df.index, name="equity")


# ---------------------------------------------------------------- metrics
def metrics(eq, trades=None):
    ret = eq.pct_change().dropna()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    total = eq.iloc[-1] / eq.iloc[0] - 1
    dd = eq / eq.cummax() - 1

    m = {
        "Final equity": eq.iloc[-1],
        "Total return": total,
        "CAGR": (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1,
        "Annualised vol": ret.std() * np.sqrt(TRADING_DAYS),
        "Max drawdown": dd.min(),
        "Sharpe (rf=0)": ret.mean() / ret.std() * np.sqrt(TRADING_DAYS),
        "Time in market": np.nan,
        "Round-trip trades": np.nan,
        "Fills": np.nan,
        "Win rate": np.nan,
    }
    if trades is not None and len(trades):
        wins = (trades["pnl"] > 0).sum()
        m["Round-trip trades"] = len(trades)
        m["Fills"] = int(2 * len(trades) - trades.get("still_open", pd.Series(dtype=bool)).fillna(False).sum())
        m["Win rate"] = wins / len(trades)
    return m


FMT = {
    "Final equity": lambda v: f"${v:,.0f}",
    "Total return": lambda v: f"{v:>8.2%}",
    "CAGR": lambda v: f"{v:>8.2%}",
    "Annualised vol": lambda v: f"{v:>8.2%}",
    "Max drawdown": lambda v: f"{v:>8.2%}",
    "Sharpe (rf=0)": lambda v: f"{v:>8.2f}",
    "Time in market": lambda v: f"{v:>8.1%}",
    "Round-trip trades": lambda v: f"{v:>8.0f}",
    "Fills": lambda v: f"{v:>8.0f}",
    "Win rate": lambda v: f"{v:>8.1%}",
}


def table(cols, title):
    keys = list(next(iter(cols.values())).keys())
    w = max(len(k) for k in keys) + 2
    head = " " * w + "".join(f"{n:>22}" for n in cols)
    print(f"\n{title}\n" + "-" * len(head))
    print(head)
    print("-" * len(head))
    for k in keys:
        line = f"{k:<{w}}"
        for m in cols.values():
            v = m.get(k, np.nan)
            line += f"{('—' if pd.isna(v) else FMT[k](v)):>22}"
        print(line)


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    px, source = load_prices(TICKER, start="2009-01-01", end="2025-01-01")
    sig = build_signals(px)

    win = sig.loc[START:END]
    print(f"Data source : {source}")
    print(f"Ticker      : {TICKER}")
    print(f"Window      : {win.index[0].date()} .. {win.index[-1].date()}  "
          f"({len(win)} trading days)")
    print(f"Warm-up     : {px.index[0].date()} .. loaded {len(px)} bars so the "
          f"{SLOW}-day SMA is already full on day one of the window")
    print(f"Costs       : {SLIPPAGE:.2%} slippage per side, ${COMMISSION:.2f} per fill")

    eq_clean, tr_clean, exec_clean = run(sig, START, END, "next_open")
    eq_look, tr_look, _ = run(sig, START, END, "signal_close")
    eq_bh = buy_and_hold(sig, START, END)

    m_clean = metrics(eq_clean, tr_clean)
    m_look = metrics(eq_look, tr_look)
    m_bh = metrics(eq_bh)

    m_clean["Time in market"] = exec_clean["target"].mean()
    m_look["Time in market"] = sig.loc[START:END, "regime"].mean()
    m_bh["Time in market"] = 1.0
    m_bh["Round-trip trades"], m_bh["Fills"] = 0, 1

    table({"SMA 50/200 (clean)": m_clean, "Buy & hold SPY": m_bh},
          "RESULTS — clean backtest vs benchmark")
    table({"Clean (next open)": m_clean, "LOOKAHEAD (signal close)": m_look,
           "Buy & hold SPY": m_bh},
          "LOOKAHEAD COMPARISON — same signals, different fill assumption")

    print("\nRound-trip trades (clean run)")
    print("-" * 78)
    t = tr_clean.copy()
    t["entry"] = t["entry_date"].dt.date
    t["exit"] = t["exit_date"].dt.date
    t["days"] = (t["exit_date"] - t["entry_date"]).dt.days
    t["return"] = (t["exit_px"] / t["entry_px"] - 1).map("{:>7.2%}".format)
    t["P&L"] = t["pnl"].map("${:>10,.0f}".format)
    t["open?"] = t.get("still_open", pd.Series(False, index=t.index)).fillna(False).map({True: "held", False: ""})
    print(t[["entry", "exit", "days", "return", "P&L", "open?"]].to_string(index=False))

    for name, e in [("clean", eq_clean), ("lookahead", eq_look), ("buyhold", eq_bh)]:
        e.to_csv(f"equity_{name}.csv")
    tr_clean.to_csv("trades_clean.csv", index=False)
