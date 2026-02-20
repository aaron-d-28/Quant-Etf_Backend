import pandas as pd
from kafka import KafkaProducer
import json
import time
from datetime import datetime
import uuid

KAFKA_BROKER = "localhost:9092"   # change if needed
TOPIC_NAME = "predictions"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
    acks="all",
    retries=3
)
def SendPredictionUsingKafka(Data: list):
    for item in Data:
        message = {
            "Month": item["month"],
            "Year": item["year"],
            "Rank": item["prediction"],
            "Ticker": item["ticker"],
            "prediction_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }

        key = f"{item['ticker']}-{item['year']}-{item['month']}"

        producer.send(
            topic=TOPIC_NAME,
            key=key,        # ✅ STRING
            value=message   # ✅ dict → JSON → bytes via value_serializer
        )

        print(f"Sent prediction of the best ETFs → {message}")

    producer.flush()
