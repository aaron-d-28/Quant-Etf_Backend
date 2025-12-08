from sqlalchemy import Column, Integer, Float, String, Date
from app.db.base import Base

class OHLCV(Base):
    __tablename__ = "ohlcv"


    date = Column("time", Date, primary_key=True)
    ticker = Column(String, primary_key=True,)
    open = Column("openprice", Float)
    high = Column("highprice", Float)
    low = Column("lowprice", Float)
    close = Column("closeprice", Float)
    volume = Column(Float)
    adj_close = Column("adjclose", Float)
