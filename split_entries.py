import re


# Assume log_splitter.py and log_parser.py are available in the same directory
# or a location included in sys.path.
# For demonstration, I'll include the necessary functions here.

# --- Start of log_splitter.py (from log_splitter_module_v3 immersive) ---
def split_entries(log_lines: list[str], start_line_number: int = 0) -> list[str]:
    """
    Splits a list of log lines into a list of individual log entry strings,
    starting from a specified line number.
    Each entry is identified by a specific starting pattern.

    Args:
        log_lines (list[str]): A list where each element is a string representing a single line
                               from the log file. Newline characters should ideally be present
                               at the end of each line if preserving original formatting is needed.
        start_line_number (int): The index of the line in log_lines to start processing from (0-based).
                                 Defaults to 0 (start from the beginning).

    Returns:
        list[str]: A list where each element is a string representing a single log entry.
                   Returns an empty list if the input list is empty, no entries are found
                   after the start_line_number, or start_line_number is out of bounds.
    """
    if not log_lines or start_line_number < 0 or start_line_number >= len(log_lines):
        # Return empty if input is empty, start_line_number is negative,
        # or start_line_number is beyond the list bounds.
        # print statements removed for cleaner output in this example script
        return []


    # Regex to identify the start of a new log entry
    # Example: 2025-01-01 00:41:25.7527 ERROR Guid ...
    # Using a non-greedy match for milliseconds (\.\d+?) and checking for " ERROR Guid"
    log_start_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ ERROR Guid")

    entries = []
    current_entry_lines = []

    # Iterate through the lines starting from the specified index
    for i in range(start_line_number, len(log_lines)):
        line = log_lines[i]
        # Check if the current line is the start of a new log entry
        if log_start_pattern.match(line):
            # If we have lines accumulated from the previous entry, process it
            if current_entry_lines:
                # Join the lines of the entry into a single string
                entries.append("".join(current_entry_lines))

            # Start accumulating lines for the new entry
            current_entry_lines = [line]
        else:
            # If it's not a log start line, append it to the current entry if one has started
            # This handles lines belonging to the first entry found after start_line_number
            if current_entry_lines:
                current_entry_lines.append(line)
            # else: ignore lines that appear before the first valid log entry starts
            # after the specified start_line_number.

    # After the loop, add the very last log entry if there are accumulated lines
    if current_entry_lines:
        entries.append("".join(current_entry_lines))

    return entries
# --- End of log_splitter.py ---

