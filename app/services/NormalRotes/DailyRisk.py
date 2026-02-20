from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import timedelta

from app.db.models.risk_factor import RiskFactor
from app.db.session import SessionLocal
from app.services.DataRouters.RequestSchema import RiskRequest  # wherever you put it

router = APIRouter()


@router.post("/risk")
def get_risk(payload: RiskRequest):
    db: Session = SessionLocal()

    try:
        ticker = payload.ticker.upper() if payload.ticker else None
        date = payload.date

        # ❌ Invalid request
        if not ticker and not date:
            raise HTTPException(
                status_code=400,
                detail="Provide at least ticker or date"
            )

        # 📅 Date provided → exact date lookup
        if date:
            q = db.query(RiskFactor).filter(RiskFactor.date == date)

            if ticker:
                q = q.filter(RiskFactor.ticker == ticker)

            results = q.all()

            if not results:
                return {
                    "date": date,
                    "ticker": ticker,
                    "count": 0,
                    "risks": []
                }

            return {
                "date": date,
                "ticker": ticker,
                "count": len(results),
                "risks": results
            }

        # 📈 Ticker only → latest 30 days DAILY data
        latest_date = (
            db.query(RiskFactor.date)
            .filter(RiskFactor.ticker == ticker)
            .order_by(desc(RiskFactor.date))
            .first()
        )

        if not latest_date:
            return {
                "ticker": ticker,
                "count": 0,
                "daily_risk": []
            }

        end_date = latest_date.date
        start_date = end_date - timedelta(days=30)

        risks = (
            db.query(RiskFactor)
            .filter(
                RiskFactor.ticker == ticker,
                RiskFactor.date >= start_date,
                RiskFactor.date <= end_date
            )
            .order_by(RiskFactor.date.asc())
            .all()
        )

        return {
            "ticker": ticker,
            "from": str(start_date),
            "to": str(end_date),
            "count": len(risks),
            "daily_risk": risks
        }

    finally:
        db.close()
