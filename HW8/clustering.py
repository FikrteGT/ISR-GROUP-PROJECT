from bs4 import BeautifulSoup
import os
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans

# =========================
# CONFIG
# =========================
DOC_PATH = "cranfield-trec-dataset-main/cran.all.1400.xml"

T = 10   # LDA topics
K = 10   # clusters
TOP_WORDS = 10

# =========================
# GLOBALS
# =========================
docText = []
docMap = {}
relDoc = {}
clusters = {}
VectorMatrix = None


# =========================
# LOAD DOCUMENTS
# =========================
def buildDocText():
    global docText, docMap

    path = "cranfield-trec-dataset-main/cran.all.1400.xml"

    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # IMPORTANT FIX: use html.parser (NOT xml)
    soup = BeautifulSoup(content, "html.parser")

    docs = soup.find_all("doc")

    print("DEBUG DOC TAGS FOUND:", len(docs))

    for i, doc in enumerate(docs):
        docno = doc.find("docno")
        text = doc.find("text")

        if docno is None:
            continue

        docMap[i] = docno.text.strip()
        docText.append(text.text.strip() if text else "")


# =========================
# LDA
# =========================
def runLDA():
    global VectorMatrix

    vectorizer = CountVectorizer(
        stop_words="english",
        max_features=5000,
        token_pattern=r"(?u)\b[a-zA-Z]{3,}\b"
    )

    X = vectorizer.fit_transform(docText)

    lda = LatentDirichletAllocation(
        n_components=T,
        max_iter=20,
        learning_method="batch",
        random_state=42
    )

    lda.fit(X)
    VectorMatrix = lda.transform(X)

    words = vectorizer.get_feature_names_out()

    print("\n===== LDA TOP WORDS =====\n")
    for i, topic in enumerate(lda.components_):
        top_words = [words[j] for j in topic.argsort()[-TOP_WORDS:]]
        print(f"Topic {i+1}: {top_words}")


# =========================
# KMEANS
# =========================
def runKmeans():
    global clusters

    kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
    labels = kmeans.fit_predict(VectorMatrix)

    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = set()
        clusters[label].add(docMap[idx])

    print("\n===== CLUSTERS =====\n")
    for c in clusters:
        print(f"Cluster {c}: {list(clusters[c])[:10]}")


# =========================
# RELEVANCE FILE (QRELS)
# =========================
def buildRelevantDocs():
    global relDoc

    qrels_path = "cranfield-trec-dataset-main/cranqrel.trec.txt"

    with open(qrels_path, "r") as f:
        for line in f:
            q, _, doc, rel = line.split()
            if rel == "1":
                if doc not in relDoc:
                    relDoc[doc] = set()
                relDoc[doc].add(q)


# =========================
# RELATION FUNCTIONS
# =========================
def isSQ(doc1, doc2):
    return doc1 in relDoc and doc2 in relDoc and len(relDoc[doc1] & relDoc[doc2]) > 0


def isSC(doc1, doc2):
    for c in clusters:
        if doc1 in clusters[c] and doc2 in clusters[c]:
            return True
    return False


# =========================
# EVALUATION
# =========================
def evaluate():
    SQSC = SQDC = DQSC = DQDC = 0

    docs = list(relDoc.keys())

    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):

            d1 = docs[i]
            d2 = docs[j]

            sq = isSQ(d1, d2)
            sc = isSC(d1, d2)

            if sq and sc:
                SQSC += 1
            elif sq and not sc:
                SQDC += 1
            elif not sq and sc:
                DQSC += 1
            else:
                DQDC += 1

    acc = (SQSC + DQDC) / (SQSC + SQDC + DQSC + DQDC)

    print("\n===== EVALUATION =====")
    print("SQSC:", SQSC)
    print("SQDC:", SQDC)
    print("DQSC:", DQSC)
    print("DQDC:", DQDC)
    print("Accuracy:", acc)

    return acc


# =========================
# MAIN PIPELINE
# =========================
buildDocText()
print("Loaded docs:", len(docText))

runLDA()
runKmeans()
buildRelevantDocs()
evaluate()