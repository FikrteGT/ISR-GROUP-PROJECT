from elasticsearch import Elasticsearch
import warnings
import urllib3

# ----------------------------
# suppress warnings (optional)
# ----------------------------
warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------
# connect
# ----------------------------
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "e7kUbdwwZ82mdCtw*9Je"),
    verify_certs=False
)

INDEX = "hw3_crawl"

# ----------------------------
# RESET INDEX (VERY IMPORTANT)
# ----------------------------
if es.indices.exists(index=INDEX):
    es.indices.delete(index=INDEX)

es.indices.create(index=INDEX)

print("Index reset complete")

# ----------------------------
# SAMPLE DATASET (MORE DOCS)
# ----------------------------
docs = {
    "doc1": "doc2\ndoc3\ndoc4",
    "doc2": "doc3\ndoc5",
    "doc3": "doc1\ndoc6",
    "doc4": "doc2\ndoc6",
    "doc5": "doc1\ndoc3",
    "doc6": ""   # sink node
}

# ----------------------------
# INDEX DOCUMENTS
# ----------------------------
for doc_id, outlinks in docs.items():
    es.index(
        index=INDEX,
        id=doc_id,
        document={"outlinks": outlinks}
    )

print("Documents inserted")

# ----------------------------
# FIND SINK NODES
# ----------------------------
sink_nodes = set()

for doc_id, outlinks in docs.items():
    if outlinks.strip() == "":
        sink_nodes.add(doc_id)

print("Sink nodes:", sink_nodes)
print("Number of sink nodes:", len(sink_nodes))