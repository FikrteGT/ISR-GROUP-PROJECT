import xml.etree.ElementTree as ET
import math
import time
from elasticsearch import Elasticsearch
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "e7kUbdwwZ82mdCtw*9Je"),
    verify_certs=False
)
class Page:
    def __init__(self, page):
        self.page = page
        self.auth = 1.0
        self.hub = 1.0
        self.inLinkPages = set()
        self.outLinkPages = set()

    def setAuth(self, value):
        self.auth = value

    def setHub(self, value):
        self.hub = value

# Path to Cranfield dataset
dataset_path = r"C:\Users\pc\Desktop\ISR-assignment\Information-Retrieval-master\HW4\cranfield-trec-dataset-main\cranqrel.qry.xml"

# Read raw file and wrap with a root element
with open(dataset_path, "r", encoding="utf-8") as f:
    raw = f.read()

wrapped = "<ROOT>\n" + raw + "\n</ROOT>"
root = ET.fromstring(wrapped)

graphPages = {}

# Extract documents
for doc in root.findall("DOC"):
    doc_id_elem = doc.find("DOCNO")
    if doc_id_elem is None or not doc_id_elem.text:
        continue
    doc_id = doc_id_elem.text.strip()

    # NOTE: Cranfield dataset does not have explicit OUTLINKS.
    # For demonstration, we’ll treat references in TEXT as outlinks (dummy).
    text_elem = doc.find("TEXT")
    outlinks = []
    if text_elem is not None and text_elem.text:
        # Example heuristic: split text into words and treat DOCNO-like tokens as outlinks
        tokens = text_elem.text.strip().split()
        outlinks = [tok for tok in tokens if tok.startswith("DOC")]

    if doc_id not in graphPages:
        graphPages[doc_id] = Page(doc_id)

    for ol in outlinks:
        if ol not in graphPages:
            graphPages[ol] = Page(ol)
        graphPages[doc_id].outLinkPages.add(ol)
        graphPages[ol].inLinkPages.add(doc_id)

print("Total pages:", len(graphPages))

# HITS iteration
def hits_iteration(graphPages):
    # Update authority scores
    norm = 0
    for p in graphPages.values():
        p.setAuth(0)
        for q in p.inLinkPages:
            p.auth += graphPages[q].hub
        norm += p.auth * p.auth
    normAuth = math.sqrt(norm)
    for p in graphPages.values():
        if normAuth > 0:
            p.setAuth(p.auth / normAuth)

    # Update hub scores
    norm = 0
    for p in graphPages.values():
        p.setHub(0)
        for q in p.outLinkPages:
            p.hub += graphPages[q].auth
        norm += p.hub * p.hub
    normHub = math.sqrt(norm)
    for p in graphPages.values():
        if normHub > 0:
            p.setHub(p.hub / normHub)

# Run iterations
start_time = time.time()
for i in range(50):
    hits_iteration(graphPages)

# Save top hubs
with open("hub.txt", "w") as f:
    pagesByHub = sorted(graphPages.values(), key=lambda x: x.hub, reverse=True)
    for page in pagesByHub[:500]:
        f.write(f"{page.page} {page.hub:.6f} {len(page.outLinkPages)}\n")

# Save top authorities
with open("authority.txt", "w") as f:
    pagesByAuth = sorted(graphPages.values(), key=lambda x: x.auth, reverse=True)
    for page in pagesByAuth[:500]:
        f.write(f"{page.page} {page.auth:.6f} {len(page.inLinkPages)}\n")

# Runtime
elapsed = time.time() - start_time
hours = int(elapsed // 3600)
minutes = int((elapsed % 3600) // 60)
seconds = int(elapsed % 60)
print(f"Runtime: {hours}:{minutes}:{seconds}")
