from __future__ import division
from elasticsearch import Elasticsearch
import math
from operator import itemgetter
import string

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "sY2SDX2lMkbFBKUEFQWh"),
    verify_certs=False,
    request_timeout=120
)

INDEX_NAME = "cacm"

# Corpus stats - all hardcoded, no need to query ES for these
D         = 3204    # total docs in CACM
avgDocLen = 185.0   # average document length
V         = 141043  # vocabulary size

print(f"Average doc length: {avgDocLen:.2f}")


# --------------------------------------------------
# Load stopwords
# --------------------------------------------------
with open(r"C:\Information-Retrieval\HW1\cacm_dataSet\common_words", "r") as f:
    STOPWORDS = set(f.read().splitlines())


def clean_query(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return [w for w in text.split() if w not in STOPWORDS]


# --------------------------------------------------
# Get term vector for a single doc from ES
# --------------------------------------------------
def get_term_vector(doc_id):
    """Returns {term: (tf, doc_len)} for a document."""
    try:
        tv = es.termvectors(
            index=INDEX_NAME,
            id=doc_id,
            fields=["text"],
            term_statistics=True,
            field_statistics=True
        )
        terms = tv["term_vectors"].get("text", {}).get("terms", {})
        doc_len = sum(v["term_freq"] for v in terms.values())
        return {t: (v["term_freq"], doc_len) for t, v in terms.items()}
    except Exception:
        return {}


# --------------------------------------------------
# Search: get top 100 doc IDs for a query term
# --------------------------------------------------
def search_docs(query_terms):
    query_str = " ".join(query_terms)
    res = es.search(
        index=INDEX_NAME,
        body={"query": {"match": {"text": query_str}}, "size": 100}
    )
    return [hit["_id"] for hit in res["hits"]["hits"]]


# --------------------------------------------------
# Get DF for a term
# --------------------------------------------------
def get_df(term):
    res = es.count(
        index=INDEX_NAME,
        body={"query": {"term": {"text": term}}}
    )
    return max(res["count"], 1)


# --------------------------------------------------
# Retrieval Models
# --------------------------------------------------

def Total_okapiTF(qNo, query_terms, doc_ids):
    docScore = []
    for doc_id in doc_ids:
        tv = get_term_vector(doc_id)
        tf = 0
        for term in query_terms:
            if term in tv:
                tfwd, docLen = tv[term]
                tf += tfwd / (tfwd + 0.5 + 1.5 * (docLen / avgDocLen))
        docScore.append([doc_id, tf])

    docScore.sort(key=itemgetter(1), reverse=True)
    with open("OkapiTF_Results_File.txt", "a") as f:
        for rank, ds in enumerate(docScore, 1):
            f.write(f"{qNo} Q0 {ds[0]} {rank} {ds[1]} Exp\n")


def TF_IDF(qNo, query_terms, doc_ids):
    docScore = []
    df_cache = {t: get_df(t) for t in query_terms}

    for doc_id in doc_ids:
        tv = get_term_vector(doc_id)
        score = 0
        for term in query_terms:
            if term in tv:
                tfwd, docLen = tv[term]
                okapitf = tfwd / (tfwd + 0.5 + 1.5 * (docLen / avgDocLen))
                score += okapitf * math.log10(D / df_cache[term])
        docScore.append([doc_id, score])

    docScore.sort(key=itemgetter(1), reverse=True)
    with open("TFIDF_Results_File.txt", "a") as f:
        for rank, ds in enumerate(docScore, 1):
            f.write(f"{qNo} Q0 {ds[0]} {rank} {ds[1]} Exp\n")


def Okapi_BM25(qNo, query_terms, doc_ids):
    k1 = 1.2
    k2 = 1.2
    b  = 0.75
    df_cache = {t: get_df(t) for t in query_terms}

    docScore = []
    for doc_id in doc_ids:
        tv = get_term_vector(doc_id)
        score = 0
        for term in query_terms:
            if term in tv:
                tfwd, docLen = tv[term]
                df    = df_cache[term]
                idf   = math.log10((D + 0.5) / (df + 0.5))
                tf    = (tfwd * (k1 + 1)) / (tfwd + k1 * (1 - b + b * docLen / avgDocLen))
                qtf   = (tfwd * (k2 + 1)) / (tfwd + k2)
                score += idf * tf * qtf
        docScore.append([doc_id, score])

    docScore.sort(key=itemgetter(1), reverse=True)
    with open("BM25_Results_File.txt", "a") as f:
        for rank, ds in enumerate(docScore, 1):
            f.write(f"{qNo} Q0 {ds[0]} {rank} {ds[1]} Exp\n")


def UnigramLM_Laplace(qNo, query_terms, doc_ids):
    docScore = []
    for doc_id in doc_ids:
        tv = get_term_vector(doc_id)
        score = 0
        doc_len = sum(v[1] for v in tv.values()) if tv else 1
        for term in query_terms:
            tfwd = tv[term][0] if term in tv else 0
            score += math.log((tfwd + 1) / (doc_len + V))
        docScore.append([doc_id, score])

    docScore.sort(key=itemgetter(1), reverse=True)
    with open("Laplace_Results_File.txt", "a") as f:
        for rank, ds in enumerate(docScore, 1):
            f.write(f"{qNo} Q0 {ds[0]} {rank} {ds[1]} Exp\n")


def UnigramLM_JelinekMercer(qNo, query_terms, doc_ids):
    lam = 0.4
    docScore = []

    # corpus probability: cf / total_corpus_len
    total_corpus_len = D * avgDocLen

    for doc_id in doc_ids:
        tv = get_term_vector(doc_id)
        score = 0
        doc_len = sum(v[1] for v in tv.values()) if tv else 1
        for term in query_terms:
            tfwd = tv[term][0] if term in tv else 0
            cf   = tv[term][0] if term in tv else 1   # fallback
            p_ml = tfwd / doc_len if doc_len > 0 else 0
            p_bg = cf / total_corpus_len
            p_jm = lam * p_ml + (1 - lam) * p_bg
            if p_jm > 0:
                score += math.log(p_jm)
        docScore.append([doc_id, score])

    docScore.sort(key=itemgetter(1), reverse=True)
    with open("JelinekMercer_Results_File.txt", "a") as f:
        for rank, ds in enumerate(docScore, 1):
            f.write(f"{qNo} Q0 {ds[0]} {rank} {ds[1]} Exp\n")


# --------------------------------------------------
# Load queries
# --------------------------------------------------
def load_queries():
    queries = []
    qid, text, in_w = None, '', False
    with open(r"C:\Information-Retrieval\HW1\cacm_dataSet\query.text", "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith(".I"):
                if qid and text.strip():
                    queries.append((qid, text.strip()))
                qid = line.split()[1]
                text, in_w = '', False
            elif line.startswith(".W"):
                in_w = True
            elif line.startswith("."):
                in_w = False
            elif in_w:
                text += " " + line
        if qid and text.strip():
            queries.append((qid, text.strip()))
    return queries


# Clear output files before writing
for fname in ["OkapiTF_Results_File.txt", "TFIDF_Results_File.txt",
              "BM25_Results_File.txt", "Laplace_Results_File.txt",
              "JelinekMercer_Results_File.txt"]:
    open(fname, "w").close()

queries = load_queries()
total   = len(queries)

for idx, (qid, qtext) in enumerate(queries, 1):
    print(f"Running Query {idx} / {total}  (ID: {qid})")
    terms   = clean_query(qtext)
    doc_ids = search_docs(terms)

    Total_okapiTF(qid, terms, doc_ids)
    TF_IDF(qid, terms, doc_ids)
    Okapi_BM25(qid, terms, doc_ids)
    UnigramLM_Laplace(qid, terms, doc_ids)
    UnigramLM_JelinekMercer(qid, terms, doc_ids)

print("\nDone! Output files created:")
print("  OkapiTF_Results_File.txt")
print("  TFIDF_Results_File.txt")
print("  BM25_Results_File.txt")
print("  Laplace_Results_File.txt")
print("  JelinekMercer_Results_File.txt")
