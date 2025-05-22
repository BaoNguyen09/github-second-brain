# Synchronous usage
import os, sys, subprocess
from subprocess import CompletedProcess
import json

OUTPUT_DIR = "data"
json_file_path = os.path.join("data", "processed_repos.json")

def process_url(repo_url: str):
    """
    Processes a GitHub repo URL into a filename using all the path
    components in the url connected by a hyphen
    """
    path = repo_url[19:] # exclude the part: https://github.com/
    filename = "-".join(path.split("/")) + ".txt"
    return filename

def write_to_file(result: CompletedProcess[str], output_path: str):
    # --- Extract and Append Summary ---
    stdout_content = result.stdout
    summary_marker = "Repository:"
    # Find the starting position of "Repository:"
    summary_start_index = stdout_content.find(summary_marker)

    if summary_start_index != -1:
        # Extract the text from "Repository:" to the end
        summary_block = stdout_content[summary_start_index:]
        summary_block = summary_block.strip() # Remove leading/trailing whitespace

        print(f"Found summary in stdout. Appending to {output_path}...")
        try: 
            # Append summary to end of file
            with open(output_path, "a", encoding='utf-8') as file:
                file.write("--- Summary ---\n")
                file.write(summary_block)

            print(f"Successfully saved digest to {output_path}")
            print(summary_block)
            
        except Exception as e:
            print(f"ERROR: Could not append summary to {output_path}: {e}", file=sys.stderr)
            return

def is_valid_repo(repo_url: str):
    return repo_url and "github.com" in repo_url

def is_processed_repo(output_filename: str) -> bool:
    # This repo will check if the incoming repo was processed
    folder_path = "data"
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return False
    
    if os.path.exists(json_file_path): # read the file if exists
        with open(json_file_path, 'r') as openfile:
            data = json.load(openfile)
            if output_filename in data:
                return True
    return False

def save_to_json(output_filename: str):
    """Store the filename into a json file for faster check

    Args:
        output_filename: filename storing processed data
    """
    data = {}
    if os.path.exists(json_file_path): # read the file if exists
        with open(json_file_path, 'r') as openfile:
            data = json.load(openfile)

    data[output_filename] = None # add another filename into this json file
    data = json.dumps(data, indent=4)
    with open(json_file_path, "w") as outfile:
        outfile.write(data)

def run_gitingest(repo_url: str, output_path: str, output_filename: str) -> bool:

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured output directory exists: {OUTPUT_DIR}")

    # Execute the gitingest command
    result = subprocess.run(['gitingest', repo_url, '-o', output_path], capture_output=True, text=True)
    # Check if the command was successful
    if result.returncode == 0:
        print("Command executed successfully")
        write_to_file(result, output_path)
        save_to_json(output_filename)
        print(f"--- Git Processing Finished ---")
        return True
    else:
        error_msg = f"gitingest command failed (code {result.returncode}): {result.stderr[:500]}..." # Limit error length
        print(f"ERROR: {error_msg}", file=sys.stderr)
        # Attempt to clean up potentially incomplete file on failure
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def ingest_repo(repo_url: str) -> tuple[bool, str, str | None]:
    """
    Processes a GitHub repo URL using the gitingest library (if available)
    and saves the primary content digest to a specified file.

    Return:
        a tuple: (bool_success, status_message, output_path)
          - output_path: the output path of the text file where processed content is saved to 

    """
    if not is_valid_repo(repo_url):
        return False, f"Invalid or non-GitHub URL provided: {repo_url}"

    output_filename = process_url(repo_url)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    if is_processed_repo(output_filename):
        return False, "Repository was processed previously.", output_path

    try:
        print(f"\n--- Starting Git Processing ---")
        print(f"Target Repository: {repo_url}")
        print(f"Output File:       {output_path}")
        print("Running processing function...")

        if run_gitingest(repo_url, output_path, output_filename):
            return True, "Repository ingested successfully.", output_path
        else:
            return False, error_msg # Failure status

    except OSError as e:
        error_msg = f"Could not create output directory '{OUTPUT_DIR}': {e}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"An unexpected error occurred during processing: {e}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        return False, error_msg # General failure status