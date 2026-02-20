from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.models.artifacts.ML_model import train_model
from app.services.risk_transformer import fetch_monthly_risk


def last_monthly_risk(date: datetime,db: Session ):
    if date.month == 1:
        prev_month = 12
        prev_year = date.year - 1
    else:
        prev_month = date.month - 1
        prev_year = date.year
    data = fetch_monthly_risk(db=db, month=str(prev_month), year=prev_year,as_df=True)
    try:
        istrain=train_model(data)
        if istrain==True:
            print("Trained model!!!!!!!!")
        else:
            print(f"Model not trained!!!!!!!!!::Month is:{prev_month} Year:{prev_year} ")
    except Exception as e:
        print(f"Error while training the model::Check the cols  :{e} ::{data.columns}")
        return "Error while training the model :",e
    db.close()
    return True
