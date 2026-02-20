import pandas as pd
from kafka import KafkaProducer
import json
import time
from datetime import datetime
import uuid

from app.services.Kafka.PredictionKafka import producer

KAFKA_BROKER = "localhost:9092"   # change if needed
ANOMALY_TOPIC  = "Anomalies"

def SendAnomalyUsingKafka(df: pd.DataFrame):
    if df.empty:
        print("Empty DataFrame!!!")
        return
    for _, row in df.iterrows():
        message = {
            "anomaly_id": str(uuid.uuid4()),
            "ticker": row["ticker"],
            "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else row["date"],
            "timestamp": datetime.utcnow().isoformat(),
            "anomaly_score": row["anomaly_score"],
            "is_anomaly": row["is_anomaly"],
        }

        producer.send(
            topic=ANOMALY_TOPIC,
            key=f"{row['ticker']}-{row['date']}",
            value=message
        )

    producer.flush()
    print(f"Sent {len(df)} anomalies → Kafka")

