from pydantic import BaseModel
from datetime import date

class RiskFactorBase(BaseModel):
    date: date
    ticker: str
    adj_close: float
    return_val: float
    volatility_14d: float
    downside_vol_30d: float
    var_95: float
    cvar_95: float
    max_drawdown_60d: float
    sharpe_30d: float
    model_config = {
        "from_attributes": True
    }


class RiskFactorCreate(RiskFactorBase):
    pass

class RiskFactorResponse(RiskFactorBase):
    id: int

    class Config:
        orm_mode = True

