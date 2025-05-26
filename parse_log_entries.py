
# --- Start of log_parser.py (Updated to extract UTC and accept server_name) ---
def parse_log_entry(log_entry_string: str, server_name: str = "") -> dict | None:
    """
    Parses a single log entry string and extracts specified fields.
    Includes placeholder fields for UTC Date and UTC Time, which cannot
    be reliably populated from the current log format without timezone info.

    Args:
        log_entry_string (str): A string containing the entire log entry,
                                with lines separated by newline characters.
        server_name (str): The name of the server to associate with this log entry.
                           Defaults to an empty string.

    Returns:
        dict | None: A dictionary containing the extracted log data, or None
                     if the entry doesn't match the expected starting pattern
                     (indicating it's not a valid error log entry).
    """
    # Initialize with default empty values, including new UTC fields and Server
    extracted_data = {
        "ServerDateTime": "", # Local server date and time
        "Date": "",         # Local server date
        "Time": "",         # Local server time
        "UTC Date": "",     # Extracted from log if present
        "UTC Time": "",     # Extracted from log if present
        "HTTPStatusCode": "",
        "ErrorCode": "", # Essential field to validate an entry
        "Controller": "",
        "Action": "",
        "URL": "",
        "RemoteHost": "",
        "User": "",
        "UserAgent": "",
        "StackTrace": "",
        "Host": "",
        "Referer": "",
        "Server": server_name # Add the Server field from the parameter
    }

    if not log_entry_string:
        return None # Cannot parse an empty string

    log_lines = log_entry_string.splitlines()

    if not log_lines:
        return None # No lines to parse

    # --- Initial Metadata Parsing (First 1-2 lines) ---
    # This is the most crucial part to identify a valid entry.
    # Example: 2025-01-01 00:41:25.7527 ERROR Guid 815af6c0-1ed2-412c-800b-80f86f9e28b3
    # Example: HTTP ERROR 500

    # Check and parse the first line
    if len(log_lines) > 0:
        line1_parts = log_lines[0].split()
        # Validate the core pattern of the first line for an ERROR entry
        if len(line1_parts) >= 5 and line1_parts[2] == "ERROR" and line1_parts[3] == "Guid":
            extracted_data["ServerDateTime"] = f"{line1_parts[0]} {line1_parts[1]}"
            extracted_data["Date"] = line1_parts[0]
            extracted_data["Time"] = line1_parts[1]
            extracted_data["ErrorCode"] = line1_parts[4]
        else:
            # If the first line doesn't match the expected ERROR start pattern,
            # this entry is likely not a relevant error log for this parser.
            return None # Indicate invalid entry

    # Check and parse the second line for HTTP Status Code
    if len(log_lines) > 1:
        line2_parts = log_lines[1].split()
        if len(line2_parts) == 3 and line2_parts[0] == "HTTP" and line2_parts[1] == "ERROR":
            extracted_data["HTTPStatusCode"] = line2_parts[2]
        # Note: If the second line doesn't match, we still proceed if the first line was valid.
        # HTTP status might not always be present in all error logs.

    # --- State Management for Stack Trace and Headers ---
    # This part is inherently stateful as we need to capture lines
    # between specific markers. While not purely functional, it's
    # contained within the processing of a single entry.
    stack_trace_lines = []
    capturing_stack_trace = False
    in_headers_section = False

    # Iterate through lines starting from the third line, as the first two are handled
    for line_content in log_lines[2:]:
        line_strip = line_content.strip()

        # --- State: Capturing Stack Trace ---
        if capturing_stack_trace:
            # Check for conditions to STOP capturing stack trace
            if line_strip == "Headers":
                capturing_stack_trace = False
                in_headers_section = True # Transition to Headers state
                continue # Do not include "Headers" line in stack trace
            elif line_strip.startswith("The template we tried to compile is"):
                 capturing_stack_trace = False # Stop capturing
                 continue # Do not include this line in stack trace
            else:
                # If not a stopping line, append it to the potential stack trace lines
                stack_trace_lines.append(line_strip)
            continue # Move to the next line

        # --- State: In Headers Section ---
        if in_headers_section:
            # Parse relevant headers
            if line_strip.startswith("Host:"):
                extracted_data["Host"] = line_strip.split(":", 1)[1].strip() if ":" in line_strip else ""
            elif line_strip.startswith("Referer:"):
                 extracted_data["Referer"] = line_strip.split(":", 1)[1].strip() if ":" in line_strip else ""
            # Ignore other headers
            continue # Move to the next line

        # --- State: Standard line parsing (before Exception, Headers, etc.) ---
        # These checks happen only if we are NOT currently capturing stack trace or in headers.

        # Check for START of Stack Trace. This line IS part of the stack trace.
        if line_strip.startswith("Exception:"):
             capturing_stack_trace = True
             stack_trace_lines = [line_strip] # Start capturing with this line
             continue # Move to the next line

        # --- Extract UTC Date and UTC Time if present ---
        if line_strip.startswith("UTC Date:") and not extracted_data["UTC Date"]:
            try:
                # Extract the part after "UTC Date:"
                utc_datetime_str = line_strip.split(":", 1)[1].strip()
                # Split the string into date and time parts
                parts = utc_datetime_str.split(maxsplit=2) # Split at most twice to handle date, time, and AM/PM
                if len(parts) >= 2:
                    extracted_data["UTC Date"] = parts[0] # First part is the date
                    # Join the rest of the parts for the time (handles HH:MM:SS and AM/PM)
                    extracted_data["UTC Time"] = " ".join(parts[1:])
                elif len(parts) == 1:
                     # If only date is present
                     extracted_data["UTC Date"] = parts[0]

            except Exception as e:
                # Handle potential parsing errors if the format is unexpected
                print(f"Warning: Could not parse UTC Date/Time from line '{line_strip}': {e}")
                extracted_data["UTC Date"] = line_strip.split(":", 1)[1].strip() # Fallback to extracting raw string


        # Parse other specific fields if not already set and not in a special section
        elif line_strip.startswith("Controller:") and not extracted_data["Controller"]:
             extracted_data["Controller"] = line_strip.split(":", 1)[1].strip()
        elif line_strip.startswith("Action:") and not extracted_data["Action"]:
             extracted_data["Action"] = line_strip.split(":", 1)[1].strip()
        elif line_strip.startswith("URL:") and not extracted_data["URL"]:
             extracted_data["URL"] = line_strip.split(":", 1)[1].strip()
        elif line_strip.startswith("Remote host:") and not extracted_data["RemoteHost"]:
             extracted_data["RemoteHost"] = line_strip.split(":", 1)[1].strip()
        elif line_strip.startswith("User:"): # Allow updating User if multiple occur (unlikely)
             parts = line_strip.split(":", 1)
             extracted_data["User"] = parts[1].strip() if len(parts) > 1 else ""
        elif line_strip.startswith("User agent:") and not extracted_data["UserAgent"]:
             extracted_data["UserAgent"] = line_strip.split(":", 1)[1].strip()

        # Any other lines not matched are ignored.

    # --- Post-processing Stack Trace ---
    # Filter out empty lines and lines that are just "---------------"
    actual_trace_lines = [
        l for l in stack_trace_lines
        if l.strip() # Remove purely empty or whitespace lines
        and l.strip() != "---------------" # Remove lines consisting only of hyphens
    ]

    if actual_trace_lines:
        # Join the filtered lines for the final StackTrace string
        extracted_data["StackTrace"] = "\n".join(actual_trace_lines)
    else:
        extracted_data["StackTrace"] = "" # Ensure it's an empty string if no trace was captured/remained

    # Return the dictionary containing the extracted data.
    # We don't filter by ErrorCode here; the caller will do that based on parse_log_entry returning None.
    return extracted_data
# --- End of log_parser.py ---