# 01_mtconnect_parser

**Project ammended from python to node-red for ease of use and encouragement of no more dashboard projects!**

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
- node-red

### Run it
install node-red, import the JSON and deploy. 

### Example output when connected to demo.mtconnect.org
<img width="1664" height="800" alt="Screenshot 2025-07-25 105244" src="https://github.com/user-attachments/assets/dfb81184-225d-43b2-9172-f69ad989893d" />
