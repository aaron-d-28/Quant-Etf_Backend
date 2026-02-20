from dataclasses import Field

from pydantic import BaseModel
from datetime import date

class TickerDateRequest(BaseModel):
    ticker: str
    date: date


class YearMonthRequest(BaseModel):
    year: int
    month: str

from typing import Optional

class MonthAnomalyRequest(BaseModel):
    year: int
    month: str          # varchar(5)
    ticker: Optional[str] = None

class RiskRequest(BaseModel):
    ticker: Optional[str] = None
    date: Optional[str] = None


class DashboardRequest(BaseModel):
    ticker: str = "QQQ"
    year: int = 2023
    month: int = 2
