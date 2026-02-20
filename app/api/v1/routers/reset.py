import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.MonthlyRankPrediction import MonthlyRankPrediction
from app.db.session import get_db
from app.db.models.ohlcv import OHLCV
from app.db.models.risk_factor import RiskFactor
from app.db.models.risk_monthly import RiskMonthly
from app.db.models.anomalies import Anomaly


router = APIRouter()

COUNTER_FILE = "monthly_prediction_counter.json"

@router.delete("/reset")
def reset_data(db: Session = Depends(get_db)):
    """
    Reset pipeline data from 2023 onwards.
    Clears:
    - OHLCV
    - RiskFactor
    - RiskMonthly
    - Anomaly
    - MonthlyRankPrediction
    - monthly_prediction_counter.json
    """

    cutoff_year = 2023

    try:
        deleted_ohlcv = (
            db.query(OHLCV)
            .filter(OHLCV.date >= datetime(cutoff_year, 1, 1))
            .delete(synchronize_session=False)
        )

        deleted_risk_factor = (
            db.query(RiskFactor)
            .filter(RiskFactor.date >= datetime(cutoff_year, 1, 1))
            .delete(synchronize_session=False)
        )

        deleted_risk_monthly = (
            db.query(RiskMonthly)
            .filter(RiskMonthly.year >= cutoff_year)
            .delete(synchronize_session=False)
        )

        deleted_anomaly = (
            db.query(Anomaly)
            .filter(Anomaly.year >= cutoff_year)
            .delete(synchronize_session=False)
        )

        deleted_predictions = (
            db.query(MonthlyRankPrediction)
            .filter(MonthlyRankPrediction.year >= cutoff_year)
            .delete(synchronize_session=False)
        )

        db.commit()

        # --- Reset monthly prediction counter file ---
        os.makedirs(os.path.dirname(COUNTER_FILE) or ".", exist_ok=True)
        with open(COUNTER_FILE, "w") as f:
            json.dump({}, f)

        return {
            "message": "Reset completed successfully",
            "deleted": {
                "ohlcv": deleted_ohlcv,
                "risk_factor": deleted_risk_factor,
                "risk_monthly": deleted_risk_monthly,
                "anomaly": deleted_anomaly,
                "monthly_rank_predictions": deleted_predictions,
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
