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

    # LEFT SIDE
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

        html.Button("Forecast", id="forecast-btn")

    ]),

    # RIGHT SIDE
    html.Div(className="outputs", children=[

        html.H2("Output Area"),

        html.Div(id="company-info"),

        dcc.Graph(id="price-graph"),
        dcc.Graph(id="indicator-graph"),
        dcc.Graph(id="forecast-graph")

    ])

])


# COMPANY INFO CALLBACK
@app.callback(
    Output("company-info", "children"),
    Input("submit-btn", "n_clicks"),
    State("stock-input", "value")
)
def update_company(n_clicks, val):

    if not val:
        return "Enter stock code"

    try:
        ticker = yf.Ticker(val)
        info = ticker.info

        name = info.get("shortName", "N/A")
        summary = info.get("longBusinessSummary", "No description available")

        return html.Div([
            html.H3(name),
            html.P(summary)
        ])

    except:
        return "Invalid stock code"


# STOCK PRICE GRAPH
@app.callback(
    Output("price-graph", "figure"),
    Input("price-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_price(n_clicks, stock, start, end):

    if not stock:
        return go.Figure()

    df = yf.download(stock, start=start, end=end)

    df.reset_index(inplace=True)

    fig = px.line(
        df,
        x="Date",
        y=["Open", "Close"],
        title="Closing and Opening Price vs Date"
    )

    return fig


# INDICATOR GRAPH
@app.callback(
    Output("indicator-graph", "figure"),
    Input("indicator-btn", "n_clicks"),
    State("stock-input", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date")
)
def update_indicator(n_clicks, stock, start, end):

    if not stock:
        return go.Figure()

    df = yf.download(stock, start=start, end=end)

    df.reset_index(inplace=True)

    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    fig = px.line(
        df,
        x="Date",
        y=["Close", "EMA_20"],
        title="Exponential Moving Average"
    )

    return fig


# FORECAST GRAPH
@app.callback(
    Output("forecast-graph", "figure"),
    Input("forecast-btn", "n_clicks"),
    State("stock-input", "value"),
    State("days-input", "value")
)
def forecast(n_clicks, stock, days):

    if not stock or not days:
        return go.Figure()

    df, preds = predict_stock(stock, days)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        name="Actual"
    ))

    future_dates = pd.date_range(df.index[-1], periods=days+1)[1:]

    fig.add_trace(go.Scatter(
        x=future_dates,
        y=preds,
        mode="lines",
        name="Forecast"
    ))

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)