import os
import email
from bs4 import BeautifulSoup
import re

# Use a variable for the path to keep it clean
path = "Files/"

# Check if the directory exists first to avoid errors
if not os.path.exists(path):
    print(f"Error: The folder '{path}' was not found.")
else:
    Files = os.listdir(path)

    for file in Files:
        # Skip system files or directories
        if file == '.DS_Store' or os.path.isdir(path + file):
            continue
            
        try:
            # 1. Open for reading
            with open(path + file, 'r', encoding="ISO-8859-1") as f:
                line = f.readline()
                # Check if line has a '/' before trying to split it
                if '/' in line:
                    parts = line.rsplit('/', 1)
                    tag = parts[1].replace('EMAIL>\n', '/EMAILID>\n')
                    line = parts[0] + tag
                
                rest = f.read()

            # 2. Open for writing (outside the read block)
            with open(path + file, 'w', encoding="ISO-8859-1") as wf:
                wf.writelines(line + rest)
            
            print(f"Processed: {file}")

        except Exception as e:
            print(f"Could not process {file}: {e}")

    print("Done! All files processed.")