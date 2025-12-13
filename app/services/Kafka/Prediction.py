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

def SendPredictionUsingKafka(Data):
    message = {
        "prediction_id": str(uuid.uuid4()),
        "Month": Data.month,
        "timestamp": datetime.utcnow().isoformat(),
        "Year":Data.year,
        "Rank":Data.prediction,
        "Ticker": Data.ticker,

    }

    producer.send(
        topic=TOPIC_NAME,
        key=Data.ticker+Data.year+Data.month,
        value=message
    )

    producer.flush()
    print(f"Sent prediction → {message}")