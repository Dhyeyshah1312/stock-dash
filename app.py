import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from model import predict_stock

app = dash.Dash(__name__)
server = app.server


app.layout = html.Div(className="container", children=[

    html.Div(className="inputs", children=[

        html.H2("Welcome to the Stock Dash App!"),

        html.Label("Input stock code:"),

        dcc.Input(
            id="stock-input",
            type="text",
            placeholder="Enter stock code (AAPL)",
            style={
                "color": "black",
                "backgroundColor": "white",
                "padding": "10px",
                "width": "100%"
            }
        ),

        html.Button("Submit", id="submit-btn"),

        html.Br(),
        html.Br(),

        dcc.DatePickerRange(id="date-picker"),

        html.Br(),
        html.Br(),

        html.Button("Stock Price", id="price-btn"),
        html.Button("Indicators", id="indicator-btn"),

        html.Br(),
        html.Br(),

        dcc.Input(
            id="days-input",
            type="number",
            placeholder="Forecast days",
            style={
                "color": "black",
                "backgroundColor": "white",
                "padding": "10px",
                "width": "100%"
            }
        ),

        html.Button("Forecast", id="forecast-btn")

    ]),

    html.Div(className="outputs", children=[

        html.H2("Output Area"),

        html.Div(id="company-info"),

        dcc.Graph(id="price-graph"),

        dcc.Graph(id="indicator-graph"),

        dcc.Graph(id="forecast-graph")

    ])
])


# COMPANY INFO
@app.callback(
    Output("company-info", "children"),
    Input("submit-btn", "n_clicks"),
    State("stock-input", "value")
)
def update_company(n_clicks, stock):

    if not stock:
        return ""

    stock = stock.upper()

    ticker = yf.Ticker(stock)
    info = ticker.info

    name = info.get("shortName", "N/A")
    summary = info.get("longBusinessSummary", "No description")

    return html.Div([
        html.H3(name),
        html.P(summary)
    ])


# STOCK PRICE GRAPH
@app.callback(
    Output("price-graph", "figure"),
    Input("price-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_price(n_clicks, stock, start, end):

    fig = go.Figure()

    if not stock:
        return fig

    stock = stock.upper()

    try:

        if start is None or end is None:
            end = pd.Timestamp.today()
            start = end - pd.Timedelta(days=365)

        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        df = yf.download(stock, start=start, end=end)

        if df.empty:
            return fig

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        fig = px.line(
            df,
            x="Date",
            y=["Open", "Close"],
            title=f"{stock} Stock Price"
        )

        return fig

    except Exception as e:
        print("Price graph error:", e)
        return fig


# EMA INDICATOR
@app.callback(
    Output("indicator-graph", "figure"),
    Input("indicator-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_indicator(n_clicks, stock, start, end):

    fig = go.Figure()

    if not stock:
        return fig

    stock = stock.upper()

    try:

        if start is None or end is None:
            end = pd.Timestamp.today()
            start = end - pd.Timedelta(days=365)

        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        df = yf.download(stock, start=start, end=end)

        if df.empty:
            return fig

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        df["EMA"] = df["Close"].ewm(span=20).mean()

        fig = px.line(
            df,
            x="Date",
            y=["Close", "EMA"],
            title="EMA Indicator"
        )

        return fig

    except Exception as e:
        print("Indicator error:", e)
        return fig


# FORECAST GRAPH
@app.callback(
    Output("forecast-graph", "figure"),
    Input("forecast-btn", "n_clicks"),
    State("stock-input", "value"),
    State("days-input", "value")
)
def forecast(n_clicks, stock, days):

    fig = go.Figure()

    if not n_clicks:
        return fig

    if not stock or not days:
        return fig

    stock = stock.upper()

    try:

        df, preds = predict_stock(stock, int(days))

        if df is None or df.empty:
            return fig

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        if "Date" not in df.columns:
            df.rename(columns={df.columns[0]: "Date"}, inplace=True)

        if "Close" not in df.columns:
            return fig

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

        return fig

    except Exception as e:
        print("Forecast error:", e)
        return fig


if __name__ == "__main__":
    app.run(debug=True)