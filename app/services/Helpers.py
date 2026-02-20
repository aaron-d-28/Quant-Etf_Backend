import json
import os
from datetime import datetime
from typing import Union

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.db.models.ohlcv import OHLCV
from app.models.artifacts.ML_model import predict
from app.services.Anomaly.AnomalyDetection import weekly_train, daily_predict
from app.services.Anomaly.AnomalyKafka import SendAnomalyUsingKafka
from app.services.Kafka.PredictionKafka import SendPredictionUsingKafka
from app.services.risk_service import last_monthly_risk
from app.services.risk_transformer import fetch_monthly_risk
from app.services.tasks import process_ohlcv_for_risk, process_monthly_ohlcv_for_risk


STATE_PATH = "models/training_state.json"
from datetime import datetime

def get_previous_month_year(dt: datetime):
    """
    Given a datetime object, return the previous month and year.

    Examples:
    - dt = 2023-03-15 -> returns (2, 2023)
    - dt = 2023-01-10 -> returns (12, 2022)
    """
    if dt.month == 1:
        prev_month = 12
        prev_year = dt.year - 1
    else:
        prev_month = dt.month - 1
        prev_year = dt.year
    return prev_month, prev_year

def update_training_state(date: pd.Timestamp):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    iso = pd.to_datetime(date).isocalendar()
    tmp_path = STATE_PATH + ".tmp"
    state = {
        "year": int(iso.year),
        "week": int(iso.week)
    }

    with open(tmp_path, "w") as f:
        json.dump(
            {"year": int(iso.year), "week": int(iso.week)},
            f
        )

    os.replace(tmp_path, STATE_PATH)


    try:
        with open(tmp_path, "w") as f:
            json.dump(state, f)

        os.replace(tmp_path, STATE_PATH)

    except Exception as e:
        print("Failed to update training state:", e)


def is_new_week(current_date:  Union[datetime, pd.Timestamp]) -> bool:
    current_date = pd.to_datetime(current_date)
    iso = current_date.isocalendar()

    current_year = int(iso.year)
    current_week = int(iso.week)

    # No state exists → first run
    if not os.path.exists(STATE_PATH):
        return True

    with open(STATE_PATH, "r") as f:
        state = json.load(f)

    last_year = state["year"]
    last_week = state["week"]

    return (current_year != last_year) or (current_week != last_week)



def insert_ohlcv(db: Session, data: dict) -> bool:
    try:
        rec = OHLCV(
            date=data["date"],
            ticker=data["ticker"],
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=float(data["volume"]),
            adj_close=float(data["adj_close"]),
        )
        db.add(rec)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"DB insert error: {e} | data={data}")
        return False

def compute_daily_risk(db: Session, ticker: str) -> pd.DataFrame | None:
    try:
        daily_risk = process_ohlcv_for_risk(ticker, db=db)

        if isinstance(daily_risk, list):
            daily_risk = pd.concat(daily_risk, ignore_index=True)

        if not isinstance(daily_risk, pd.DataFrame) or daily_risk.empty:
            print("DailyRiskData empty or invalid")
            return None

        return daily_risk

    except Exception as e:
        print(f"Daily risk computation error: {e}")
        return None
def maybe_retrain_anomaly_model(db: Session, date_str: str) -> datetime | None:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception as e:
        print(f"Date parsing error: {e}")
        return None

    try:
        if is_new_week(dt):
            weekly_train(db=db, as_of_date=dt.strftime("%Y-%m-%d"))
            update_training_state(pd.Timestamp(dt))
            print("Weekly anomaly retraining completed")
    except Exception as e:
        print(f"Weekly retraining error: {e}")

    return dt


def prepare_daily_risk_for_ml(daily_risk_df, feature_cols):
    return daily_risk_df



def prepare_daily_features(
        daily_risk_df: pd.DataFrame,
        feature_cols: list[str]
) -> pd.DataFrame | None:
    try:
        clean_df = prepare_daily_risk_for_ml(daily_risk_df, feature_cols)

        if not isinstance(clean_df, pd.DataFrame) or clean_df.empty:
            print("Clean ML dataframe empty")
            return None

        return clean_df

    except Exception as e:
        print(f"Feature preparation error: {e}")
        print(f"Input columns: {daily_risk_df.columns.tolist()}")
        return None
def detect_daily_anomalies(clean_df: pd.DataFrame):
    try:
        anomalies = daily_predict(clean_df)

        if anomalies is None:
            print("Anomaly model returned None")

        return anomalies

    except Exception as e:
        print(f"Daily anomaly detection error: {e}")
        print(f"Clean DF snapshot:\n{clean_df.head()}")
        return None
def process_monthly_risk(db: Session, dt: datetime | None) -> str | None:
    if dt is None or dt.day != 1:
        return None

    prev_month = dt.month - 1 if dt.month > 1 else 12
    prev_year = dt.year if dt.month > 1 else dt.year - 1
    prev_month_str = f"{prev_year}-{prev_month:02d}"

    try:
        monthly_df = process_monthly_ohlcv_for_risk(prev_month_str, db)
        print(f"Inserted Monthly Risk rows: {len(monthly_df)}")
        return prev_month_str
    except Exception as e:
        print(f"Monthly risk processing error: {e}")
        return None

def format_monthly_predictions(df: pd.DataFrame, preds: list[float]) -> list[dict]:
    """
    Zip predictions with the dataframe rows and return a list of dicts.
    """
    try:
        records = df.to_dict('records')  # Convert DataFrame to list of dicts
        return [
            {
                "month": row["month"],
                "year": row["year"],
                "ticker": row["ticker"],
                "prediction": float(pred),
            }
            for row, pred in zip(records, preds)
        ]
    except Exception as e:
        print(f"Error formatting monthly predictions: {e}")
        return []


def run_monthly_prediction(db: Session, dt: datetime | None) -> list[dict]:
    if dt is None or dt.day != 1:
        return []

    try:
        prev_month, prev_year = get_previous_month_year(dt)

        # 🔁 COUNT EVERY FUNCTION CALL
        call_count, already_predicted = increment_call_counter(
            prev_year, prev_month
        )

        print(
            f"Monthly prediction call counter → "
            f"{call_count}/{EXPECTED_CALLS} "
            f"for {prev_month}/{prev_year}"
        )

        # ❌ Already predicted → never again
        if already_predicted:
            return []

        # ❌ Until 20 calls → do nothing
        if call_count < EXPECTED_CALLS:
            return []

    except Exception as e:
        print(f"Monthly counter error: {e}")
        return []

    # ---- RUN PREDICTION ONLY WHEN COUNT == 20 ----
    try:
        df = fetch_monthly_risk(
            db=db,
            year=prev_year,
            month=str(prev_month),
            as_df=True
        )

        if df is None or df.empty:
            print("Prediction aborted: no monthly data")
            return []

        df = df.sort_values("ticker").reset_index(drop=True)

        preds = np.asarray(predict(df)).reshape(-1)

        results = format_monthly_predictions(df, preds)

        # 🔒 Mark as predicted (VERY IMPORTANT)
        mark_predicted(prev_year, prev_month)

        print("✅ Monthly prediction executed ONCE")

        return results

    except Exception as e:
        print(f"Monthly prediction error: {e}")
        return []


def dispatch_kafka(predictions, anomalies):
    try:
        if predictions:
            SendPredictionUsingKafka(predictions)
            print("Sent monthly predictions")
    except Exception as e:
        print(f"Kafka dispatch error for Rotation: {e}")

    try:
        if isinstance(anomalies, pd.DataFrame) and not anomalies.empty:
            SendAnomalyUsingKafka(anomalies)
            print("Sent anomalies")
    except Exception as e:
        print(f"Kafka dispatch error for Anomalies: {e}")


import json
import os

COUNTER_FILE = "monthly_prediction_counter.json"
EXPECTED_CALLS = 20


def load_counter():
    if not os.path.exists(COUNTER_FILE):
        return {}
    with open(COUNTER_FILE, "r") as f:
        return json.load(f)


def save_counter(counter: dict):
    with open(COUNTER_FILE, "w") as f:
        json.dump(counter, f, indent=2)


def increment_call_counter(year: int, month: int):
    key = f"{year}-{month}"
    counter = load_counter()

    if key not in counter:
        counter[key] = {"count": 1, "predicted": False}
    else:
        counter[key]["count"] += 1

    save_counter(counter)
    return counter[key]["count"], counter[key]["predicted"]


def mark_predicted(year: int, month: int):
    key = f"{year}-{month}"
    counter = load_counter()

    if key in counter:
        counter[key]["predicted"] = True
        save_counter(counter)
