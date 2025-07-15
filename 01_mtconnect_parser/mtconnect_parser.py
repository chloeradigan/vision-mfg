# Goal: Transform the MTConnect XML data into readable machine status information

import requests
import xml.etree.ElementTree as ET # Needed to parse XML
import pandas as pd
import time

# Define a function that accepts an MTConnect URL
def mtconnect_parser(url):
    # Get MTConnect XML stream
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to get data from MTConnect stream.")
        return None

    # Parse XML response into tree structure
    root = ET.fromstring(response.text)

    # Define the dataitems of interest
    dataitems_to_track = {
        "Spindle Speed": {
            "tag": "RotaryVelocity",
            "component": "Rotary",
            "name_hint": "Srpm"
        },
        "C Axis Angle": {
            "tag": "Angle",
            "component": "Rotary",
            "name_hint": "Cpos"
        },
        "X Position": {
            "tag": "Position",
            "component": "Linear",
            "name_hint": "Xpos"
        },
        "Y Position": {
            "tag": "Position",
            "component": "Linear",
            "name_hint": "Ypos"
        },
        "Z Position": {
            "tag": "Position",
            "component": "Linear",
            "name_hint": "Zpos"
        },
        "Execution State": {
            "tag": "Execution",
            "component": "Path"
        },
        "Availability": {
            "tag": "Availability",
            "component": "Device"
        },
        "Part Count": {
            "tag": "PartCount",
            "component": "Path"
        },
        "Tool Number": {
            "tag": "ToolNumber",
            "component": "Path"
        }
    }

    # Create dictionary to store values
    dataitem_status = {}

    # Extract timestamp from root tag
    timestamp = root.attrib.get("timestamp", "Unknown")
    dataitem_status["Timestamp"] = timestamp

    # Search for the relevant DataItems in the XML
    for component_stream in root.findall(".//ComponentStream"):
        for sample in component_stream.findall("./Samples/*"):
            data_item_id = sample.attrib.get("dataItemID", "Unknown")
            name = sample.tag.lower()
            value = sample.text

            # Match based on the desired items
            for label, tag_name in dataitems_to_find.items():
                if tag_name in name:
                    dataitem_status[label] = value
    
    # Fill missing values with "N/A"
    for label in dataitems_to_track:
        dataitem_status.setdefault(label, "N/A")
    return dataitem_status

    # Convert to DataFrame
    #df.pd.DataFrame([dataitem_status])
    #return df

# Main loop: Pull every few seconds
def run_stream_logger(url, interval_seconds=3, max_iterations=10):
    history = []

    print("Starting MTConnect stream logger...\n")

    for i in range(max_iterations):
        print(f"Pull #{i+1}")
    result = mtconnect_parser(url)
    if result:
        history.append(result)
        print(result)
    else:
        print("No data collected.")

    time.sleep(interval_seconds)

    # Convert final list of results to a DataFrame
    df = pd.DataFrame(history)

    # Save to CSV
    df.to_csv("machine_state_log.csv", index=False)
    print("\nSaved log to machine_state_log.csv")

if __name__ == "__main__":
    stream_url = "http://mtconnect.mazakcorp.com:5609/current"
    run_stream_logger(stream_url, interval_seconds=3, max_iterations=10)
