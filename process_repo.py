# Synchronous usage
from gitingest import ingest, ingest_async
import os, sys
import asyncio

OUTPUT_DIR = "data"

def process_url(repo_url: str):
    """
    Processes a GitHub repo URL into a filename using all the path
    components in the url connected by a hyphen
    """
    path = repo_url[19:] # exclude the part: https://github.com/
    filename = "-".join(path.split("/"))
    return filename

async def ingest_repo(repo_url: str):
    """
    Processes a GitHub repo URL using the gitingest library (if available)
    and saves the primary content digest to a specified file.
    """
    if repo_url and "github.com" in repo_url:
        output_filename = process_url(repo_url)
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        print(f"\n--- Starting Git Processing ---")
        print(f"Target Repository: {repo_url}")
        print(f"Output File:       {output_path}")

        try:
            print("Running processing function...")

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"Ensured output directory exists: {OUTPUT_DIR}")

            result = asyncio.run(ingest_async("path/to/directory"))
            summary_data, tree_data, content_data = result
            # summary_data, tree_data, content_data = await ingest_async(repo_url)

            # concatenate all these data
            repo_content = "\n\n".join(list(summary_data, tree_data, content_data))

            print(f"Processing finished. Writing digest content to file...")
            # Write the main content digest to the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(repo_content)

            print(f"Successfully saved digest to {output_path}")
            # Get summary data for debugging
            print("Summary:", summary_data)

        except OSError as e:
            print(f"ERROR: Could not create output directory '{OUTPUT_DIR}': {e}", file=sys.stderr)
            return
        
        except Exception as e:
            print(f"ERROR: An error occurred during processing or file writing: {e}", file=sys.stderr)
            sys.exit(0)
            
        print(f"--- Git Processing Finished ---")