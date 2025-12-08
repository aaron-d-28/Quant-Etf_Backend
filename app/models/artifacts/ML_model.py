import pandas as pd
from tensorflow import keras
import pickle as pkl

modelpath = "./Riskmodel_Dense.keras"
encoderpath ="../../MainApp/app/models/artifacts/encoder.pkl"
model = keras.models.load_model(modelpath)
encoder =pkl.load(open(encoderpath, "rb"))

def preprocess(df: pd.DataFrame,ticker_column='ticker'):
    colstodrop=['date','month','rank','ticker','return_p','sharpe_p','vol_p','downside_p','var_p','cvar_p','dd_p']
    ticker_encoded = encoder.transform(df[[ticker_column]])

    ticker_df = pd.DataFrame(ticker_encoded,
                             columns=encoder.get_feature_names_out([ticker_column]),
                             index=df.index
                             )
    df = df.drop(columns=colstodrop, errors='ignore')
    df = pd.concat([df,ticker_df], axis=1)
    return df

def predict(df: pd.DataFrame):
    predictions = model.predict(df)
    return predictions

def train_model(df: pd.DataFrame):
    X = preprocess(df)
    y = df['rank']
    model.fit(X, y, epochs=5, batch_size=32)



