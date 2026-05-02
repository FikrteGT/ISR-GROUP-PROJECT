from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans

FILE = "cranfield-trec-dataset-main/cran.all.1400.xml"

doc_ids = []
doc_texts = []

with open(FILE, encoding="utf-8", errors="ignore") as f:
    content = f.read()

# use html parser (better for imperfect XML collections)
soup = BeautifulSoup(content, "html.parser")

docs = soup.find_all("doc")

for doc in docs:
    docno = doc.find("docno").get_text(strip=True)
    title = doc.find("title").get_text(" ", strip=True)
    text = doc.find("text").get_text(" ", strip=True)

    doc_ids.append(docno)
    doc_texts.append(title + " " + text)

print("Loaded docs:", len(doc_ids))

# Vectorize
vectorizer = CountVectorizer(stop_words="english", max_features=5000)
X = vectorizer.fit_transform(doc_texts)

# Topic vectors
lda = LatentDirichletAllocation(n_components=20, random_state=42)
topic_vectors = lda.fit_transform(X)

# Partitioning
k = 10
kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
labels = kmeans.fit_predict(topic_vectors)

clusters = {}

for i, label in enumerate(labels):
    clusters.setdefault(label, []).append(doc_ids[i])

for c in sorted(clusters):
    print(f"\nCluster {c}:")
    print(", ".join(clusters[c][:20]))