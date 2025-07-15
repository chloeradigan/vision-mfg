# Goal: Create a Dash app with live dropdowns + plot that pulls and maps mtconnect data from the live datastream

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import time
from mtconnect_parser import mtconnect_parser
import threading

# Configure
URL = "http://mtconnect.mazakcorp.com:5609/current"
POLL_INTERVAL = 3 #seconds

# Global Dataframe
df = pd.DataFrame()

# Polling thread to update dataframe
def poll_data():
    global df
    while True:
        new_data = mtconnect_parser(URL)
        if new_data:
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        time.sleep(POLL_INTERVAL)

# Start polling thread
thread = threading.Thread(target=poll_data, daemon=True)
thread.start()

# Dash App
app = Dash(__name__)
app.title = "Machine Status Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Live MTConnect Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.Div(id="execution-state", className="status-box"),
        html.Div(id="availability", className="status-box"),
        html.Div(id="emergency-stop", className="status-box"),
    ], style={"display": "flex", "justifyContent": "center", "gap": "20px"}),

    html.Br(),

    html.Div([
        html.Label("Select signal:"),
        dcc.Dropdown(
            id="signal-dropdown",
            options=[
                {"label": "Spindle Speed", "value": "Spindle Speed"},
                {"label": "X Position", "value": "X Position"},
                {"label": "Y Position", "value": "Y Position"},
                {"label": "Z Position", "value": "Z Position"},
                {"label": "Part Count", "value": "Part Count"},
                {"label": "Tool Number", "value": "Tool Number"}
            ],
            value="Spindle Speed"
        ),
    ], style={"width": "300px", "margin": "auto"}),

    dcc.Graph(id="live-plot"),
    dcc.Interval(id="update-interval", interval=5000, n_intervals=0)
])


# Callbacks
@app.callback(
    Output("live-plot", "figure"),
    Input("update-interval", "n_intervals"),
    Input("signal-dropdown", "value")
)
def update_graph(n, selected_signal):
    global df
    if df.empty or selected_signal not in df.columns:
        return go.Figure()

    # Parse timestamp column with expected format
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce")

    # Drop rows with missing timestamps or bad signal values
    clean_df = df.copy()
    clean_df = clean_df.dropna(subset=["Timestamp", selected_signal])
    clean_df = clean_df[clean_df[selected_signal] != "UNAVAILABLE"]

    # Try to convert the signal column to numeric
    try:
        clean_df[selected_signal] = pd.to_numeric(clean_df[selected_signal], errors="coerce")
        clean_df = clean_df.dropna(subset=[selected_signal])
    except:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=clean_df["Timestamp"],
        y=clean_df[selected_signal],
        mode="lines+markers",
        name=selected_signal
    ))
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=selected_signal,
        template="plotly_white",
        height=500
    )
    return fig
# Callback for status panel
@app.callback(
    Output("execution-state", "children"),
    Output("availability", "children"),
    Output("emergency-stop", "children"),
    Input("update-interval", "n_intervals")
)
def update_status_panels(n):
    global df
    if df.empty:
        return "Execution: --", "Availability: --", "E-Stop: --"

    latest = df.iloc[-1]

    return (
        f"Execution: {latest.get('Execution State', '--')}",
        f"Availability: {latest.get('Availability', '--')}",
        f"E-Stop: {latest.get('Emergency Stop', '--')}"
    )

# Run server
if __name__ == "__main__":
    app.run(debug=True)
