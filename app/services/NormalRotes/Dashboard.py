from fastapi import Depends, APIRouter
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models.MonthlyRankPrediction import MonthlyRankPrediction
from app.db.models.anomalies import Anomaly
from app.db.models.risk_factor import RiskFactor
from app.db.models.risk_monthly import RiskMonthly
from app.db.session import get_db, SessionLocal

router = APIRouter()

@router.post("/Data")
def risk_dashboard():
    db: Session = SessionLocal()
    # --- Daily risk based ---
    least_risky = (
        db.query(RiskMonthly)
        .order_by(RiskMonthly.rank.asc())
        .first()
    )

    most_risky = (
        db.query(RiskMonthly)
        .order_by(RiskMonthly.rank.desc())
        .first()
    )

    # --- Latest ranking month ---
    latest_rank = (
        db.query(
            MonthlyRankPrediction.month,
            MonthlyRankPrediction.year
        )
        .order_by(desc(MonthlyRankPrediction.created_at))
        .first()
    )

    top_ranked = []
    worst_ranked = None

    if latest_rank:
        top_ranked = (
            db.query(MonthlyRankPrediction)
            .filter(
                MonthlyRankPrediction.month == latest_rank.month,
                MonthlyRankPrediction.year == latest_rank.year
            )
            .order_by(MonthlyRankPrediction.rank.asc())
            .limit(10)
            .all()
        )

        worst_ranked = (
            db.query(MonthlyRankPrediction)
            .filter(
                MonthlyRankPrediction.month == latest_rank.month,
                MonthlyRankPrediction.year == latest_rank.year
            )
            .order_by(MonthlyRankPrediction.rank.desc())
            .first()
        )

    # --- Most anomalous stock (latest month) ---
    latest_anomaly_month = (
        db.query(
            Anomaly.month,
            Anomaly.year
        )
        .order_by(desc(Anomaly.detected_at))
        .first()
    )

    most_anomalous = None

    if latest_anomaly_month:
        most_anomalous = (
            db.query(Anomaly)
            .filter(
                Anomaly.month == latest_anomaly_month.month,
                Anomaly.year == latest_anomaly_month.year
            )
            .order_by(desc(Anomaly.anomaly_score))
            .first()
        )
    db.close()
    return {
        "daily_risk": {
            "least_risky_stock": least_risky,
            "most_risky_stock": most_risky,
        },
        "ranking": {
            "month": latest_rank.month if latest_rank else None,
            "year": latest_rank.year if latest_rank else None,
            "top_ranked_stocks": top_ranked,
            "most_risky_ranked_stock": worst_ranked
        },
        "anomaly": {
            "most_anomalous_stock": most_anomalous
        }
    }
