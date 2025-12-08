import pandas as pd
from tensorflow import keras
import pickle as pkl

modelpath = "./Riskmodel_dense.keras"
encoderpath ="../../MainApp/app/models/artifacts/encoder.pkl"
model = keras.models.load_model(modelpath)
encoder =pkl.load(open(encoderpath, "rb"))

def preprocess(df: pd.DataFrame,ticker_column='ticker'):

    ticker_encoded = encoder.transform(df[[ticker_column]])

    ticker_df = pd.DataFrame(ticker_encoded,
                             columns=encoder.get_feature_names_out([ticker_column]),
                             index=df.index
                             )
    df = df.drop(columns=[ticker_column,'date','month','rank'], errors='ignore')
    df = pd.concat([df,ticker_df], axis=1)
    return df

def predict(df: pd.DataFrame):
    predictions = model.predict(df)
    return predictions

def train_model(df: pd.DataFrame):
    X = preprocess(df)
    y = df['rank']
    model.fit(X, y, epochs=5, batch_size=32)



