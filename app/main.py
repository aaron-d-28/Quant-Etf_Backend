from fastapi import FastAPI
from tensorflow.python.ops.distributions.normal import Normal

from app.services.NormalRotes import AnomaliesRoute, Dashboard, DailyRisk, PredictedRanks
from .api.v1.routers import risk,reset, ohlcv
from .api.v1.routers import Kafka as kafka
from fastapi.middleware.cors import CORSMiddleware  

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# note  aaron@Aarons-hp:~/Desktop/Coding/QuantEtf/MainApp$ uvicorn app.main:app --host 0.0.0.0 --port 6000 --reload

@app.get("/")
def root():
    return {"message": "hello"}

app.include_router(risk.router, prefix="/risk", tags=["Risk Factor"])


app.include_router(ohlcv.router, prefix="/ohlcv", tags=["OHLCV"])

app.include_router(kafka.router, prefix="/kafka", tags=["Kafka"])


app.include_router(reset.router, prefix="/admin", tags=["Admin"])

app.include_router(AnomaliesRoute.router, prefix="/anomalies", tags=["Anomalies"])

app.include_router(Dashboard.router, prefix="/dashboard", tags=["Dashboard"])

app.include_router(DailyRisk.router, prefix="/Dailyrisk", tags=["Risk"])

app.include_router(PredictedRanks.router, prefix="/predictedranks", tags=["Predicted Ranks"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000,reload=True)