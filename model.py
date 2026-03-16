import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.svm import SVR


def predict_stock(stock, days):

    df = yf.download(stock, period="60d")

    df = df[["Close"]]

    df["Prediction"] = df["Close"].shift(-days)

    X = np.array(df.drop(["Prediction"], axis=1))[:-days]

    y = np.array(df["Prediction"])[:-days]

    model = SVR(kernel="rbf")

    model.fit(X, y)

    x_forecast = np.array(df.drop(["Prediction"], axis=1))[-days:]

    predictions = model.predict(x_forecast)

    return df, predictions