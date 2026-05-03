# ISR Group Project Information Storage and Retrieval

A comprehensive collection of information retrieval (IR) coursework covering the full spectrum of modern IR techniques: from classical retrieval models and custom indexing to link analysis, learning-to-rank, spam classification, and unsupervised document clustering. All modules are implemented in Python and evaluated against standard TREC benchmark datasets.

---

## Repository Structure

| Folder | Topic |
|--------|-------|
| [HW1](#hw1--retrieval-models-with-elasticsearch) | Retrieval models with Elasticsearch |
| [HW2](#hw2--custom-inverted-index) | Custom inverted index |
| [HW4](#hw4--link-analysis-pagerank--hits) | Link analysis: PageRank & HITS |
| [HW5](#hw5--trec-evaluation-utilities) | TREC evaluation utilities |
| [HW6](#hw6--learning-to-rank-ir-pipeline) | Learning-to-rank IR pipeline |
| [HW7](#hw7--email-spam-classification) | Email spam classification |
| [HW8](#hw8--document-clustering) | Document clustering |

---

## HW1 – Retrieval Models with Elasticsearch

Implements and compares multiple retrieval models against the AP89 news corpus using Elasticsearch as the backend index.

### Datasets
- **AP89 Collection** – Associated Press newswire articles (TREC format)
- **Queries** – `query_desc.51-100.short.txt` (50 queries)
- **Relevance judgements** – `qrels.adhoc.51-100.AP89.txt`

### Key Scripts

| Script | Purpose |
|--------|---------|
| `Create_Index.py` | Parses TREC-format documents and indexes them into Elasticsearch |
| `Query_Processing.py` | Runs queries against Elasticsearch and retrieves TF/DF statistics |
| `Retrieval_Models.py` | Implements five retrieval models using the statistics from ES |
| `Pseudo_Relevance.py` | Implements pseudo-relevance feedback to expand queries |
| `Trec_Eval.py` / `Trec_Prep.py` | Formats results and runs `trec_eval` for quantitative evaluation |

### Retrieval Models

- **ES Built-in** – Elasticsearch's native BM25 ranking via the `match` API
- **Okapi TF** – Length-normalized term frequency scoring
- **TF-IDF** – Okapi TF weighted by inverse document frequency
- **Okapi BM25** – Probabilistic ranking with tunable constants k₁, k₂, and b
- **Unigram LM – Laplace smoothing** – Language model with add-one smoothing
- **Unigram LM – Jelinek-Mercer smoothing** – Language model mixing document and corpus distributions

### Output Format

Each retrieval model produces one output file; each line has the format:

```
<query-number> Q0 <docno> <rank> <score> Exp
```

### Getting Started

1. Install and start [Elasticsearch](https://www.elastic.co) and the [Kibana](https://www.elastic.co/products/kibana) plugin.
2. Download [AP89_DATA.zip](http://dragon.ischool.drexel.edu/example/ap89_collection.zip) and extract it.
3. Run `Create_Index.py` to index the corpus.
4. Run `Query_Processing.py` to execute queries with any of the above models.
5. Evaluate results with `trec_eval`:

```bash
trec_eval [-q] qrels.adhoc.51-100.AP89.txt <results_file>
```

---

## HW2 – Custom Inverted Index

Replaces the Elasticsearch backend from HW1 with a hand-built inverted index, demonstrating disk-efficient index construction via merge-sort.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `Unstemmed_With_Stopwords_Index-1.py` | Builds an inverted index without stemming, removing stop words |
| `Stemmed_Stopwords_Removed_Index-1.py` | Builds an inverted index with Porter stemming and stop word removal |
| `Query_Processing.py` / `Query_Processing_Stemmed.py` | Runs ranked queries against the respective index |
| `Query_Processing_Unstemmed_Proximity.py` / `Query_Processing_Stemmed_Proximity.py` | Proximity-based retrieval model |
| `Retrieval_Models.py` / `Retrieval_Models_Stemmed.py` | TF-IDF, BM25, and LM scoring using the custom index |
| `Demo_Related.py`, `Demo_Stemmed.py`, `Demo_Unstemmed.py` | Demo scripts comparing stemmed vs unstemmed retrieval |

### Index Design

Each inverted list entry stores:
- Document frequency (DF) and collection term frequency (CF / TTF)
- Per-document: document ID, TF, and a list of term positions

Two index variants are built:
1. **Unstemmed** – tokenized and lowercased, stop words removed
2. **Stemmed** – additionally Porter-stemmed before indexing

### Tokenization Rules
- A token is any contiguous sequence of alphanumeric characters (optionally containing internal periods, e.g., `192.168.0.1`)
- All tokens are lowercased
- Stop words are filtered using the [NLTK stop word list](http://www.ccs.neu.edu/home/vip/teach/IRcourse/2_indexing_ngrams/HW2/stoplist.txt)

### Proximity Search
An additional retrieval model scores documents based on how close query terms appear to each other, using term position data stored in the index.

---

## HW4 – Link Analysis: PageRank & HITS

Implements two classic link-analysis algorithms on a web graph loaded from a `linkgraph.txt` file (one node and its outlinks per line).

### Key Scripts

| Script | Purpose |
|--------|---------|
| `PageRank.py` | Iterative PageRank with configurable damping factor (d = 0.85) and sink-node handling |
| `PageRankDummy.py` | Simplified PageRank variant for testing |
| `HITS.py` | Hyperlink-Induced Topic Search (HITS) computing hub and authority scores |
| `hit.py` | Supporting HITS utilities |
| `Graph.py` / `GraphDummy.py` | Graph construction and traversal helpers |
| `Canonicalizer.py` | URL/node canonicalization |
| `Elasticsearch.py` | Optional ES integration for graph-enriched retrieval |
| `scorer.py` | Combines link scores with content-based retrieval scores |
| `cranfieldGraph.py` | Builds a citation graph from the Cranfield dataset |

### Algorithms

**PageRank** – Computes the stationary distribution of a random walk over the link graph:

```
PR(n) = (1−d)/N  +  d × Σ PR(m)/|out(m)|   for all m→n
```

Sink nodes (pages with no outlinks) redistribute their rank uniformly across all nodes.

**HITS** – Iteratively updates hub and authority scores until convergence:
- *Authority score*: sum of hub scores of all pages pointing in
- *Hub score*: sum of authority scores of all pages pointed to

---

## HW5 – TREC Evaluation Utilities

Provides helper scripts for preparing and evaluating retrieval results against TREC relevance judgements.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `Trec_Prep.py` | Parses raw relevance judgement files and formats them for `trec_eval` |
| `Trec_Eval.py` | Runs evaluation and aggregates MAP, P@10, and other metrics across models |

Results are stored as Excel spreadsheets (`Graphs.xlsx`, `Precision-Recall.xlsx`) for comparison across retrieval models.

---

## HW6 – Learning-to-Rank IR Pipeline

A complete IR pipeline that extracts document features, trains a learning-to-rank model, and evaluates performance on the CACM and AP89 datasets.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `build_feature_matrix.py` | Parses XML documents and queries, builds an in-memory index, writes `staticFeatureMatrix.csv`, and exports TREC run files for TF-IDF, Okapi TF, BM25, Laplace, and Jelinek-Mercer |
| `train_ranker.py` | Reads the feature matrix, trains a linear regression ranker with cross-validation, and writes results in TREC format |
| `ir_pipeline.py` | End-to-end pipeline orchestration |
| `Feature_Matrix.py` | Feature extraction helpers |
| `plot_eval.py` | Plots precision-recall curves for each model |
| `ML_Learning Algorithms.py` | Compatibility wrapper around `train_ranker.py` |
| `trec_eval.pl` | Bundled Perl `trec_eval` script |

### Usage

```bash
python build_feature_matrix.py --documents path/to/docs.xml --queries path/to/queries.xml --qrels path/to/qrels.txt
python train_ranker.py --input-csv staticFeatureMatrix.csv
```

To also index documents into Elasticsearch:

```bash
python build_feature_matrix.py --documents path/to/docs.xml --queries path/to/queries.xml --qrels path/to/qrels.txt --index-elasticsearch
```

### Features Used for Ranking

Each query-document pair is represented by a feature vector drawn from the five classical retrieval scores (TF-IDF, Okapi TF, BM25, Laplace LM, Jelinek-Mercer LM) and document-level statistics (length, term coverage).

---

## HW7 – Email Spam Classification

Applies NLP and machine learning to classify emails from the [TREC 2007 Spam Track](https://plg.uwaterloo.ca/~gvcormac/trec07p/) dataset as spam or ham.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `EmailFilter.py` | Parses raw emails (stripping HTML, URLs, and headers), loads spam/ham labels from the TREC index file |
| `Indexer.py` | Builds a term index over the email corpus |
| `FeatureMatrix.py` | Constructs bag-of-words or TF-IDF feature matrices for classification |
| `Tagger.py` | POS-tagging utilities using NLTK |
| `MachineLearning.py` | Trains classifiers (logistic regression, etc.) and reports accuracy |
| `ML-GIVEN.py` | Baseline classifier provided as reference |
| `doc-term.py` | Document-term matrix construction utilities |
| `setup_nltk.py` | Downloads required NLTK resources |

### Dataset

The [TREC 2007 Public Spam Corpus](https://plg.uwaterloo.ca/~gvcormac/trec07p/) (`trace07/trec07p/`) must be downloaded separately and placed inside the `HW7/` folder. The index file at `trace07/trec07p/full/index` maps each email file to its `spam` or `ham` label.

### Pipeline

1. `EmailFilter.py` reads the index, parses each email, strips HTML/URLs, and writes cleaned text to the `Files/` output directory.
2. `Indexer.py` and `FeatureMatrix.py` build a vectorized representation of the corpus.
3. `MachineLearning.py` trains and evaluates a classifier using k-fold cross-validation.

---

## HW8 – Document Clustering

Applies unsupervised clustering and topic modeling to the [Cranfield dataset](https://github.com/jjz17/cranfield-trec-dataset) (1,400 aerodynamics abstracts).

### Key Scripts

| Script | Purpose |
|--------|---------|
| `clustering.py` | Full pipeline: loads documents, vectorizes with CountVectorizer, runs LDA topic modeling and K-Means clustering, prints top words per topic/cluster |
| `partition.py` | Standalone K-Means partitioning variant |

### Algorithms

- **LDA (Latent Dirichlet Allocation)** – Discovers `T = 10` latent topics across the corpus; reports the top words per topic.
- **K-Means** – Partitions the document vectors into `K = 10` clusters; reports the most representative terms per cluster centroid.

### Dataset

Download the Cranfield TREC dataset and place it at:

```
HW8/cranfield-trec-dataset-main/cran.all.1400.xml
```

### Dependencies

```bash
pip install beautifulsoup4 scikit-learn numpy
```

---

## Prerequisites

All modules require **Python 3.7+**. Install common dependencies with:

```bash
pip install elasticsearch elasticsearch-dsl nltk scikit-learn numpy pandas beautifulsoup4
```

Individual homework folders may contain a `requirements.txt` with module-specific pins (see `HW6/requirements.txt`).

---

## Evaluation

All retrieval experiments are evaluated with [trec_eval](https://trec.nist.gov/trec_eval/). Key metrics reported:

- **MAP** – Mean Average Precision
- **P@10** – Precision at rank 10
- **Recall** – Overall recall across all queries

Run evaluation with:

```bash
trec_eval [-q] <qrels_file> <results_file>
```

The `-q` flag prints per-query breakdowns in addition to the summary average.
