# Synchronous usage
import os, sys, subprocess
from subprocess import CompletedProcess

OUTPUT_DIR = "data"

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
            file = open(output_path, "a", encoding='utf-8')
            file.write("\n\n--- Summary ---\n")
            file.write(summary_block)
            file.close()

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

    for root, _, files in os.walk(folder_path):
        for file in files:
            print(file)
            if file == output_filename:
                return True
            
    return False


def ingest_repo(repo_url: str) -> bool:
    """
    Processes a GitHub repo URL using the gitingest library (if available)
    and saves the primary content digest to a specified file.

    Return:
        - True: if the repo wasn't processed and now ingested successfully
        - False: if the repo was processed or now fail to be ingested
    """
    if is_valid_repo(repo_url):
        output_filename = process_url(repo_url)
        if is_processed_repo(output_filename):
            return False
        
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        print(f"\n--- Starting Git Processing ---")
        print(f"Target Repository: {repo_url}")
        print(f"Output File:       {output_path}")

        try:
            print("Running processing function...")

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"Ensured output directory exists: {OUTPUT_DIR}")

            # Execute the gitingest command
            result = subprocess.run(['gitingest', repo_url, '-o', output_path], capture_output=True, text=True)
            # Check if the command was successful
            if result.returncode == 0:
                print("Command executed successfully")
                write_to_file(result, output_path)
            else:
                print("Command failed with error code:", result.returncode)
                print("Error:", result.stderr)
                return False

        except OSError as e:
            print(f"ERROR: Could not create output directory '{OUTPUT_DIR}': {e}", file=sys.stderr)
            return False
        
        except Exception as e:
            print(f"ERROR: An error occurred during processing or file writing: {e}", file=sys.stderr)
            sys.exit(0)
            
        print(f"--- Git Processing Finished ---")
        return True