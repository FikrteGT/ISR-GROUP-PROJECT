import os
from elasticsearch import Elasticsearch
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "e7kUbdwwZ82mdCtw*9Je"),
    verify_certs=False
)
# Initialize data structures
docID = set()
linkgraph = {}
lg = {}
sinkNodes = set()

# Open the dataset file safely
with open(r"C:\\Users\\pc\Desktop\\ISR-assignment\\Information-Retrieval-master\\HW4\\cranfield-trec-dataset-main\\cran.all.1400.xml", "r") as g:
    for line in g:
        line = line.strip()
        if ":" not in line:   # skip malformed lines
            continue

        # Split into docID and outlinks
        parts = line.split(":", 1)
        doc = parts[0].strip()
        outlinks = parts[1].split()

        # Add docID
        docID.add(doc)

        # Build linkgraph
        for ol in outlinks:
            ol = ol.strip()
            if ol in linkgraph:
                linkgraph[ol].add(doc)
            else:
                linkgraph[ol] = {doc}

# Build final link graph and sink nodes
for ol in linkgraph:
    if ol in docID:
        lg[ol] = linkgraph.get(ol)
    if ol == '':
        for link in linkgraph.get(ol, []):
            sinkNodes.add(link)

# Write output file
with open(r"C:\\Users\\pc\\Desktop\\ISR-assignment\\Information-Retrieval-master\\HW4\\LinkGraphDummy.txt", "w") as of:
    for ol in lg:
        line = ol
        for il in lg[ol]:
            line += ' ' + il
        of.write(line + '\n')

# Print results
print("Sink nodes:", sinkNodes)
print("Number of sink nodes:", len(sinkNodes))
print("Number of documents:", len(docID))
