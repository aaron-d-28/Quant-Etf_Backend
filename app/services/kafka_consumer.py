import json
import threading
from datetime import datetime

from confluent_kafka import Consumer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.ohlcv import OHLCV
from app.core.config import settings
from app.services.risk_service import last_monthly_risk

from app.services.tasks import process_ohlcv_for_risk, process_monthly_ohlcv_for_risk

consumer_running = False
consumer = None


def insert_ohlcv_to_db(data: dict):
    db: Session = SessionLocal()
    try:
        rec = OHLCV(
            date=data["date"],
            ticker=data["ticker"],
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=float(data["volume"]),
            adj_close=float(data["adj_close"]),
        )

        db.add(rec)
        db.commit()
        print(f"Inserted {rec}")
        process_ohlcv_for_risk(data["ticker"])
        dt = datetime.strptime(data["date"], "%Y-%m-%d")
        if dt.day==1:
            if dt.month == 1:
                prev_month = 12
                prev_year = dt.year - 1
            else:
                prev_month = dt.month - 1
                prev_year = dt.year
            prev_month_str = f"{prev_year}-{prev_month:02d}"  # e.g., "2025-11"
            process_monthly_ohlcv_for_risk(prev_month_str)
            last_monthly_risk(db,dt)



    except Exception as e:
        print(f"DB insert error:Dataframe not Proper it is{data}", e)
        db.rollback()
    finally:
        db.close()


def kafka_loop():
    global consumer

    consumer = Consumer({
        "bootstrap.servers": settings.KAFKA_BROKER,
        "group.id": "ohlcv_group",
        "auto.offset.reset": "earliest",
    })

    consumer.subscribe([settings.KAFKA_TOPIC])
    print(f"Kafka consumer started on topic: {settings.KAFKA_TOPIC}")

    try:
        while consumer_running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                print("Kafka error:", msg.error())
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                insert_ohlcv_to_db(data)

            except Exception as e:
                print("Message handling error:", e)

    finally:
        print("Closing Kafka consumer...")
        consumer.close()


def start_consumer():
    global consumer_running

    if consumer_running:
        return False

    consumer_running = True
    thread = threading.Thread(target=kafka_loop, daemon=True)
    thread.start()

    return True


def stop_consumer():
    global consumer_running, consumer
    consumer_running = False
    return True
