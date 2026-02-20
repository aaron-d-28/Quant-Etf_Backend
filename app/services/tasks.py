# app/services/tasks.py
import pandas as pd
from fastapi import Depends
from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models.MonthlyRankPrediction import MonthlyRankPrediction
from app.db.models.anomalies import Anomaly
from app.db.models.risk_monthly import RiskMonthly
from app.db.models.risk_factor import RiskFactor
from app.services.DataRouters.RiskKafka import SendDailyRiskUsingKafka
from app.services.risk_transformer import (
    fetch_recent_ohlcv,
    compute_risk_for_latest,
    fetch_monthly_risk,
    fetch_risk,
    calculate_monhtly_risk,
    calculate_monthly_rank, calculate_monthly_risk_demo,
)

def process_ohlcv_for_risk(ticker: str, db: Session) -> pd.DataFrame | None:
    try:
        df = fetch_recent_ohlcv(db=db, ticker=ticker)
        if df is None or df.empty:
            print("Not enough data to compute risk factors.")
            return None

        risk = compute_risk_for_latest(df)

        if not risk:
            print("Risk computation returned None.")
            return None

        daily_risk = RiskFactor(
            date=risk["date"],
            ticker=ticker,
            adj_close=risk.get("adj_close"),
            return_val=risk["return_val"],
            volatility_14d=risk["volatility_14d"],
            downside_vol_30d=risk["downside_vol_30d"],
            var_95=risk["var_95"],
            cvar_95=risk["cvar_95"],
            max_drawdown_60d=risk["max_drawdown_60d"],
            sharpe_30d=risk["sharpe_30d"],
        )

        db.add(daily_risk)
        db.commit()

        risk_df = pd.DataFrame([risk])
        risk_df["ticker"] = ticker

        # Kafka should NEVER break ML
        try:
            SendDailyRiskUsingKafka(risk_df.to_dict(orient="records")[0])
        except Exception as e:
            print("Kafka daily risk send error:", e)

        return risk_df

    except Exception as e:
        print("Risk factor pipeline error:", e)
        db.rollback()
        return None

def process_monthly_ohlcv_for_risk(month_str: str, db: Session) -> pd.DataFrame:
    """Compute monthly risk factors for all tickers and store in DB."""
    try:
        df = fetch_risk(db=db, month_str=month_str)
        if df is None or df.empty:
            print("Not enough data to compute monthly risk factors.")
            return pd.DataFrame()

        df = calculate_monthly_risk_demo(df)
        df = calculate_monthly_rank(df)

        if df is None or df.empty:
            print("Monthly risk computation returned None.")
            return pd.DataFrame()

        # =========================
        # UPSERT LAYER (DB only)
        # =========================
        records_dicts = df.to_dict(orient="records")

        stmt = insert(RiskMonthly).values(records_dicts)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["ticker", "date"]
        )

        db.execute(stmt)
        db.commit()

        # =========================
        # PIPELINE RETURN (ML only)
        # =========================
        return df

    except Exception as e:
        print("Risk factor pipeline error inserting RiskMonthData:", e)
        db.rollback()
        return pd.DataFrame()

def insert_monthly_predictions(
        db: Session,
        predictions: list[dict] | None,
        model_version: str | None = None
) -> int:
    if  predictions is None:
        return 0

    try:
        records = []

        for p in predictions:
            records.append(
                MonthlyRankPrediction(
                    ticker=p["ticker"],
                    month=str(p["month"]),
                    year=p["year"],
                    rank=float(p["prediction"]),
                    model_version=model_version
                )
            )

        if not records:
            return 0

        db.bulk_save_objects(records)
        db.commit()
        return len(records)

    except Exception as e:
        db.rollback()
        print(f"Error inserting monthly predictions: {e}")
        return 0


from pandas import DataFrame

def insert_anomalies(
        db: Session,
        anomalies,
        model_version: str | None = None
) -> int:

    if anomalies is None:
        return 0

    # 🔑 Convert DataFrame → list[dict]
    if isinstance(anomalies, pd.DataFrame):
        if anomalies.empty:
            return 0
        anomalies = anomalies.to_dict(orient="records")

    if not anomalies:
        return 0

    try:
        records = []

        for a in anomalies:
            dt = a.get("date")
            if dt is None:
                continue  # hard safety

            records.append(
                Anomaly(
                    ticker=a["ticker"],
                    anomaly_score=float(a["anomaly_score"]),
                    year=dt.year,
                    month=str(dt.month),
                    anomaly_type="model",
                    source="risk_pipeline",
                    feature_values={
                        k: v for k, v in a.items()
                        if k not in {"date", "ticker", "anomaly_score"}
                    }
                )
            )

        if not records:
            return 0

        db.bulk_save_objects(records)
        db.commit()
        return len(records)

    except Exception as e:
        db.rollback()
        print(f"Error inserting anomalies: {e}")
        return 0

