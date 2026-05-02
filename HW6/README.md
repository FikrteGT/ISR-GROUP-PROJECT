# HW6 IR Pipeline

This workspace has a small, runnable information retrieval pipeline.

## Scripts

- `build_feature_matrix.py` parses XML documents and queries, builds an in-memory index, writes `staticFeatureMatrix.csv`, and exports TREC run files for TF-IDF, Okapi TF, BM25, Laplace, and Jelinek-Mercer.
- `train_ranker.py` reads `staticFeatureMatrix.csv`, trains a linear regression ranker with cross-validation, and writes `trainingperformance.txt` in TREC format.
- `ML_Learning Algorithms.py` is kept as a compatibility wrapper around `train_ranker.py`.

## Example usage

```bash
python build_feature_matrix.py --documents path/to/docs.xml --queries path/to/queries.xml --qrels path/to/qrels.txt
python train_ranker.py --input-csv staticFeatureMatrix.csv
```

If you also want to index documents into Elasticsearch, add `--index-elasticsearch` to `build_feature_matrix.py`.
