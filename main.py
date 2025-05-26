
import json
import os
from dotenv import load_dotenv
import datetime
from pathlib import Path
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
import schedule

from file_handling import checkNewLines, getLatestFile
from parse_log_entries import parse_log_entry
from split_entries import split_entries


def get_collection():
    """Helper to get the MongoDB collection."""
    global client
    try:
        db = client[DATABASE_NAME]
        return db[FILE_COLLECTION], client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None, None

def check_file(filename):
    """
    Checks if a file with the given filename exists in the FileInfo collection.
    Returns the document if it exists, otherwise None.
    """
    collection, client = get_collection()
    if collection is None:
        return None

    try:
        query = {"Filename": filename}
        document = collection.find_one(query)
        return document
    except Exception as e:
        print(f"Error checking file existence: {e}")
        return None


def update_file_info(filename, new_last_line_read=None, new_is_done=None, new_filepath=None):
    """
    Updates the information for a file based on its filename.
    Only updates the fields for which new values are provided.
    """
    collection, client = get_collection()
    if collection is None:
        return

    query = {"Filename": filename}
    update_fields = {}

    if new_last_line_read is not None:
        update_fields["Lastlineread"] = new_last_line_read
    if new_is_done is not None:
        update_fields["Isdone"] = new_is_done
    if new_filepath is not None:
        update_fields["Filepath"] = new_filepath
    # if new_filename is not None:
    #     update_fields["Filename"] = new_filename

    if not update_fields:
        print("No update fields provided.")
        return

    update_operation = {"$set": update_fields}

    try:
        result = collection.update_one(query, update_operation)
        if result.matched_count > 0:
            print(f"Successfully updated {result.modified_count} document(s) for Filename: {filename}")
        else:
            print(f"No document found with Filename: {filename} to update.")
    except Exception as e:
        print(f"Error updating document: {e}")


def insert_or_update_file_info(filename, filepath, last_line_read, is_done):
    """
    Inserts a new document if the filename doesn't exist, otherwise updates it.
    """
    collection, client = get_collection()
    if collection is None:
        return

    query = {"Filename": filename}
    new_values = {
        "Filename": filename,
        "Filepath": filepath,
        "Lastlineread": last_line_read,
        "Isdone": is_done
    }

    # The upsert=True option will insert the document if it doesn't exist.
    # If it exists, it will update it.
    try:
        result = collection.update_one(query, {"$set": new_values}, upsert=True)
        if result.upserted_id:
            print(f"Inserted new document with ID: {result.upserted_id} for Filename: {filename}")
        elif result.matched_count > 0:
            print(f"Updated existing document for Filename: {filename}. Modified count: {result.modified_count}")
        else:
            print(f"Operation completed for Filename: {filename}, but no changes were made (document already matched).")
    except Exception as e:
        print(f"Error inserting or updating document: {e}")



def main(log_lines, start_line_number):
    """
    Main function to demonstrate extracting specific log entries from a string.
    """
    #print("Simulating log processing from provided content...")
    
    # You can keep the output filename as is, or change it.
    
    # last_line = 874569 # 54
     #100
    log_lines_lenght = len(log_lines)
    output_json = []
    
    
        
    # 2. Use split_entries to get potential log entry strings
    # split_entries will identify entries starting with the ERROR Guid pattern
    # We start from line 0 to process the entire provided content
    potential_entries = split_entries(log_lines, start_line_number)

    last_line = log_lines_lenght
    if not potential_entries:
        print("No potential log entries found matching the start pattern.")
        return False, None, last_line, None

    #print(f"Identified {len(potential_entries)} potential log entries based on start pattern.")
    

    server_name = "US"

    # 3. Parse each potential entry and filter for valid ones
    # parse_log_entry will return None for entries that don't fully match the expected structure
    # (specifically, those not starting with ERROR Guid as per its logic, although split_entries
    # should have already filtered for the start pattern). We filter out None results.
    parsed_results = map(lambda entry_string: parse_log_entry(entry_string, server_name), potential_entries)
    valid_parsed_entries = list(filter(None, parsed_results))
    valid_parsed_entries_lenght = len(valid_parsed_entries)
    
    if not valid_parsed_entries:
        print("No valid log entries parsed after applying parsing logic.")
        return False, None, last_line, None 

    #print(f"Successfully parsed {len(valid_parsed_entries)} valid log entries.")

    # 4. Output the extracted data as JSON
    # print("\n--- Extracted Log Entries (JSON Output) ---")
    # print(json.dumps(valid_parsed_entries, indent=4, ensure_ascii=False))
    # print("-----------------------------------------")

    output_json = json.dumps(valid_parsed_entries, indent=4, ensure_ascii=False)

    return True, output_json, last_line, valid_parsed_entries_lenght



def main_program(FOLDER_PATH, MONGO, DATABASE_NAME, LOG_COLLECTION_NAME):

    global CURRENT_FILE_NAME
    # clear = lambda: os.system('cls')
    # clear()

    # Get the latest file name and path
    LATEST_FILE_NAME, LATEST_FILE_PATH = getLatestFile(FOLDER_PATH)


    new_entries = 0
    last_line = 0
    
    #print("Comparing current file name with latest file name...")
    # print("Current file name:", CURRENT_FILE_NAME)
    # print("Latest file name:", LATEST_FILE_NAME)

    haveLatest = check_file(LATEST_FILE_NAME)
    if CURRENT_FILE_NAME != LATEST_FILE_NAME:
        if haveLatest and CURRENT_FILE_NAME == None:
            # If the file already exists in the database, get its last line
            CURRENT_FILE_NAME = LATEST_FILE_NAME
        elif haveLatest and CURRENT_FILE_NAME != None:
            # If the file already exists in the database, get its last line
            update_file_info(CURRENT_FILE_NAME, new_is_done=True)
            CURRENT_FILE_NAME = LATEST_FILE_NAME
            last_line = 0
            insert_or_update_file_info(LATEST_FILE_NAME, LATEST_FILE_PATH, last_line, False)

        elif not haveLatest and CURRENT_FILE_NAME == None:
            # If the file doesn't exist in the database, insert it with last line 0, update the current file to Done reading( this means that a new file is created/ a new day has started)
            #update_file_info(CURRENT_FILE_NAME, new_is_done=True)
            CURRENT_FILE_NAME = LATEST_FILE_NAME
            last_line = 0
            insert_or_update_file_info(LATEST_FILE_NAME, LATEST_FILE_PATH, last_line, False)   
        elif not haveLatest and CURRENT_FILE_NAME != None:
            # If the file already exists in the database, get its last line
            update_file_info(CURRENT_FILE_NAME, new_is_done=True)
            CURRENT_FILE_NAME = LATEST_FILE_NAME
            last_line = 0
            insert_or_update_file_info(LATEST_FILE_NAME, LATEST_FILE_PATH, last_line, False)    
        

    #print("Getting last line from the database...")
    #output_json_filepath = "parsed_log_output_2.json"
    #print("Latest file name:", CURRENT_FILE_NAME)
    if CURRENT_FILE_NAME == LATEST_FILE_NAME:
        if not check_file(CURRENT_FILE_NAME):
            # If the file doesn't exist in the database, insert it with last line 0
            last_line = 0
            insert_or_update_file_info(CURRENT_FILE_NAME, LATEST_FILE_PATH, last_line, False)
            print("File not found in the database. Inserting new file info.")

    FILE = check_file(CURRENT_FILE_NAME)
    # print("File info from the database:", FILE)
    last_line = int(FILE["Lastlineread"])
    # print("Last line read from the database:", last_line)
    # Check if new lines have been added to the log file
    haveNewLines, lines, lines_lenght = checkNewLines(LATEST_FILE_PATH, last_line)

    # Parse the log file if new lines are found
    if haveNewLines:
        Valid, output_json, last_line, new_entries = main(lines, last_line)
        if Valid: 
            client = MongoClient(MONGO)
            db = client[DATABASE_NAME]
            LOG_COLLECTION = db[LOG_COLLECTION_NAME]

            #print("output_json: ", output_json)
            result = LOG_COLLECTION.insert_many(json.loads(output_json))
            #print("Inserted document IDs:", result.inserted_ids)
        update_file_info(CURRENT_FILE_NAME, new_last_line_read=last_line)

        # output_json, last_line = main(lines, start_line)
    now = datetime.now()
    print(now, LATEST_FILE_PATH, "\t| Have New Lines: ", haveNewLines , "\t| last line: ", last_line,"\t| new entries: ", new_entries)
  # Sleep for 5 seconds before checking again



if __name__ == '__main__':

    # def schedule_main_program():
    #     threading.Thread(target=main_program, args=(FOLDER_PATH, MONGO, DATABASE_NAME, LOG_COLLECTION_NAME), daemon=True).start()

    

    load_dotenv()  # <-- THIS MUST BE FIRST THING

    FOLDER_PATH = Path(os.getenv("FOLDER_PATH"))
    MONGO = str(os.getenv("MONGO"))
    client = MongoClient(MONGO)

    DATABASE_NAME = 'LogParser'
    FILE_COLLECTION = 'FileInfo'
    LOG_COLLECTION_NAME = "LogEntries"

    CURRENT_FILE_NAME = None

    if not FOLDER_PATH.is_dir():
        print(f"Invalid folder path: {FOLDER_PATH}")
        exit(1)

    print(f"FOLDER_PATH: {FOLDER_PATH}")
    print(f"MONGO: {MONGO}")
    # Initial main program call
    print("Starting log file monitoring...")
    main_program(FOLDER_PATH, MONGO, DATABASE_NAME, LOG_COLLECTION_NAME)
    print("Initial main program call completed.")
    

    schedule.every(15).seconds.do(lambda: main_program(FOLDER_PATH, MONGO, DATABASE_NAME, LOG_COLLECTION_NAME))
    #print(f"Scheduled jobs: {schedule.jobs}")
    while True:
        schedule.run_pending()
        time.sleep(1)
