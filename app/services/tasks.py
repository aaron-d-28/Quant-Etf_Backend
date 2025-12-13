# app/services/tasks.py

from sqlalchemy.orm import Session

from app.db.models.risk_monthly import RiskMonthly
from app.db.session import SessionLocal
from app.db.models.risk_factor import RiskFactor
from app.services.risk_transformer import fetch_recent_ohlcv, compute_risk_for_latest, fetch_monthly_risk, fetch_risk, \
    calculate_monhtly_risk, calculate_monthly_rank


def process_ohlcv_for_risk(ticker: str):
    """Main task triggered after Kafka receives a new OHLCV row."""

    global DailyRiskData
    db: Session = SessionLocal()

    try:
        df = fetch_recent_ohlcv(db, ticker)
        if df is None or df.empty:
            print("Not enough data to compute risk factors.")
            return False

        risk = compute_risk_for_latest(df)
        if not risk:
            print("Risk computation returned None.")
            return False

        DailyRiskData = RiskFactor(
            date=risk["date"],
            ticker=ticker,
            adj_close=risk.get("adj_close"),        # optional
            return_val=risk["return_val"],
            volatility_14d=risk["volatility_14d"],
            downside_vol_30d=risk["downside_vol_30d"],
            var_95=risk["var_95"],
            cvar_95=risk["cvar_95"],
            max_drawdown_60d=risk["max_drawdown_60d"],
            sharpe_30d=risk["sharpe_30d"],
        )


        db.add(DailyRiskData)
        db.commit()
        return True

    except Exception as e:
        print("Risk factor pipeline error:", e)
        db.rollback()
        return False

    finally:
        db.close()
        return DailyRiskData



def process_monthly_ohlcv_for_risk(month_str:str):
    global RiskMonthData
    db: Session = SessionLocal()
    try:
        df = fetch_risk(db, month_str)
        if df is None or df.empty:
            print("Not enough data to compute risk factors.")
            return False
        df = calculate_monhtly_risk(df)
        if not df:
            print("Risk computation returned None.")
            return False
        df = calculate_monthly_rank(df)
        if not df:
            print("Risk computation returned None.")
            return False

        records = []

        for _, row in df.iterrows():
            RiskMonthData = RiskMonthly(
                ticker=row['ticker'],
                month=row['month'],
                monthly_return=row['monthly_return'],
                monthly_volatility=row['monthly_volatility'],
                downside_vol_monthly=row['downside_vol_monthly'],
                var_95_monthly=row['var_95_monthly'],
                cvar_95_monthly=row['cvar_95_monthly'],
                max_drawdown_monthly=row['max_drawdown_monthly'],
                sharpe_monthly=row['sharpe_monthly'],
                return_p=row['return_p'],
                sharpe_p=row['sharpe_p'],
                vol_p=row['vol_p'],
                downside_p=row['downside_p'],
                var_p=row['var_p'],
                cvar_p=row['cvar_p'],
                dd_p=row['dd_p'],
                safety_score=row['safety_score'],
                rank=row['rank'],
                date           = row['date'],
                year           = row['year'],
                month_sin      = row['month_sin'],
                month_cos      = row['month_cos']

            )
            records.append(RiskMonthData)
            db.add_all(records)
            db.commit()
    except Exception as e:
        print("Risk factor pipeline error:", e)
        db.rollback()
        return False
    finally:
        db.close()
        return RiskMonthData
