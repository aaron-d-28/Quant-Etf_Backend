from fastapi import APIRouter
from app.services.kafka_consumer import start_consumer, stop_consumer
router = APIRouter()

@router.post("/start")
def start_kafka_consumer():
    ok = start_consumer()
    if ok:
        return {"message": "Kafka consumer started"}
    return {"message": "Kafka consumer is already running"}

@router.post("/stop")
def stop_kafka_consumer_api():
    stop_consumer()
    return {"message": "Kafka consumer stopped"}
