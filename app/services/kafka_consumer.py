import json
import os
import threading
from datetime import datetime
from typing import Union

import pandas as pd
from confluent_kafka import Consumer
from sqlalchemy.orm import Session

from app.db.models.risk_monthly import RiskMonthly
from app.db.session import SessionLocal
from app.db.models.ohlcv import OHLCV
from app.core.config import settings
from app.models.artifacts.ML_model import predict
from app.services.Anomaly.AnomalyDetection import weekly_train, daily_predict, FEATURE_COLS
from app.services.Anomaly.AnomalyKafka import SendAnomalyUsingKafka
from app.services.Helpers import insert_ohlcv, compute_daily_risk, maybe_retrain_anomaly_model, prepare_daily_features, \
    detect_daily_anomalies, process_monthly_risk, run_monthly_prediction, dispatch_kafka
from app.services.Kafka.PredictionKafka import SendPredictionUsingKafka
from app.services.risk_service import last_monthly_risk
from app.services.risk_transformer import fetch_monthly_risk

from app.services.tasks import process_ohlcv_for_risk, process_monthly_ohlcv_for_risk, insert_anomalies, \
    insert_monthly_predictions

consumer_running = False
consumer = None



def insert_ohlcv_to_db(data: dict):
    db: Session = SessionLocal()

    try:
        if not insert_ohlcv(db, data):
            return

        daily_risk_df = compute_daily_risk(db, data["ticker"])
        if daily_risk_df is None:
            return

        dt = maybe_retrain_anomaly_model(db, data["date"])

        clean_df = prepare_daily_features(daily_risk_df, FEATURE_COLS)
        anomalies = detect_daily_anomalies(clean_df) if clean_df is not None else None

        process_monthly_risk(db, dt)
        predictions = run_monthly_prediction(db, dt)


        dispatch_kafka(predictions, anomalies)

        #note made changes here so take care test this
        inserted = insert_anomalies(db, anomalies)
        inserted = insert_monthly_predictions(db, predictions)

    except Exception as e:
        print(f"Pipeline fatal error: {e}")
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
