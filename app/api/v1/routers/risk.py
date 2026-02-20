from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.risk_monthly import RiskMonthly
from app.db.session import SessionLocal
from app.db.models.risk_factor import RiskFactor
from app.schemas.risk_factor import RiskFactorCreate, RiskFactorResponse
from app.services.DataRouters.RequestSchema import TickerDateRequest


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_data_for_ticker_and_date(ticker, date):
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(RiskMonthly)
            .filter(RiskMonthly.ticker == ticker)
            .filter(RiskMonthly.date == date)
            .all()
        )
        return rows
    finally:
        db.close()


@router.post("/RiskMonthly",response_model=None)
def fetch_ticker_data(payload: TickerDateRequest):
    ticker = payload.ticker.upper()
    target_date = payload.date

    # Example: pull from database / dataframe / service
    data = get_data_for_ticker_and_date(ticker, target_date)

    if data is None or len(data) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {ticker} on {target_date}"
        )

    return {
        "ticker": ticker,
        "date": target_date,
        "data":data
    }

@router.post("/")
def create_risk_factor():

    return {
        "Working":True
    }
