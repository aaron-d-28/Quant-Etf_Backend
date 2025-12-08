from sqlalchemy import Column, String, Float, Integer, Date
from app.db.base import Base

class RiskMonthly(Base):
    __tablename__ = "risk_monthly"

    # Composite primary key
    ticker = Column(String, primary_key=True, nullable=False, index=True)
    month = Column(Date, primary_key=True, nullable=False)   # correct type

    monthly_return = Column(Float)
    monthly_volatility = Column(Float)
    downside_vol_monthly = Column(Float)
    var_95_monthly = Column(Float)
    cvar_95_monthly = Column(Float)
    max_drawdown_monthly = Column(Float)
    sharpe_monthly = Column(Float)

    return_p = Column(Float)
    sharpe_p = Column(Float)
    vol_p = Column(Float)
    downside_p = Column(Float)
    var_p = Column(Float)
    cvar_p = Column(Float)
    dd_p = Column(Float)

    safety_score = Column(Float)
    rank = Column(Integer)   # correct type (integer)

    # Newly added columns
    date = Column(Date)
    year = Column(Integer)
    month_sin = Column(Float)
    month_cos = Column(Float)
