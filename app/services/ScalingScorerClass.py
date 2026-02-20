from sklearn.preprocessing import StandardScaler
import pickle
import os

class SafetyScorer:
    ScalerCols  = [
        "monthly_return",
        "monthly_volatility",
        "downside_vol_monthly",
        "var_95_monthly",
        "cvar_95_monthly",
        "max_drawdown_monthly",
        "sharpe_monthly",
        "year",
    ]

    def __init__(self, scaler_path="safety_scaler.pkl"):
        self.scaler_path = scaler_path
        self.scaler = None
        self.pickle = pickle

    # -------------------------------
    # Fit scaler on a DataFrame
    # -------------------------------
    def fit_scaler(self, df):
        self.scaler = StandardScaler()
        self.scaler.fit(df[self.SAFETY_COLS])

        with open(self.scaler_path, "wb") as f:
            self.pickle.dump(self.scaler, f)

        return self

    # -------------------------------
    # Load scaler from disk
    # -------------------------------
    def load_scaler(self):
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError("Safety scaler not found. Fit first.")

        with open(self.scaler_path, "rb") as f:
            self.scaler = self.pickle.load(f)
        return self

    # -------------------------------
    # Compute safety score from current scaler
    # -------------------------------
    def compute_score(self, df):
        if self.scaler is None:
            self.load_scaler()

        Z = self.scaler.transform(df[self.SAFETY_COLS])

        df["safety_score"] = (
                0.15 * Z[:, 0] +   # return_p
                0.20 * Z[:, 1] +   # sharpe_p
                0.15 * Z[:, 2] +   # vol_p
                0.15 * Z[:, 3] +   # downside_p
                0.15 * Z[:, 4] +   # var_p
                0.10 * Z[:, 5] +   # cvar_p
                0.10 * Z[:, 6]     # dd_p
        )

        return df

    # -------------------------------
    # Rank assets by safety score
    # -------------------------------
    def rank_assets(self, df):
        df["rank"] = (
            df.groupby(["year", "month"])["safety_score"]
            .rank(ascending=False, method="first")
        )
        return df

    # -------------------------------
    # Daily update (use existing scaler)
    # -------------------------------
    def daily_update(self, df):
        """
        Use the latest saved scaler to compute safety score and rank daily data
        """
        self.load_scaler()
        df = self.compute_score(df)
        df = self.rank_assets(df)
        return df

    # -------------------------------
    # Weekly refit (use rolling data)
    # -------------------------------
    def weekly_refit(self, df):
        """
        Refit scaler on recent weekly/rolling data,
        then compute safety score and rank
        """
        self.fit_scaler(df)
        df = self.compute_score(df)
        df = self.rank_assets(df)
        return df
