import yfinance as yf
import numpy as np
from sklearn.svm import SVR


def predict_stock(stock, days):

    df = yf.download(stock, period="60d")

    X = np.arange(len(df)).reshape(-1, 1)

    y = df["Close"].values

    model = SVR(kernel="rbf")

    model.fit(X, y)

    future = np.arange(len(df), len(df) + days).reshape(-1, 1)

    preds = model.predict(future)

    return df, preds