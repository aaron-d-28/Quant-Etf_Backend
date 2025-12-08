from pydantic import BaseModel
from datetime import date
from typing import Optional

class RiskMonthlyBase(BaseModel):
    ticker: str
    month: date                     # correct type
    monthly_return: float
    monthly_volatility: float
    downside_vol_monthly: float
    var_95_monthly: float
    cvar_95_monthly: float
    max_drawdown_monthly: float
    sharpe_monthly: float
    return_p: float
    sharpe_p: float
    vol_p: float
    downside_p: float
    var_p: float
    cvar_p: float
    dd_p: float
    safety_score: float
    rank: int                       # correct type

    # newly added 4 columns
    date: Optional[date] = None
    year: Optional[int] = None
    month_sin: Optional[float] = None
    month_cos: Optional[float] = None

    model_config = {"from_attributes": True}


class RiskMonthlyCreate(RiskMonthlyBase):
    pass


class RiskMonthlyResponse(RiskMonthlyBase):
    class Config:
        orm_mode = True
