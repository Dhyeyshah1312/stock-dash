import yfinance as yf
import numpy as np
import pandas as pd
import plotly.express as px

from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error


def forecast_stock(stock, days):
    # Fetch last 60 days data
    df = yf.download(stock, period="60d")
    df.reset_index(inplace=True)

    # Use closing price
    data = df[["Close"]].values

    # Create time index
    X = np.arange(len(data)).reshape(-1, 1)
    y = data.ravel()

    # Train-test split (9:1)
    split = int(len(X) * 0.9)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # GridSearch for SVR
    params = {
        "C": [0.1, 1, 10],
        "gamma": ["scale", "auto"],
        "epsilon": [0.01, 0.1, 1],
        "kernel": ["rbf"]
    }

    grid = GridSearchCV(SVR(), params, cv=3)
    grid.fit(X_train, y_train)

    model = grid.best_estimator_

    # Predictions on test set
    preds = model.predict(X_test)

    # Metrics
    mse = mean_squared_error(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    print("MSE:", mse)
    print("MAE:", mae)

    # Future forecast
    future_X = np.arange(len(data), len(data) + int(days)).reshape(-1, 1)
    future_preds = model.predict(future_X)

    # Build forecast dataframe
    future_dates = pd.date_range(df["Date"].iloc[-1], periods=int(days)+1)[1:]

    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Forecast": future_preds
    })

    # Plot
    fig = px.line(forecast_df, x="Date", y="Forecast",
                  title="Stock Price Forecast")

    return fig