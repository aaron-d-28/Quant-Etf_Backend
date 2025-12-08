from datetime import datetime

from sqlalchemy.orm import Session

from app.models.artifacts.ML_model import train_model
from app.services.risk_transformer import fetch_monthly_risk


def last_monthly_risk(db:Session,date: datetime):
    if date.month == 1:
        prev_month = 12
        prev_year = date.year - 1
    else:
        prev_month = date.month - 1
        prev_year = date.year
    data = fetch_monthly_risk(db, str(prev_month), prev_year)
    try:
        train_model(data)
    except Exception as e:
        print(f"Error while training the model :{e}")
    return data
