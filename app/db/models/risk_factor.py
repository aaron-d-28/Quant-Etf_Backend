from sqlalchemy import Column, Integer, String, Float, Date
from app.db.base import Base

class RiskFactor(Base):
    __tablename__ = "risk_factor"

    date = Column("date", Date, nullable=False, primary_key=True)
    ticker = Column("ticker", String, nullable=False, index=True, primary_key=True)

    adj_close = Column("adj_close", Float)
    return_val = Column("return", Float)
    volatility_14d = Column("volatility_14d", Float)
    downside_vol_30d = Column("downside_vol_30d", Float)
    var_95 = Column("var_95", Float)
    cvar_95 = Column("cvar_95", Float)
    max_drawdown_60d = Column("max_drawdown_60d", Float)
    sharpe_30d = Column("sharpe_30d", Float)


