import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import date, timedelta
from model import predict_stock

app = dash.Dash(__name__)
server = app.server


app.layout = html.Div(className="container", children=[

    # LEFT PANEL
    html.Div(className="inputs", children=[

        html.H2("Stock Dashboard"),

        html.P("Enter a stock ticker to start (e.g., AAPL, TSLA)"),

        dcc.Input(
            id="stock-input",
            type="text",
            placeholder="Example: AAPL",
            style={
                "color": "black",
                "backgroundColor": "white",
                "padding": "10px",
                "width": "100%"
            }
        ),

        html.Button("Submit", id="submit-btn"),

        html.Label("Select Date Range"),

        dcc.DatePickerRange(
            id="date-picker",
            start_date=date.today() - timedelta(days=365),
            end_date=date.today(),
            display_format="YYYY-MM-DD",
            style={"width": "100%"}
        ),

        html.Br(),

        dcc.Input(
            id="days-input",
            type="number",
            placeholder="Forecast days (e.g. 20)",
            style={
                "color": "black",
                "backgroundColor": "white",
                "padding": "10px",
                "width": "100%"
            }
        ),

        html.Button("Forecast", id="forecast-btn")

    ]),

    # RIGHT PANEL
    html.Div(className="outputs", children=[

        html.H2("Company Information"),

        html.Div(id="company-info"),

        dcc.Loading(dcc.Graph(id="price-graph"), type="circle"),
        dcc.Loading(dcc.Graph(id="indicator-graph"), type="circle"),
        dcc.Loading(dcc.Graph(id="forecast-graph"), type="circle"),

        html.Div(id="forecast-text", style={"marginTop": "10px", "fontSize": "15px"})

    ])
])


# ✅ PREMIUM COMPANY INFO
@app.callback(
    Output("company-info", "children"),
    Input("submit-btn", "n_clicks"),
    State("stock-input", "value")
)
def update_company(n_clicks, stock):

    if not stock:
        return "Enter a stock code"

    stock = stock.upper()

    try:
        ticker = yf.Ticker(stock)
        info = ticker.info

        name = info.get("shortName", stock)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        country = info.get("country", "N/A")
        market_cap = info.get("marketCap", "N/A")

        # Format market cap nicely
        if market_cap != "N/A":
            market_cap = f"${market_cap:,}"

        summary = (
            info.get("longBusinessSummary") or
            info.get("longDescription") or
            info.get("description") or
            "No description available"
        )

        return html.Div([
            html.H3(name),

            html.Div([
                html.P(f"📊 Sector: {sector}"),
                html.P(f"🏭 Industry: {industry}"),
                html.P(f"🌍 Country: {country}"),
                html.P(f"💰 Market Cap: {market_cap}")
            ], style={"marginBottom": "10px"}),

            html.P(summary, style={"fontSize": "14px", "lineHeight": "1.5"})
        ])

    except Exception as e:
        print("Company info error:", e)
        return "Invalid stock code"


# STOCK PRICE (AUTO LOAD)
@app.callback(
    Output("price-graph", "figure"),
    Input("submit-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_price(n_clicks, stock, start, end):

    if not stock:
        return go.Figure().update_layout(title="Enter stock to view data")

    stock = stock.upper()

    try:
        if start is None or end is None:
            end = pd.Timestamp.today()
            start = end - pd.Timedelta(days=365)

        df = yf.download(stock, start=start, end=end)

        if df.empty:
            return go.Figure().update_layout(title="No data available")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])

        fig.update_layout(title=f"{stock} Stock Price (Candlestick)")

        return fig

    except Exception as e:
        print("Price error:", e)
        return go.Figure().update_layout(title="Error loading data")


# EMA INDICATOR
@app.callback(
    Output("indicator-graph", "figure"),
    Input("submit-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_indicator(n_clicks, stock, start, end):

    if not stock:
        return go.Figure()

    stock = stock.upper()

    try:
        if start is None or end is None:
            end = pd.Timestamp.today()
            start = end - pd.Timedelta(days=365)

        df = yf.download(stock, start=start, end=end)

        if df.empty:
            return go.Figure().update_layout(title="No data available")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["EMA"] = df["Close"].ewm(span=20).mean()

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close"))
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA"], name="EMA"))

        fig.update_layout(title="EMA Indicator")

        return fig

    except Exception as e:
        print("Indicator error:", e)
        return go.Figure().update_layout(title="Error loading indicator")


# FORECAST + DYNAMIC TEXT
@app.callback(
    [Output("forecast-graph", "figure"),
     Output("forecast-text", "children")],
    Input("forecast-btn", "n_clicks"),
    State("stock-input", "value"),
    State("days-input", "value")
)
def forecast(n_clicks, stock, days):

    fig = go.Figure()

    if not n_clicks:
        return fig, ""

    if not stock or not days:
        return fig, "Please enter stock and forecast days."

    stock = stock.upper()

    try:
        df, preds = predict_stock(stock, int(days))

        if df is None or df.empty:
            return fig, "No data available."

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        if "Date" not in df.columns:
            df.rename(columns={df.columns[0]: "Date"}, inplace=True)

        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="Actual"
        ))

        last_date = pd.to_datetime(df["Date"].iloc[-1])
        future_dates = pd.date_range(start=last_date, periods=int(days)+1)[1:]

        fig.add_trace(go.Scatter(
            x=future_dates,
            y=preds,
            mode="lines",
            name="Forecast"
        ))

        fig.update_layout(title=f"{stock} Price Forecast")

        # 🔥 Smart Explanation
        start_price = round(preds[0], 2)
        end_price = round(preds[-1], 2)

        change_pct = round(((end_price - start_price) / start_price) * 100, 2)

        trend = "upward 📈" if change_pct > 0 else "downward 📉"

        forecast_text = (
            f"{stock} is expected to move from ${start_price} to ${end_price} "
            f"over the next {days} days (~{change_pct}%), indicating a {trend} trend."
        )

        return fig, forecast_text

    except Exception as e:
        print("Forecast error:", e)
        return fig, "Error generating forecast."


if __name__ == "__main__":
    app.run(debug=True)