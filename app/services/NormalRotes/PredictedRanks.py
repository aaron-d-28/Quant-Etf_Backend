from fastapi import APIRouter, Query, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models.MonthlyRankPrediction import MonthlyRankPrediction
from app.db.session import get_db, SessionLocal
from app.services.DataRouters.RequestSchema import YearMonthRequest

router = APIRouter()

@router.post("/ranks")
def get_ranked_stocks(
        payload:YearMonthRequest

):

    month = payload.month
    year = payload.year
    db: Session = SessionLocal()
    if month is None or year is None:
        latest = (
            db.query(
                MonthlyRankPrediction.month,
                MonthlyRankPrediction.year
            )
            .order_by(desc(MonthlyRankPrediction.created_at))
            .first()
        )

        if not latest:
            db.close()
            return {"message": "No rankings available"}

        month, year = latest.month, latest.year

    ranks = (
        db.query(MonthlyRankPrediction)
        .filter(
            MonthlyRankPrediction.month == month,
            MonthlyRankPrediction.year == year
        )
        .order_by(MonthlyRankPrediction.rank.asc())
        .all()
    )
    db.close()

    return {
        "month": month,
        "year": year,
        "total": len(ranks),
        "rankings": ranks
    }
