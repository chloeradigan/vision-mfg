import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time

# Define the MTConnect Streams namespace
# Key point: The 'm' prefix maps to the default namespace URI.
# ElementTree requires us to map prefixes even for the default namespace
# if we want to use findall with prefixes.
MTCONNECT_STREAMS_NAMESPACE = {'m': 'urn:mtconnect.org:MTConnectStreams:2.5'}

# Discover available dataitems
def discover_dataitems(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch MTConnect stream for discovery. Status code: {response.status_code}")
        return {}, {}

    root = ET.fromstring(response.text)

    print("\n=== DEBUG: Raw XML Structure (first 500 chars) ===")
    print(response.text[:500])
    print("===================================================")

    # Check for the root tag with namespace for initial confirmation
    print(f"DEBUG: Root tag is: {root.tag}")
    if not root.tag.startswith("{urn:mtconnect.org:MTConnectStreams"):
        print("WARNING: Root tag does not match expected MTConnectStreams namespace. Parsing might fail.")


    numeric_signals = {}
    status_signals = {}

    # Correctly navigate through MTConnect XML for DataItems, using the namespace
    # We use the 'm:' prefix defined in MTCONNECT_STREAMS_NAMESPACE
    # Path: MTConnectStreams -> DeviceStream -> ComponentStream -> Samples/Events/Condition -> DataItem (e.g., Temperature, PathFeedrate)
    # The crucial part: Ensure the paths correctly reflect how elements appear in the XML.
    # If DeviceStream is directly under the root and is NOT prefixed in the XML,
    # then you should use './{namespace_uri}DeviceStream' or register an empty prefix.
    # However, by defining 'm' to be the default namespace, ElementTree will handle it.

    # Let's try iterating through all DeviceStream elements directly under the root,
    # but ensure findall respects the namespace.
    # The default namespace is applied to all *unprefixed* elements in the XML.
    # So, if DeviceStream is <DeviceStream> (no prefix) in the XML, it belongs to the default namespace.

    # Revised approach for findall - using the registered namespace prefix 'm'
    # which points to the *default* namespace for unprefixed elements like DeviceStream.
    for device_stream in root.findall("m:Streams/m:DeviceStream", MTCONNECT_STREAMS_NAMESPACE): # MTConnectStreams is the root, then Streams, then DeviceStream
        device_name = device_stream.attrib.get("name", "UnknownDevice")
        device_uuid = device_stream.attrib.get("uuid", "UnknownUUID")

        print(f"DEBUG: Found DeviceStream: {device_name}")

        for component_stream in device_stream.findall("m:ComponentStream", MTCONNECT_STREAMS_NAMESPACE):
            component_name = component_stream.attrib.get("name", "UnknownComponent")
            component_id = component_stream.attrib.get("componentId", "UnknownComponentId")
            component_type = component_stream.attrib.get("component", "UnknownType")

            print(f"  DEBUG: Found ComponentStream: {component_name} (Type: {component_type})")

            for data_set_type_tag in ["m:Samples", "m:Events", "m:Condition"]: # Apply namespace to section tags
                # This finds direct children of Samples/Events/Condition
                for data_item_element in component_stream.findall(f"./{data_set_type_tag}/*", MTCONNECT_STREAMS_NAMESPACE):
                    name_attrib = data_item_element.attrib.get("name")
                    data_item_id = data_item_element.attrib.get("dataItemId")
                    type_attribute = data_item_element.attrib.get("type")

                    signal_name = name_attrib or data_item_id or type_attribute or ET.QName(data_item_element.tag).localname

                    label = f"{signal_name.replace('_', ' ').title()} ({component_name} - {device_name})"
                    value = data_item_element.text

                    # print(f"    DEBUG: Found DataItem - Tag: {ET.QName(data_item_element.tag).localname}, Name: {signal_name}, Value: '{value}'")


                    if not value or value.upper() == "UNAVAILABLE":
                        # print(f"      Skipping unavailable or empty value for {label}")
                        continue

                    val = value.strip()
                    try:
                        float(val)
                        if label not in numeric_signals:
                            numeric_signals[label] = signal_name
                    except ValueError:
                        if label not in status_signals:
                            status_signals[label] = signal_name

    print(f"\nDiscovered {len(numeric_signals)} numeric and {len(status_signals)} status signals.")

    print("\n=== Discovered Numeric Signals ===")
    for label, name in numeric_signals.items():
        print(f"  - {label} (Internal Name: {name})")

    print("\n=== Discovered Status Signals ===")
    for label, name in status_signals.items():
        print(f"  - {label} (Internal Name: {name})")

    return numeric_signals, status_signals


# The rest of your code (select_dataitems_to_track, mtconnect_parser, run_stream_logger, __main__)
# The mtconnect_parser also needs to reflect the corrected paths if they are different from what was previously assumed.

# Parse a single MTConnect snapshot
def mtconnect_parser(url, selected_items):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to get data from MTConnect stream. Status code: {response.status_code}")
        return None

    root = ET.fromstring(response.text)
    dataitem_status = {"Timestamp": root.attrib.get("timestamp", "Unknown")}

    # Apply namespace to findall calls here as well
    for device_stream in root.findall("m:Streams/m:DeviceStream", MTCONNECT_STREAMS_NAMESPACE):
        for component_stream in device_stream.findall("m:ComponentStream", MTCONNECT_STREAMS_NAMESPACE):
            for section_tag in ["m:Samples", "m:Events"]:
                for data_item_element in component_stream.findall(f"./{section_tag}/*", MTCONNECT_STREAMS_NAMESPACE):
                    name_attrib = data_item_element.attrib.get("name")
                    data_item_id = data_item_element.attrib.get("dataItemId")
                    type_attribute = data_item_element.attrib.get("type")

                    current_signal_name = name_attrib or data_item_id or type_attribute or ET.QName(data_item_element.tag).localname
                    value = data_item_element.text

                    if not value or value.upper() == "UNAVAILABLE":
                        continue

                    for label, config in selected_items.items():
                        if config["name"] == current_signal_name:
                            dataitem_status[label] = value
                            break

    for label in selected_items:
        dataitem_status.setdefault(label, "N/A")

    return dataitem_status

# The other functions (select_dataitems_to_track, run_stream_logger, __main__) are assumed to be correct
# from the previous version and don't need changes related to XML parsing.
# Paste them here if you want a complete runnable block.

# Let user choose dataitems to track
def select_dataitems_to_track(numeric, status):
    print("\n=== Available Numeric Signals ===")
    numeric_keys = list(numeric.keys())
    for i, label in enumerate(numeric_keys):
        print(f"{i + 1}: {label}")

    print("\n=== Available Status Signals ===")
    status_keys = list(status.keys())
    offset = len(numeric_keys)
    for i, label in enumerate(status_keys):
        print(f"{offset + i + 1}: {label}")

    selected_indices_input = input("\nEnter numbers of signals to track (comma-separated), or 'all' to select all: ")

    if selected_indices_input.lower() == 'all':
        selected_items = {}
        for label, name in numeric.items():
            selected_items[label] = {"name": name}
        for label, name in status.items():
            selected_items[label] = {"name": name}
        print(f"Selected all {len(selected_items)} available signals.")
        return selected_items

    selected_indices = [int(x.strip()) - 1 for x in selected_indices_input.split(",") if x.strip().isdigit()]

    selected_items = {}
    for i in selected_indices:
        if 0 <= i < len(numeric_keys):
            label = numeric_keys[i]
            selected_items[label] = {"name": numeric[label]}
        elif len(numeric_keys) <= i < len(numeric_keys) + len(status_keys):
            label = status_keys[i - len(numeric_keys)]
            selected_items[label] = {"name": status[label]}
        else:
            print(f"Warning: Invalid selection index {i+1} ignored.")
    return selected_items


# Run live logger
def run_stream_logger(url, selected_items, interval_seconds=3, max_iterations=10):
    history = []
    print("\nStarting MTConnect stream logger...\n")

    # Get column names from selected_items for consistent DataFrame columns
    column_names = ["Timestamp"] + list(selected_items.keys())

    for i in range(max_iterations):
        print(f"Pull #{i + 1}")
        result = mtconnect_parser(url, selected_items)
        if result:
            # Ensure the order of columns in the result dictionary matches column_names
            ordered_result = {col: result.get(col, "N/A") for col in column_names}
            history.append(ordered_result)
            print(ordered_result)
        else:
            print("No data collected for this pull.")
        time.sleep(interval_seconds)

    if history:
        df = pd.DataFrame(history)
        df.to_csv("machine_state_log.csv", index=False)
        print("\nSaved log to machine_state_log.csv")
    else:
        print("\nNo data to save.")


# MAIN
if __name__ == "__main__":
    stream_url = "https://demo.mtconnect.org/current"
    print(f"Attempting to discover data items from: {stream_url}")
    numeric, status = discover_dataitems(stream_url)

    if not numeric and not status:
        print("No usable dataitems found after discovery.")
    else:
        selected = select_dataitems_to_track(numeric, status)
        if not selected:
            print("No dataitems selected. Exiting.")
        else:
            run_stream_logger(stream_url, selected, interval_seconds=3, max_iterations=10)
