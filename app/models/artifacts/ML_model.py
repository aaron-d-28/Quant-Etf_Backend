import pandas as pd
from tensorflow import keras
import pickle as pkl
import os
BASE_DIR = os.path.dirname(__file__)
modelpath = os.path.join(BASE_DIR, "Riskmodel_Fixed_1-25-2026.keras")
encoderpath = os.path.join(BASE_DIR, "encoder.pkl")
model = keras.models.load_model(modelpath)
encoder =pkl.load(open(encoderpath, "rb"))



def one_hot_encode_tickers(df, ticker_column='ticker'):
    ticker_encoded = encoder.transform(df[[ticker_column]])
    ticker_df = pd.DataFrame(
        ticker_encoded,
        columns=encoder.get_feature_names_out([ticker_column])
    )
    return pd.concat(
        [df.reset_index(drop=True), ticker_df.reset_index(drop=True)],
        axis=1
    )

def preprocess(X)-> pd.DataFrame:
    X = X.copy()
    predictionCols = ['monthly_return', 'monthly_volatility', 'downside_vol_monthly',
                      'var_95_monthly', 'cvar_95_monthly', 'max_drawdown_monthly',
                      'sharpe_monthly', 'year', 'month_sin', 'month_cos','ticker']
    for col in predictionCols:
        if col not in X.columns:
            raise ValueError(f"Missing required feature: {col}::All columns are {X.columns}")
    X = X[predictionCols]
    X = one_hot_encode_tickers(X, ticker_column='ticker')
    X.drop(columns=['ticker','date'], inplace=True,errors='ignore')

    return X


def predict(df: pd.DataFrame):
    if isinstance(df, list):
        df = pd.DataFrame(df)

    if df.empty:
        print("Prediction skipped: empty dataframe")
        return []
    df = preprocess(df)
    predictions = model.predict(df)
    return predictions

def train_model(df: pd.DataFrame):
    try:
        if df is None or df.empty:
            print("Monthly training skipped: empty dataset")
            return False
        X = preprocess(df)
        y = df['rank']
        model.fit(X, y, epochs=5, batch_size=32)
        return True
    except Exception as e:
        print(f"Model training Error: {e}")
        return False


