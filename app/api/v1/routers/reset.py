from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models.ohlcv import OHLCV
from app.db.models.risk_factor import RiskFactor

router = APIRouter()

@router.delete("/reset")
def reset_data(db: Session = Depends(get_db)):
    """
    Delete all OHLCV + RiskFactor rows from 2023 onwards.
    """

    cutoff = datetime(2023, 1, 1)

    try:
        deleted_ohlcv = (
            db.query(OHLCV)
            .filter(OHLCV.date >= cutoff)
            .delete(synchronize_session=False)
        )

        deleted_risk = (
            db.query(RiskFactor)
            .filter(RiskFactor.date >= cutoff)
            .delete(synchronize_session=False)
        )

        db.commit()

        return {
            "message": "Reset completed",
            "deleted_ohlcv": deleted_ohlcv,
            "deleted_risk_factor": deleted_risk
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
