# 01_mtconnect_parser

This micro-project connects to a live MTConnect data stream and builds a real-time dashboard that:
- Parses and logs machine state data
- Plots live time-series charts of selected numeric signals (e.g., spindle speed, axis positions)
- Displays real-time status indicators for execution state, availability, and emergency stop
- Demonstrates how to combine MTConnect with Dash, Plotly, and pandas in a production-friendly Python workflow
As anything, it's a work in progress.

### Technologies
- Python 3.11
- MTConnect (simulated /current stream)
- Dash (UI), Plotly (charts), pandas (data structuring)
- Live polling with threading

### Run it
```bash
pip install -r requirements.txt
python dashboard.py
