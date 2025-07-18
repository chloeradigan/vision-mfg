# dashboard.py

from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import time
import threading
import sys # For graceful shutdown

# Import your mtconnect_parser functions
# Make sure mtconnect_parser.py is in the same directory or accessible in your Python path
try:
    from mtconnect_parser import mtconnect_parser, discover_dataitems
    print("Successfully imported mtconnect_parser functions.")
except ImportError:
    print("Error: Could not import mtconnect_parser.py. "
          "Make sure it's in the same directory and its functions are correctly defined.")
    sys.exit(1) # Exit if essential functions can't be imported


# --- Configuration ---
URL = "https://demo.mtconnect.org/current"
POLL_INTERVAL = 3  # seconds: How often the data polling thread fetches new data
UPDATE_INTERVAL_DASH = 5000 # milliseconds: How often Dash callbacks refresh the UI


# --- Global Data Structures and Control Flags ---
# Lock for thread-safe access to the global DataFrame
df_lock = threading.Lock()
df = pd.DataFrame() # Global DataFrame to store collected data

# Thread management variables
polling_thread = None # To hold the polling thread object
stop_polling_event = threading.Event() # Event to signal the polling thread to stop

# This dictionary stores the actual data items being actively polled by the thread.
# Its keys are the user-friendly labels, and values are {"name": "internal_mtconnect_name"}.
selected_items_for_polling = {}

# These store all available signals found during initial discovery.
# They are used to populate dropdowns and look up internal names.
# ALL_NUMERICAL_SIGNALS and ALL_STATUS_SIGNALS store {label: internal_name}
ALL_NUMERICAL_SIGNALS = {}
ALL_STATUS_SIGNALS = {}
# ALL_AVAILABLE_SIGNALS_MAPPED stores {label: {"name": internal_name}}, for consistent lookup
ALL_AVAILABLE_SIGNALS_MAPPED = {}


# --- Initial Data Discovery (Run once at app startup) ---
# This discovers all possible data items to present to the user for selection.
# It does NOT start polling or populate the main DataFrame yet.
print("Performing initial discovery of all available MTConnect data items...")
raw_numerical, raw_status = discover_dataitems(URL) # Returns {label: name}

# Populate the global dictionaries
ALL_NUMERICAL_SIGNALS.update(raw_numerical)
ALL_STATUS_SIGNALS.update(raw_status)

# Create the mapped dictionary used for selection and lookup
for label, name in raw_numerical.items():
    ALL_AVAILABLE_SIGNALS_MAPPED[label] = {"name": name}
for label, name in raw_status.items():
    ALL_AVAILABLE_SIGNALS_MAPPED[label] = {"name": name}

if not ALL_AVAILABLE_SIGNALS_MAPPED:
    print("WARNING: No usable data items found during initial discovery. Dashboard selection will be empty.")
else:
    print(f"Discovered {len(ALL_AVAILABLE_SIGNALS_MAPPED)} total data items for selection.")


# --- Polling Thread Function ---
def poll_data_loop():
    """
    This function runs in a separate thread, continuously polling MTConnect data.
    It updates the global 'df' DataFrame.
    """
    global df
    print(f"Polling thread started for URL: {URL}")
    while not stop_polling_event.is_set(): # Loop until the stop event is set
        try:
            # Get a copy of the currently selected items for this poll cycle
            current_selected_items = {}
            with df_lock: # Safely read selected_items_for_polling
                current_selected_items = selected_items_for_polling.copy()

            if not current_selected_items:
                # If no items are selected, wait and continue
                time.sleep(POLL_INTERVAL)
                continue

            # Fetch new data from MTConnect agent
            new_data = mtconnect_parser(URL, current_selected_items)

            if new_data:
                with df_lock: # Acquire lock before modifying df
                    # Ensure new_data dictionary has all expected columns (labels of selected items)
                    # This prevents missing columns if a signal is temporarily unavailable
                    ordered_new_data = {col: new_data.get(col, "N/A")
                                        for col in ["Timestamp"] + list(current_selected_items.keys())}
                    df = pd.concat([df, pd.DataFrame([ordered_new_data])], ignore_index=True)

                    # Keep the DataFrame from growing too large (e.g., last 1000 records)
                    if len(df) > 1000:
                        df = df.iloc[-1000:].copy()
                        df.reset_index(drop=True, inplace=True)
            # else:
            #     print("Polling: No data collected in this poll (or mtconnect_parser returned None).")
        except Exception as e:
            print(f"Polling Error: {e}")
        time.sleep(POLL_INTERVAL)
    print("Polling thread stopped.")


# --- Dash App Initialization ---
app = Dash(__name__)
app.title = "Dynamic Machine Status Dashboard"

# --- Dash App Layout ---
app.layout = html.Div([
    html.H1("Live MTConnect Dashboard", style={"textAlign": "center", "color": "#2c3e50"}),

    # Panel for signal selection and polling control
    html.Div([
        html.Label("Select Signals to Track:", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block', 'color': '#34495e'}),
        dcc.Dropdown(
            id="signal-selection-dropdown",
            options=[{"label": label, "value": label} for label in ALL_AVAILABLE_SIGNALS_MAPPED.keys()],
            multi=True, # Allow multiple selections
            placeholder="Select one or more signals...",
            style={'width': '100%'}
        ),
        html.Button('Start/Restart Polling', id='start-polling-button', n_clicks=0,
                    style={
                        'marginTop': '15px', 'backgroundColor': '#3498db', 'color': 'white',
                        'border': 'none', 'padding': '12px 25px', 'borderRadius': '5px',
                        'cursor': 'pointer', 'fontSize': '16px', 'fontWeight': 'bold',
                        'transition': 'background-color 0.3s ease'
                    }),
    ], style={"width": "60%", "maxWidth": "800px", "margin": "30px auto", "padding": "25px",
              "border": "1px solid #e0e0e0", "borderRadius": "10px", "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
              "backgroundColor": "#ffffff"}),

    html.Hr(style={'marginTop': '40px', 'marginBottom': '40px', 'borderTop': '1px solid #e0e0e0'}),

    # Status boxes for specific, commonly available signals
    html.H2("Current Machine Status", style={"textAlign": "center", "marginTop": "20px", "color": "#2c3e50"}),
    html.Div([
        html.Div(id="execution-state", className="status-box", children="Execution: --"),
        html.Div(id="availability", className="status-box", children="Availability: --"),
        html.Div(id="emergency-stop", className="status-box", children="E-Stop: --"),
    ], style={"display": "flex", "justifyContent": "center", "gap": "25px", "marginBottom": "40px"}),

    # Panel for plotting selected signals
    html.H2("Live Signal Plot", style={"textAlign": "center", "marginTop": "20px", "color": "#2c3e50"}),
    html.Div([
        html.Label("Select Signal to Plot:", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block', 'color': '#34495e'}),
        dcc.Dropdown(
            id="plot-signal-dropdown",
            options=[], # Will be updated dynamically based on user's selection
            placeholder="Select a signal to plot...",
            clearable=False,
            style={'width': '100%'}
        ),
    ], style={"width": "60%", "maxWidth": "800px", "margin": "20px auto", "padding": "25px",
              "border": "1px solid #e0e0e0", "borderRadius": "10px", "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
              "backgroundColor": "#ffffff"}),

    dcc.Graph(id="live-plot"),
    dcc.Interval(id="update-interval", interval=UPDATE_INTERVAL_DASH, n_intervals=0) # Controls UI refresh rate
], style={"fontFamily": "Arial, sans-serif", "padding": "30px", "backgroundColor": "#f0f2f5"}) # Changed body background

# Custom HTML template for the Dash app (correctly includes all lowercase placeholders)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%css%}
        <style>
            body {
                background-color: #f0f2f5; /* Light background */
                margin: 0;
                padding: 0;
            }
            .status-box {
                border: 1px solid #ced4da; /* Light grey border */
                padding: 15px 20px;
                border-radius: 8px;
                background-color: #ffffff; /* White background */
                font-weight: bold;
                color: #495057; /* Darker text */
                min-width: 200px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); /* Soft shadow */
                font-size: 1.1em;
            }
            .status-box:hover {
                box-shadow: 0 4px 10px rgba(0,0,0,0.15); /* Slightly more prominent on hover */
            }
            #start-polling-button:hover {
                background-color: #2980b9 !important; /* Darker blue on hover */
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# --- Dash Callbacks ---

# Callback to manage the polling thread and update the plot selection dropdown
@app.callback(
    Output('plot-signal-dropdown', 'options'), # Update plot dropdown options
    Output('plot-signal-dropdown', 'value'),   # Set default value for plot dropdown
    Input('start-polling-button', 'n_clicks'),
    State('signal-selection-dropdown', 'value'), # Get the list of selected labels from the user
    prevent_initial_call=False # This allows the callback to run on initial page load to set up dropdowns
)
def manage_polling_and_update_plot_dropdown(n_clicks, selected_labels_from_ui):
    global polling_thread, stop_polling_event, selected_items_for_polling, df

    # Check which input triggered the callback
    triggered_id = callback_context.triggered_id if callback_context.triggered_id else 'initial_load'

    if triggered_id == 'start-polling-button' and n_clicks > 0:
        print(f"User clicked 'Start/Restart Polling'. Selected labels: {selected_labels_from_ui}")

        # 1. Stop any existing polling thread gracefully
        if polling_thread and polling_thread.is_alive():
            print("Stopping existing polling thread...")
            stop_polling_event.set() # Signal the thread to stop
            # Wait for thread to finish (with a timeout slightly longer than POLL_INTERVAL)
            polling_thread.join(timeout=POLL_INTERVAL + 2)
            if polling_thread.is_alive():
                print("Warning: Polling thread did not stop gracefully. It might still be running in background.")
            stop_polling_event.clear() # Clear the event for a potential new thread

        # 2. Clear the global DataFrame for fresh data
        with df_lock:
            df = pd.DataFrame()

        # 3. Update the global 'selected_items_for_polling' based on user's selection
        # This is the map {label: {"name": internal_name}} that the polling thread will use
        newly_selected_items_map = {}
        if selected_labels_from_ui: # Ensure selected_labels_from_ui is not None or empty
            for label in selected_labels_from_ui:
                if label in ALL_AVAILABLE_SIGNALS_MAPPED:
                    newly_selected_items_map[label] = ALL_AVAILABLE_SIGNALS_MAPPED[label] # Get the {"name": ...} dict

        with df_lock: # Safely update the shared variable
            selected_items_for_polling = newly_selected_items_map.copy()

        # 4. Start a new polling thread if items are selected
        if selected_items_for_polling:
            print(f"Starting new polling thread for {len(selected_items_for_polling)} selected items.")
            polling_thread = threading.Thread(target=poll_data_loop, daemon=True)
            polling_thread.start()
        else:
            print("No signals selected. Polling thread not started.")

    # 5. Always update the plot-signal-dropdown options and default value
    plot_options = []
    plot_default_value = None

    if selected_labels_from_ui:
        # Filter the user's selected labels to find only the numeric ones for plotting
        numeric_selected_labels = [
            lbl for lbl in selected_labels_from_ui
            if lbl in ALL_NUMERICAL_SIGNALS # Check if the label corresponds to a numeric signal
        ]
        plot_options = [{"label": label, "value": label} for label in numeric_selected_labels]

        if numeric_selected_labels:
            plot_default_value = numeric_selected_labels[0] # Set default to the first numeric selected signal

    return plot_options, plot_default_value


# Callback for the live plot
@app.callback(
    Output("live-plot", "figure"),
    Input("update-interval", "n_intervals"),
    Input("plot-signal-dropdown", "value") # Input from the dropdown selecting what to plot
)
def update_graph(n_intervals, selected_label_to_plot):
    with df_lock: # Acquire lock before reading the global DataFrame
        local_df = df.copy() # Work on a copy to release the lock quickly

    # Handle initial state or no selection
    if local_df.empty or not selected_label_to_plot or selected_label_to_plot not in local_df.columns:
        return go.Figure(layout=go.Layout(title="Select signals and click 'Start Polling'"))

    # --- Data Cleaning and Preparation for Plotting ---
    # Convert 'Timestamp' column to datetime objects with explicit format
    # THIS IS THE KEY FIX FOR THE USER WARNINGS
    local_df["Timestamp"] = pd.to_datetime(local_df["Timestamp"], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce")

    # Drop rows where Timestamp or the selected signal's value is missing/unavailable
    clean_df = local_df.dropna(subset=["Timestamp", selected_label_to_plot])
    clean_df = clean_df[clean_df[selected_label_to_plot] != "UNAVAILABLE"]

    # Try to convert the selected signal column to numeric
    try:
        clean_df[selected_label_to_plot] = pd.to_numeric(clean_df[selected_label_to_plot], errors="coerce")
        clean_df = clean_df.dropna(subset=[selected_label_to_plot]) # Drop rows where conversion resulted in NaN
    except Exception as e:
        print(f"Error converting '{selected_label_to_plot}' to numeric: {e}")
        return go.Figure(layout=go.Layout(title=f"Error: Could not plot {selected_label_to_plot}. Is it a numeric signal?"))

    # Return empty figure if no valid numeric data remains
    if clean_df.empty:
        return go.Figure(layout=go.Layout(title=f"No valid numeric data for {selected_label_to_plot} to plot yet."))

    # Create the plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=clean_df["Timestamp"],
        y=clean_df[selected_label_to_plot],
        mode="lines+markers",
        name=selected_label_to_plot,
        line=dict(color='#2ecc71', width=2), # Green line
        marker=dict(size=6, color='#27ae60', line=dict(width=1, color='#ffffff'))
    ))
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=selected_label_to_plot,
        template="plotly_white",
        height=500,
        title=f"Live Data for {selected_label_to_plot}",
        hovermode="x unified",
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis_showgrid=True, yaxis_showgrid=True,
        xaxis_gridcolor='#e0e0e0', yaxis_gridcolor='#e0e0e0',
    )
    return fig

# Callback for the status panels
@app.callback(
    Output("execution-state", "children"),
    Output("availability", "children"),
    Output("emergency-stop", "children"),
    Input("update-interval", "n_intervals")
)
def update_status_panels(n_intervals):
    with df_lock: # Acquire lock before reading the global DataFrame
        if df.empty:
            return "Execution: --", "Availability: --", "E-Stop: --"
        latest = df.iloc[-1] # Get the very last row (most recent data)

    # Dynamically find the correct 'label' for each specific status signal
    # We iterate through ALL_AVAILABLE_SIGNALS_MAPPED to find the labels whose
    # internal 'name' attribute contains "execution", "availability", or "estop".
    # This is more robust than hardcoding labels like "Execution State (Controller - Tlfdn1)".
    execution_label = next(
        (lbl for lbl, cfg in ALL_AVAILABLE_SIGNALS_MAPPED.items() if 'execution' in cfg['name'].lower()), None
    )
    availability_label = next(
        (lbl for lbl, cfg in ALL_AVAILABLE_SIGNALS_MAPPED.items() if 'availability' in cfg['name'].lower()), None
    )
    emergency_stop_label = next(
        (lbl for lbl, cfg in ALL_AVAILABLE_SIGNALS_MAPPED.items()
         if 'estop' in cfg['name'].lower() or 'emergency_stop' in cfg['name'].lower()), None
    )

    # Retrieve values using the found labels. Use .get() with a default for safety.
    execution_val = latest.get(execution_label, '--') if execution_label else '--'
    availability_val = latest.get(availability_label, '--') if availability_label else '--'
    emergency_stop_val = latest.get(emergency_stop_label, '--') if emergency_stop_label else '--'

    return (
        f"Execution: {execution_val}",
        f"Availability: {availability_val}",
        f"E-Stop: {emergency_stop_val}"
    )

# --- Run the Dash Server ---
if __name__ == "__main__":
    # app.run() is the current method. host='0.0.0.0' allows external access.
    # debug=True provides a development server with hot-reloading and browser debugging.
    app.run(debug=True, host='0.0.0.0', port=8050)
