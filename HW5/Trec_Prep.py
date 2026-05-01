from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

es = Elasticsearch(
    "https://localhost:9200",
    # update this if you chose a different password
    basic_auth=("elastic", "sY2SDX2lMkbFBKUEFQWh"),
    verify_certs=False,
    request_timeout=120
)

QRELS_INPUT = r'C:\Information-Retrieval\HW1\cacm_dataSet\qrels.text'
QUERY_INPUT = r'C:\Information-Retrieval\HW1\cacm_dataSet\query.text'
QRELS_OUTPUT = r'C:\Information-Retrieval\HW5\qrels.txt'
RANKLIST_OUTPUT = r'C:\Information-Retrieval\HW5\rankList.txt'


def createQrel():
    """
    Reads CACM qrels.text and writes a clean qrels.txt.
    CACM format per line:  queryID  docID  0  0
    All listed documents are considered relevant, so we write relevance = 1.
    Output format:  queryID 0 docID 1
    """
    with open(QRELS_INPUT, 'r') as fin, open(QRELS_OUTPUT, 'w') as fout:
        for line in fin:
            cols = line.split()
            if len(cols) >= 2:
                queryID = cols[0]
                docID = cols[1]
                fout.write(f"{queryID} 0 {docID} 1\n")
    print("qrels.txt created successfully.")


def load_queries():
    """
    Reads CACM query.text and returns list of (queryText, queryID) tuples.
    CACM query format uses .I for ID and .W for the start of query text.
    """
    queries = []
    qid, text, in_w = None, '', False
    with open(QUERY_INPUT, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('.I'):
                if qid is not None and text.strip():
                    queries.append((text.strip(), str(qid)))
                qid = int(line.split()[1])
                text, in_w = '', False
            elif line.startswith('.W'):
                in_w = True
            elif line.startswith('.'):
                in_w = False
            elif in_w:
                text += ' ' + line
        if qid is not None and text.strip():
            queries.append((text.strip(), str(qid)))
    print(f"Loaded {len(queries)} queries from query.text.")
    return queries


def createRankList(query, qid):
    """
    Runs a query against the 'cacm' Elasticsearch index.
    Saves top 1000 results to rankList.txt in TREC format:
    queryID Q0 docID rank score Exp
    """
    s = Search(using=es, index="cacm").query("match", text=query)
    res = s[0:1000].execute()
    with open(RANKLIST_OUTPUT, 'a') as f:
        for i, hit in enumerate(res.hits, 1):
            f.write(f"{qid} Q0 {hit.meta.id} {i} {hit.meta.score} Exp\n")


def main():
    # Step 1: Convert CACM qrels.text -> qrels.txt
    createQrel()

    # Step 2: Clear rankList.txt before writing fresh results
    open(RANKLIST_OUTPUT, 'w').close()

    # Step 3: Load all 64 CACM queries and run them against Elasticsearch
    queries = load_queries()
    for query_text, qid in queries:
        print(f"Running query {qid}...")
        createRankList(query_text, qid)

    print("rankList.txt created successfully.")


main()
