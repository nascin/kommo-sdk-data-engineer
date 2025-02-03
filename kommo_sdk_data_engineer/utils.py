import os
import sys
from collections import deque
import shutil


# ANSI codes for colors
RED = "\033[91m"
GRAY = "\033[90m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"  # Reset color to default value (white)

def print_with_color(text, color: str = GRAY, output_verbose: bool=True):
    if output_verbose:
        sys.stdout.write(f"{color}{text}{RESET}\n")
        sys.stdout.flush()

def status_execution(**kwargs):
    if kwargs.get('output_verbose'):
        _ = kwargs.get('total_extracted')
        max_width = len(f"Total records extracted:         {_}")
        summary = "--- EXTRACTION SUMMARY ---".center(max_width)

        sys.stdout.write(f"\r{"\033[94m"}{summary}{RESET}\n")
        sys.stdout.write(f"\r{kwargs.get('color_total_extracted')}Total records extracted:___ {kwargs.get('total_extracted')}{RESET}\n")
        sys.stdout.write(f"\r{kwargs.get('color_total_errors')}Extraction errors:_________ {kwargs.get('total_errors')}{RESET}")
        sys.stdout.flush()


last_lines = deque(maxlen=7)
def print_last_extracted(text, color: str = GRAY, output_verbose: bool=True):
    if output_verbose:
        last_lines.append(f"{color}{text}{RESET}")

        # clear the output terminal before printing the new lines
        try:
            from IPython.display import clear_output
            clear_output(wait=True)
        except ImportError: # exception if code is not running in a Jupyter notebook
            os.system("cls" if os.name == "nt" else "clear")

        # write the last 7 lines
        for line in last_lines:
            sys.stdout.write(line + "\n")
        
        sys.stdout.flush()
