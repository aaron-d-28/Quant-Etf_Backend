import datetime

from fastapi import Depends, APIRouter
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db.models.anomalies import Anomaly
from app.db.session import get_db, SessionLocal
from app.services.DataRouters.RequestSchema import YearMonthRequest, MonthAnomalyRequest

router = APIRouter()


@router.post("/anomalyData")
def get_anomalies(payload: MonthAnomalyRequest):
    db: Session = SessionLocal()

    month = payload.month
    year = payload.year
    ticker = payload.ticker.upper() if payload.ticker else None

    #print(f"Type of {month} is {type(month)} and {year} is {type(year)}")
    # Base query
    q = db.query(Anomaly).filter(
        Anomaly.month == month,
        Anomaly.year == year
    )

    # Optional ticker filter
    if ticker:
        q = q.filter(Anomaly.ticker == ticker)

    anomalies = q.all()

    worst_anomaly = (
        q.order_by(desc(Anomaly.anomaly_score)).first()
        if anomalies else None
    )

    db.close()

    return {
        "month": month,
        "year": year,
        "ticker": ticker,
        "total_anomalies": len(anomalies),
        "worst_anomaly": worst_anomaly,
        "anomalies": anomalies
    }

@router.post("/random")
def get_random_anomalies(db: Session = Depends(get_db)):
    anomalies = (
        db.query(Anomaly)
        .order_by(func.random())   # PostgreSQL random
        .limit(5)
        .all()
    )

    return {
        "count": len(anomalies),
        "anomalies": anomalies
    }