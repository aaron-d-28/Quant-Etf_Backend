import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    JSON,
    func
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    anomaly_id = Column(
        "anomaly_id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ticker = Column(
        "ticker",
        String(20),
        nullable=False
    )

    anomaly_score = Column(
        "anomaly_score",
        Float,
        nullable=False
    )

    anomaly_type = Column(
        "anomaly_type",
        String(50),
        nullable=True
    )

    detected_at = Column(
        "detected_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    year = Column(
        "year",
        Integer,
        nullable=False
    )

    month = Column(
        "month",
        String(5),   # <-- varchar(5) as requested
        nullable=False
    )

    source = Column(
        "source",
        String(50),
        nullable=True
    )

    feature_values = Column(
        "metadata",
        JSON,
        nullable=True
    )
