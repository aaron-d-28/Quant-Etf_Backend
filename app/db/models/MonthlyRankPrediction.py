import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    func
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class MonthlyRankPrediction(Base):
    __tablename__ = "monthly_rank_predictions"

    prediction_id = Column(
        "prediction_id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ticker = Column(
        "ticker",
        String(20),
        nullable=False
    )

    year = Column(
        "year",
        Integer,
        nullable=False
    )

    month = Column(
        "month",
        String(5),   # <-- varchar(5)
        nullable=False
    )

    rank = Column(
        "rank",
        Float,
        nullable=False
    )

    model_version = Column(
        "model_version",
        String(50),
        nullable=True
    )

    created_at = Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
