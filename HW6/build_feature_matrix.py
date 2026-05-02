from __future__ import annotations

import argparse
from pathlib import Path

from ir_pipeline import (
    InMemoryIndex,
    ElasticsearchIndexAdapter,
    build_feature_rows,
    parse_documents,
    parse_queries,
    parse_qrels,
    write_feature_matrix_csv,
    write_trec_results,
)


MODEL_OUTPUTS = {
    "tfidf": "TF-IDF_Results_File.txt",
    "okapi_tf": "OkapiTF_Results_File.txt",
    "bm25": "OkapiBM25_Results_File.txt",
    "laplace": "UnigramLMLaplace_Results_File.txt",
    "jm": "UnigramLMJM_Results_File.txt",
}

DEFAULT_MODELS = ["tfidf", "okapi_tf", "bm25"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the feature matrix and TREC result files.")
    parser.add_argument("--documents", required=True,
                        help="Path to the XML document collection.")
    parser.add_argument("--queries", required=True,
                        help="Path to the XML query file.")
    parser.add_argument("--qrels", required=True,
                        help="Path to the qrels file.")
    parser.add_argument("--output-csv", default="staticFeatureMatrix.csv",
                        help="Output feature matrix CSV file.")
    parser.add_argument("--output-dir", default=".",
                        help="Directory for TREC result files.")
    parser.add_argument("--index-elasticsearch", action="store_true",
                        help="Index the documents into Elasticsearch as well.")
    parser.add_argument("--index-name", default="cranfield",
                        help="Elasticsearch index name.")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS),
                        help="Comma-separated model list to score (tfidf,okapi_tf,bm25,laplace,jm).")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    documents = parse_documents(args.documents)
    queries = parse_queries(args.queries)
    qrels = parse_qrels(args.qrels)

    index = InMemoryIndex(documents)

    if args.index_elasticsearch:
        ElasticsearchIndexAdapter(
            index_name=args.index_name).index_documents(documents)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_models = [model.strip()
                       for model in args.models.split(",") if model.strip()]
    rows = build_feature_rows(index, queries, qrels,
                              model_names=selected_models)
    write_feature_matrix_csv(rows, args.output_csv)

    for model_name, filename in MODEL_OUTPUTS.items():
        if model_name not in selected_models:
            continue
        write_trec_results(index, queries, model_name, output_dir / filename)

    print(f"Wrote {len(rows)} feature rows to {args.output_csv}")


if __name__ == "__main__":
    main()
