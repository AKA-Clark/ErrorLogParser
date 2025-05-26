import re
import os


def checkNewLines(input_log_filepath: str, last_line: int) -> None:
    try:
        with open(input_log_filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {input_log_filepath} was not found.")
        return False, None, None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return False, None, None
    
    # if not log_lines:
    #     print("No lines found in the provided log content.")
    #     return
    # 1. Split the raw content string into a list of lines
    # Using splitlines(keepends=True) to preserve original line endings
    log_lines = lines
    log_lines_lenght = len(log_lines)

    # print("current log lines : ", log_lines_lenght)
    # print("last line : ", last_line)
    if log_lines_lenght > last_line:
        #  print(f"Log file has been updated. {log_lines_lenght - last_line} new lines found.")
         return True, lines, log_lines_lenght

    if last_line == log_lines_lenght or log_lines_lenght < last_line:
        # print("No log entries found in the provided content.")
        return False, None, None


def checkErrorLogFiles(path):
    
    # print(f"Checking folder: {path}")
    if not path.exists():
        print(f"Folder does not exist: {path}")
        return []
    
    # List all files in the folder
    all_files = [f.name for f in path.iterdir() if f.is_file()]
    pattern = re.compile(r"errors_\d{4}-\d{2}-\d{2}.log$")
    matching_files = sorted([f for f in all_files if pattern.match(f)],reverse=True)

    return matching_files
        


def getLatestFile(FOLDER_PATH):
    # Get all the error log files
    files = checkErrorLogFiles(FOLDER_PATH)

    # Get the first file name from the list
    LATEST_FILE_NAME = files[0]
    # print("Latest file name:", LATEST_FILE_NAME)
    LATEST_FILE_PATH = os.path.join(FOLDER_PATH, LATEST_FILE_NAME)

    # print("Latest file path:", LATEST_FILE_PATH)

    return LATEST_FILE_NAME, LATEST_FILE_PATH

