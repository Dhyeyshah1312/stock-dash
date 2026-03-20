import yfinance as yf
import numpy as np
from sklearn.svm import SVR


def predict_stock(stock, days):

    df = yf.download(stock, period="60d")

    if df.empty:
        return None, None

    if isinstance(df.columns, tuple):
        df.columns = df.columns.get_level_values(0)

    X = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].values.ravel()

    model = SVR(kernel="rbf")
    model.fit(X, y)

    future = np.arange(len(df), len(df) + days).reshape(-1, 1)
    preds = model.predict(future)

    return df, preds