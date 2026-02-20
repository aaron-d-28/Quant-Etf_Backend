import uuid
from datetime import datetime

from app.services.Kafka.PredictionKafka import producer
RISK_TOPIC_NAME="daily_risk"
def SendDailyRiskUsingKafka(Data: dict):
    message = {
        "risk_id": str(uuid.uuid4()),
        "ticker": Data["ticker"],
        "date": Data["date"].isoformat() if hasattr(Data["date"], "isoformat") else Data["date"],
        "data": [{
            "adj_close": Data.get("adj_close"),
            "return_val": Data["return_val"],
            "volatility_14d": Data["volatility_14d"],
            "downside_vol_30d": Data["downside_vol_30d"],
            "var_95": Data["var_95"],
            "cvar_95": Data["cvar_95"],
            "max_drawdown_60d": Data["max_drawdown_60d"],
            "sharpe_30d": Data["sharpe_30d"]
        }],
    }
    key = Data["ticker"]+Data["date"].isoformat() if hasattr(Data["date"], "isoformat") else Data["date"]

    producer.send(
        topic=RISK_TOPIC_NAME,
        key=key,
        value=message
    )
    producer.flush()

    print(f"Sent daily risk → {message.keys()}")
