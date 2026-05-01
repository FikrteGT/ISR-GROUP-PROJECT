import time
from elasticsearch import Elasticsearch
import os
import re

# -----------------------------
# 1. Connect to Elasticsearch
# -----------------------------
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "sY2SDX2lMkbFBKUEFQWh"),
    verify_certs=False,
    request_timeout=120,     # wait up to 120 seconds
    max_retries=5,
    retry_on_timeout=True
)

# -----------------------------
# 2. Path to CACM dataset
# -----------------------------
# Folder contains ONE file: cacm.all
path = r"C:\Information-Retrieval\hw1\cacm_dataSet"
file_path = os.path.join(path, "cacm.all")

# -----------------------------
# 3. Start timing
# -----------------------------
start_time = time.time()

doc_count = 0

# -----------------------------
# 4. Open CACM file
# -----------------------------
with open(file_path, "r", encoding="utf-8", errors="ignore") as file:

    docno = None
    text = ""

    for line in file:
        line = line.strip()

        # New document starts
        if line.startswith(".I"):
            # Index previous document
            if docno is not None:
                es.index(
                    index="cacm",
                    id=docno,
                    document={"text": text}
                )
                print("Indexed:", docno)
                doc_count += 1

            # Get new document ID
            docno = line.split()[1]
            text = ""

        # Start of main text section
        elif line.startswith(".W"):
            continue

        # Ignore other CACM tags (.T, .A, .B, etc.)
        elif line.startswith("."):
            continue

        # Actual document text
        else:
            text += " " + line

    # Index the last document
    if docno is not None:
        es.index(
            index="cacm",
            id=docno,
            document={"text": text}
        )
        print("Indexed:", docno)
        doc_count += 1
        time.sleep(0.001)   # 1 millisecond pause
# -----------------------------
# 5. Time statistics
# -----------------------------
elapsed = time.time() - start_time
hours = elapsed // 3600
minutes = (elapsed % 3600) // 60
seconds = elapsed % 60

print("\nTotal documents indexed:", doc_count)
print("Time taken: %d:%d:%d" % (hours, minutes, seconds))
