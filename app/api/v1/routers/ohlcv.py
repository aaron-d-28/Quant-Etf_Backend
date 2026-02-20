from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.ohlcv import OHLCV
from app.schemas.ohlcv import OHLCVCreate, OHLCVResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_ohlcv( ):

    return {
        "message": "hello testing ohlcv",
    }

