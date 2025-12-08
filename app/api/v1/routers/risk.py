from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.risk_factor import RiskFactor
from app.schemas.risk_factor import RiskFactorCreate, RiskFactorResponse



router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=RiskFactorResponse)
def create_risk_factor(payload: RiskFactorCreate, db: Session = Depends(get_db)):
    risk = RiskFactor(**payload.dict())
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk

