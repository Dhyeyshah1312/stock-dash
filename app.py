import dash
from dash import dcc, html
import yfinance as yf
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State

# ML Model import
from model import forecast_stock

# ---------------- APP SETUP ----------------
app = dash.Dash(__name__)
server = app.server

# ---------------- LAYOUT ----------------
app.layout = html.Div(className="container", children=[

    # -------- LEFT PANEL --------
    html.Div(className="inputs", children=[
        html.H2("Welcome to the Stock Dash App!"),

        html.Label("Input stock code:"),
        dcc.Input(
            id="stock-input",
            type="text",
            placeholder="Enter stock code"
        ),

        html.Button("Submit", id="submit-btn"),

        html.Br(), html.Br(),

        dcc.DatePickerRange(
            id="date-picker"
        ),

        html.Br(), html.Br(),

        html.Button("Stock Price", id="price-btn"),
        html.Button("Indicators", id="indicator-btn"),

        html.Br(), html.Br(),

        dcc.Input(
            id="days-input",
            type="number",
            placeholder="number of days"
        ),

        html.Button("Forecast", id="forecast-btn"),
    ]),

    # -------- RIGHT PANEL --------
    html.Div(className="content", children=[
        html.H2("Output Area"),

        html.Div(id="company-info"),
        dcc.Graph(id="price-graph"),
        dcc.Graph(id="indicator-graph"),
        dcc.Graph(id="forecast-graph"),
    ])
])

# ---------------- HELPER FUNCTIONS ----------------

def get_stock_price_fig(df):
    fig = px.line(
        df,
        x="Date",
        y=["Open", "Close"],
        title="Opening vs Closing Price"
    )
    return fig


def get_indicator_fig(df):
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    fig = px.line(
        df,
        x="Date",
        y="EMA_20",
        title="20-Day Exponential Moving Average"
    )
    return fig


# ---------------- CALLBACKS ----------------

# Company Info Callback
@app.callback(
    Output("company-info", "children"),
    Input("submit-btn", "n_clicks"),
    State("stock-input", "value")
)
def update_company_info(n, stock):
    if not n or not stock:
        return "Enter stock code and click Submit"

    ticker = yf.Ticker(stock)
    info = ticker.info

    name = info.get("shortName", "N/A")
    summary = info.get("longBusinessSummary", "No description available")
    logo = info.get("logo_url", "")

    return html.Div([
        html.H3(name),
        html.Img(src=logo, style={"height": "60px"}) if logo else None,
        html.P(summary)
    ])


# Stock Price Graph Callback
@app.callback(
    Output("price-graph", "figure"),
    Input("price-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_price_graph(n, stock, start, end):
    if not n or not stock or not start or not end:
        return {}

    df = yf.download(stock, start=start, end=end)
    df.reset_index(inplace=True)

    return get_stock_price_fig(df)


# Indicator Graph Callback
@app.callback(
    Output("indicator-graph", "figure"),
    Input("indicator-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_indicator_graph(n, stock, start, end):
    if not n or not stock or not start or not end:
        return {}

    df = yf.download(stock, start=start, end=end)
    df.reset_index(inplace=True)

    return get_indicator_fig(df)


# Forecast Graph Callback (ML Model)
@app.callback(
    Output("forecast-graph", "figure"),
    Input("forecast-btn", "n_clicks"),
    State("stock-input", "value"),
    State("days-input", "value")
)
def update_forecast(n, stock, days):
    if not n or not stock or not days:
        return {}

    return forecast_stock(stock, days)


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)   