from pydantic import BaseModel
from datetime import date

class OHLCVBase(BaseModel):
    date: date
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: float
    
    model_config = {
        "from_attributes": True
    }


class OHLCVCreate(OHLCVBase):
    pass

class OHLCVResponse(OHLCVBase):
    id: int

    class Config:
        orm_mode = True

