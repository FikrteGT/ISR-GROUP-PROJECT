from __future__ import division
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import re
import string

# -----------------------------
# CONNECT TO ELASTICSEARCH
# -----------------------------
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "sY2SDX2lMkbFBKUEFQWh"),
    verify_certs=False,
    request_timeout=120
)

INDEX_NAME = "cacm"


# -----------------------------
# STOPWORD REMOVAL
# -----------------------------
def load_stopwords():
    with open(r"C:\Information-Retrieval\hw1\cacm_dataSet\common_words", "r") as f:
        return f.read().splitlines()


stopWords = load_stopwords()


def queryProcessor(query):
    query = query.lower()
    query = query.translate(str.maketrans("", "", string.punctuation))

    words = query.split()
    cleaned = []

    for w in words:
        if w not in stopWords:
            cleaned.append(w)

    return cleaned


# -----------------------------
# SEARCH FUNCTION (BM25 / ES built-in)
# -----------------------------
def search_query(query, qid):
    cleaned_query = queryProcessor(query)

    final_query = " ".join(cleaned_query)

    s = Search(using=es, index=INDEX_NAME).query("match", text=final_query)

    response = s[:100].execute()

    results = []

    rank = 1
    for hit in response:
        docno = hit.meta.id
        score = hit.meta.score

        results.append(f"{qid} Q0 {docno} {rank} {score} Exp")
        rank += 1

    return results


# -----------------------------
# READ QUERIES FILE
# -----------------------------
def load_queries():
    queries = []

    with open(r"C:\Information-Retrieval\hw1\cacm_dataSet\query.text", "r") as f:
        for line in f:
            line = re.sub(r"\s+", " ", line).strip()
            if line:
                queries.append(line)

    return queries


# -----------------------------
# MAIN EXECUTION
# -----------------------------
queries = load_queries()

all_results = []

qid = 1
for q in queries:
    print("Processing Query:", qid)

    results = search_query(q, qid)
    all_results.extend(results)

    qid += 1


# -----------------------------
# SAVE OUTPUT FILE
# -----------------------------
with open("results_bm25.txt", "w") as f:
    for line in all_results:
        f.write(line + "\n")

print("\nDONE: results_bm25.txt created")
