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

@router.post("/", response_model=OHLCVResponse)
def create_ohlcv(payload: OHLCVCreate, db: Session = Depends(get_db)):
    record = OHLCV(**payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

