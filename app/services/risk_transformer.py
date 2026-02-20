from datetime import datetime
from typing import List, Union

import numpy as np
import pandas as pd
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.models.ohlcv import OHLCV
from app.db.models.risk_monthly import RiskMonthly
from app.db.models.risk_factor import RiskFactor

WINDOW = 60  # last 60 rows for rolling risk calculations


# -----------------------------------------------------
# FETCH LAST 60 ROWS FOR THAT TICKER
# -----------------------------------------------------
def fetch_recent_ohlcv( ticker: str,db: Session ):
    rows = (
        db.query(OHLCV)
        .filter(OHLCV.ticker == ticker)
        .order_by(OHLCV.date.desc())
        .limit(WINDOW)
        .all()
    )

    if not rows:
        return None

    df = pd.DataFrame([{
        "Date": r.date,
        "ticker": r.ticker,
        "Adj Close": r.adj_close
    } for r in rows])
    db.close()
    return df.sort_values("Date").reset_index(drop=True)


# -----------------------------------------------------
# COMPUTE RISK FACTORS FOR LAST ROW (60-row window)
# -----------------------------------------------------
def compute_risk_for_latest(df: pd.DataFrame):
    # --- rename & clean like your batch script ---
    df = df.rename(columns={
        'adj close': 'Adj Close',
        'adj_close': 'Adj Close',
        'close': 'Adj Close',
        'date': 'Date'
    })

    df = df.dropna(subset=['Adj Close', 'Date', 'ticker']).reset_index(drop=True)
    df = df.sort_values(['ticker', 'Date']).reset_index(drop=True)

    if len(df) < 5:
        return None  # not enough data for rolling

    ticker = df["ticker"].iloc[0]
    n = len(df)

    # ==========================
    # Extract arrays
    # ==========================
    dates = df["Date"].to_numpy()
    adj_close_raw = df["Adj Close"].to_numpy()

    if adj_close_raw.ndim == 2:
        adj_close = adj_close_raw[:, 0]
    else:
        adj_close = adj_close_raw

    # Ensure 1D
    dates = np.atleast_1d(dates).squeeze()
    adj_close = np.atleast_1d(adj_close).squeeze()

    # ==========================
    # Log returns
    # ==========================
    returns = np.zeros(n)
    if n > 1:
        returns[1:] = np.log(adj_close[1:] / adj_close[:-1])

    # ==========================
    # VOLATILITY 14D
    # ==========================
    vol_14 = np.zeros(n)
    for i in range(n):
        start = max(0, i - 13)
        vol_14[i] = np.std(returns[start:i+1])

    # ==========================
    # DOWNSIDE VOL 30D
    # ==========================
    dvol_30 = np.zeros(n)
    for i in range(n):
        start = max(0, i - 29)
        window = returns[start:i+1]
        window = window[window < 0]
        dvol_30[i] = np.std(window) if len(window) else 0

    # ==========================
    # VAR 95 (60D)
    # ==========================
    var_95 = np.zeros(n)
    for i in range(n):
        start = max(0, i - 59)
        var_95[i] = np.quantile(returns[start:i+1], 0.05)

    # ==========================
    # CVAR 95 (60D)
    # ==========================
    cvar_95 = np.zeros(n)
    for i in range(n):
        start = max(0, i - 59)
        window = returns[start:i+1]
        var_cut = np.quantile(window, 0.05)
        below = window[window <= var_cut]
        cvar_95[i] = below.mean() if len(below) else 0

    # ==========================
    # MAX DRAWDOWN 60D
    # ==========================
    cumulative = np.cumprod(1 + returns)
    max_dd = np.zeros(n)
    for i in range(n):
        start = max(0, i - 59)
        segment = cumulative[start:i+1]
        running_max = np.maximum.accumulate(segment)
        max_dd[i] = segment[-1] / running_max[-1] - 1

    # ==========================
    # SHARPE 30D
    # ==========================
    risk_free_rate = 0.0001 / 252
    sharpe_30 = np.zeros(n)
    for i in range(n):
        start = max(0, i - 29)
        window = returns[start:i+1] - risk_free_rate
        mean_excess = np.mean(window)
        std_excess = np.std(window)
        sharpe_30[i] = mean_excess / std_excess if std_excess > 1e-9 else 0

    # ====================================================
    # RETURN ONLY THE LAST (LATEST) ROW
    # ====================================================
    return {
        "date": dates[-1],
        "ticker": ticker,
        "return_val": float(returns[-1]),
        "volatility_14d": float(vol_14[-1]),
        "downside_vol_30d": float(dvol_30[-1]),
        "var_95": float(var_95[-1]),
        "cvar_95": float(cvar_95[-1]),
        "max_drawdown_60d": float(max_dd[-1]),
        "sharpe_30d": float(sharpe_30[-1]),
        "adj_close":float(adj_close[-1]),

    }


def fetch_monthly_risk(
        db: Session,
        year: int,
        month: str,
        as_df: bool = False
) -> Union[List[RiskMonthly], pd.DataFrame]:

    rows: List[RiskMonthly] = (
        db.query(RiskMonthly)
        .filter(RiskMonthly.year == year)
        .filter(RiskMonthly.month == month)
        .all()
    )

    if not as_df:
        return rows

    # Explicit DataFrame conversion (only when requested)
    db.close()
    return pd.DataFrame([
        {
            "ticker": r.ticker,
            "month": r.month,
            "year": r.year,
            "rank": r.rank,

            "monthly_return": r.monthly_return,
            "monthly_volatility": r.monthly_volatility,
            "downside_vol_monthly": r.downside_vol_monthly,
            "var_95_monthly": r.var_95_monthly,
            "cvar_95_monthly": r.cvar_95_monthly,
            "max_drawdown_monthly": r.max_drawdown_monthly,
            "sharpe_monthly": r.sharpe_monthly,

            "return_p": r.return_p,
            "sharpe_p": r.sharpe_p,
            "vol_p": r.vol_p,
            "downside_p": r.downside_p,
            "var_p": r.var_p,
            "cvar_p": r.cvar_p,
            "dd_p": r.dd_p,

            "date": r.date,
            "month_sin": r.month_sin,
            "month_cos": r.month_cos,
        }
        for r in rows
    ])

def fetch_risk( month_str: str,db: Session ):

    start_date = datetime.strptime(month_str + "-01", "%Y-%m-%d")
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, 1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, 1)

    rows = (
        db.query(RiskFactor)
        .filter(RiskFactor.date >= start_date)
        .filter(RiskFactor.date < end_date)
        .all()
    )
    data = [r.__dict__ for r in rows]
    for d in data:
        d.pop('_sa_instance_state', None)
    df = pd.DataFrame(data)
    db.close()
    return df


def calculate_monhtly_risk(df: pd.DataFrame):

    df["date"] = pd.to_datetime(df["date"])

    # Add year-month column
    df["year_month"] = df["date"].dt.to_period("M")

    results = []
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # # cyclic encoding for month
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    # Group by ticker and month
    for (ticker, ym), group in df.groupby(["ticker", "year_month"]):

        daily_returns = group["return_val"].values

        # Monthly return (geometric)
        monthly_return = np.prod(1 + daily_returns) - 1

        # Monthly volatility
        monthly_vol = np.std(daily_returns)

        # Downside volatility
        negative = daily_returns[daily_returns < 0]
        downside_vol = np.std(negative) if len(negative) else 0

        # VaR 95
        var_95 = np.percentile(daily_returns, 5)

        # CVaR 95
        tail = daily_returns[daily_returns < var_95]
        cvar_95 = np.mean(tail) if len(tail) else var_95

        # Max drawdown
        cum = np.cumprod(1 + daily_returns)
        peak = np.maximum.accumulate(cum)
        drawdown = (cum - peak) / peak
        max_dd = np.min(drawdown)

        # Sharpe ratio
        if np.std(daily_returns) > 0:
            sharpe = np.mean(daily_returns) / np.std(daily_returns)
        else:
            sharpe = 0




        results.append({
            "ticker": ticker,
            "month": str(ym),
            "monthly_return": monthly_return,
            "monthly_volatility": monthly_vol,
            "downside_vol_monthly": downside_vol,
            "var_95_monthly": var_95,
            "cvar_95_monthly": cvar_95,
            "max_drawdown_monthly": max_dd,
            "sharpe_monthly": sharpe,
            "date": df["date"].iloc[0],
            "year": df["year"].iloc[0],
            "month_sin": df["month_sin"].iloc[0],
            "month_cos": df["month_cos"].iloc[0],
        })


    return pd.DataFrame(results)


def calculate_monthly_rank(df: pd.DataFrame):

    for col in df.columns:
        if isinstance(df[col].dtype, pd.PeriodDtype):
            df[col] = df[col].dt.to_timestamp()


    def normalize_month(g):
        # 👍 Positive metrics (rank ascending)
        g["return_p"] = g["monthly_return"].rank(pct=True)  # <-- Fixed
        g["sharpe_p"] = g["sharpe_monthly"].rank(pct=True)  # <-- Fixed

        # 👎 Bad metrics (invert rank for score)
        g["vol_p"] = 1 - g["monthly_volatility"].rank(pct=True)     # <-- Fixed
        g["downside_p"] = 1 - g["downside_vol_monthly"].rank(pct=True) # <-- Fixed
        g["var_p"] = 1 - g["var_95_monthly"].rank(pct=True)          # <-- Fixed
        g["cvar_p"] = 1 - g["cvar_95_monthly"].rank(pct=True)        # <-- Fixed
        g["dd_p"] = 1 - g["max_drawdown_monthly"].rank(pct=True)    # <-- Fixed

        # final combined score (all columns)
       # calculate percentile class and scale to be called here
        g["safety_score"] = (
                0.15 * g["return_p"] +
                0.20 * g["sharpe_p"] +
                0.15 * g["vol_p"] +
                0.15 * g["downside_p"] +
                0.15 * g["var_p"] +
                0.10 * g["cvar_p"] +
                0.10 * g["dd_p"]
        )

        # rank by final score
        g["rank"] = g["safety_score"].rank(ascending=False)

        return g

    return df.groupby("month").apply(normalize_month).reset_index(drop=True)
    # note this above calculates sccore so here we call our function of the class defined ScalingScorere class and then we get the score

def calculate_monthly_risk_demo(df: pd.DataFrame):

    df["date"] = pd.to_datetime(df["date"])

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month.astype(str)  # <-- CANONICAL

    # cyclic encoding
    df["month_sin"] = np.sin(2 * np.pi * df["month"].astype(int) / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"].astype(int) / 12)

    results = []

    for (ticker, year, month), group in df.groupby(
            ["ticker", "year", "month"]
    ):

        daily_returns = group["return_val"].values

        monthly_return = np.prod(1 + daily_returns) - 1
        monthly_vol = np.std(daily_returns)

        negative = daily_returns[daily_returns < 0]
        downside_vol = np.std(negative) if len(negative) else 0

        var_95 = np.percentile(daily_returns, 5)
        tail = daily_returns[daily_returns < var_95]
        cvar_95 = np.mean(tail) if len(tail) else var_95

        cum = np.cumprod(1 + daily_returns)
        peak = np.maximum.accumulate(cum)
        max_dd = np.min((cum - peak) / peak)

        sharpe = (
            np.mean(daily_returns) / np.std(daily_returns)
            if np.std(daily_returns) > 0 else 0
        )

        results.append({
            "ticker": ticker,
            "month": month,                      # ✅ "12"
            "year": year,                        # ✅ 2022
            "date": group["date"].min(),         # ✅ 2022-12-01
            "month_sin": np.sin(2 * np.pi * int(month) / 12),
            "month_cos": np.cos(2 * np.pi * int(month) / 12),

            "monthly_return": monthly_return,
            "monthly_volatility": monthly_vol,
            "downside_vol_monthly": downside_vol,
            "var_95_monthly": var_95,
            "cvar_95_monthly": cvar_95,
            "max_drawdown_monthly": max_dd,
            "sharpe_monthly": sharpe,
        })

    return pd.DataFrame(results)
