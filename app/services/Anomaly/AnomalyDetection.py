# weekly_training.py
# Weekly retraining pipeline using IncrementalPCA + IsolationForest
import os

import numpy as np
import pandas as pd
from fastapi import Depends
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import IncrementalPCA
from sklearn.ensemble import IsolationForest
import joblib
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models.risk_factor import RiskFactor

# =========================
# CONFIG
# =========================
N_COMPONENTS = 10
CONTAMINATION = 0.03
N_ESTIMATORS = 300
BATCH_SIZE = 256

MODEL_DIR = os.path.dirname(__file__)
SCALER_PATH = MODEL_DIR + "scaler.pkl"
IPCA_PATH = MODEL_DIR + "ipca.pkl"
IF_PATH = MODEL_DIR + "isoforest.pkl"

FEATURE_COLS = [
    "return_val",
    "volatility_14d",
    "downside_vol_30d",
    "var_95",
    "cvar_95",
    "max_drawdown_60d",
    "sharpe_30d"
]

STATE_PATH = "models/training_state.json"
# =========================
# LOAD WEEKLY DATA
# =========================

def load_weekly_data(as_of_date: str, db: Session , window_days: int = 90, )->pd.DataFrame|None:
    as_of = pd.to_datetime(as_of_date)
    start = as_of - timedelta(days=window_days)

    rows = (
        db.query(
            RiskFactor.ticker,
            RiskFactor.date,
            RiskFactor.return_val,
            RiskFactor.volatility_14d,
            RiskFactor.downside_vol_30d,
            RiskFactor.var_95,
            RiskFactor.cvar_95,
            RiskFactor.max_drawdown_60d,
            RiskFactor.sharpe_30d,
        )
        .filter(RiskFactor.date >= start)
        .filter(RiskFactor.date <= as_of)
        .all()
    )
    db.close()

    return pd.DataFrame(rows, columns=[
        "ticker",
        "date",
        "return_val",
        "volatility_14d",
        "downside_vol_30d",
        "var_95",
        "cvar_95",
        "max_drawdown_60d",
        "sharpe_30d",
    ])


# =========================
# WEEKLY TRAIN FUNCTION
# =========================

def weekly_train(as_of_date, db: Session) -> bool:
    try:
        df_weekly = load_weekly_data(as_of_date=as_of_date, db=db)

        if df_weekly is None or df_weekly.empty:
            print("[Weekly] No data")
            return False

        df_weekly = df_weekly[FEATURE_COLS].dropna()
        X = df_weekly.values

        n_features = X.shape[1]
        n_components = min(N_COMPONENTS, n_features)

        if len(X) < n_components:
            print("[Weekly] Not enough rows for PCA")
            return False

        scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else StandardScaler()
        X_scaled = scaler.fit_transform(X)

        ipca = (
            joblib.load(IPCA_PATH)
            if os.path.exists(IPCA_PATH)
            else IncrementalPCA(n_components=n_components)
        )

        for i in range(0, len(X_scaled), BATCH_SIZE):
            ipca.partial_fit(X_scaled[i:i + BATCH_SIZE])

        X_reduced = ipca.transform(X_scaled)

        iso = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=CONTAMINATION,
            random_state=42,
            n_jobs=-1
        )
        iso.fit(X_reduced)

        joblib.dump(scaler, SCALER_PATH)
        joblib.dump(ipca, IPCA_PATH)
        joblib.dump(iso, IF_PATH)

        print(f"[✓] Weekly training completed: {as_of_date}")
        return True

    except Exception as e:
        print("❌ Weekly training failed:", e)
        return False



def daily_predict(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Detect anomalies using the latest trained models.
    Expects a CLEAN DataFrame. No type juggling here.
    """

    # -------- HARD SAFETY --------
    if df is None or not isinstance(df, pd.DataFrame):
        print(f"daily_predict received invalid input: {type(df)}")
        return None

    if df.empty:
        print("daily_predict received empty DataFrame")
        return None

    # -------- REQUIRED COLUMNS CHECK --------
    missing = [col for col in FEATURE_COLS if col not in df.columns]
    if missing:
        print(f"daily_predict missing columns: {missing} :Cols existing:{df.columns} ")
        return None

    # ---- Load models ----
    scaler = joblib.load(SCALER_PATH)
    ipca = joblib.load(IPCA_PATH)
    iso = joblib.load(IF_PATH)

    # ---- Prepare features ----
    feature_df = df[FEATURE_COLS].copy()
    feature_df = feature_df.dropna()

    if feature_df.empty:
        print("No valid feature rows after dropna")
        return None

    X = feature_df.values

    X_scaled = scaler.transform(X)
    X_reduced = ipca.transform(X_scaled)

    # Align back to original rows
    result_df = df.loc[feature_df.index].copy()

    result_df["anomaly_score"] = iso.score_samples(X_reduced)
    result_df["is_anomaly"] = iso.predict(X_reduced) == -1

    return result_df
