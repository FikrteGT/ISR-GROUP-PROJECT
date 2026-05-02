from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from operator import itemgetter
from pathlib import Path

from sklearn import linear_model, model_selection


FEATURE_COLUMNS = ["TF-IDF", "Okapi TF", "BM25", "Laplace", "Jelinek-Mercer"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train a linear ranker from the feature matrix.")
    parser.add_argument("--input-csv", default="staticFeatureMatrix.csv",
                        help="Input feature matrix CSV file.")
    parser.add_argument(
        "--output", default="trainingperformance.txt", help="Output TREC run file.")
    parser.add_argument("--folds", type=int, default=5,
                        help="Number of cross-validation folds.")
    return parser


def load_feature_matrix(csv_path: str | Path):
    qd_ids = []
    features = []
    labels = []

    with open(csv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            qd_ids.append(row["QID-DocID"])
            features.append([float(row[column] or 0.0)
                            for column in FEATURE_COLUMNS])
            labels.append(float(row["Label"] or 0.0))

    return qd_ids, features, labels


def create_result_dict(qd_ids, predictions):
    result = defaultdict(list)
    for qd_id, prediction in zip(qd_ids, predictions):
        query_id, doc_id = qd_id.split("-", 1)
        result[query_id].append((doc_id, float(prediction)))
    return result


def sort_result_dict(result_dict):
    for query_id in result_dict:
        result_dict[query_id] = sorted(
            result_dict[query_id], key=itemgetter(1), reverse=True)
    return result_dict


def write_trec_run(result_dict, output_path):
    with open(output_path, "w", encoding="utf-8") as handle:
        for query_id, ranked_docs in result_dict.items():
            for rank, (doc_id, score) in enumerate(ranked_docs, start=1):
                handle.write(
                    f"{query_id} Q0 {doc_id} {rank} {score:.6f} Exp\n")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    qd_ids, features, labels = load_feature_matrix(args.input_csv)

    kfold = model_selection.KFold(
        n_splits=args.folds, shuffle=True, random_state=42)
    run_rows = []

    for train_index, test_index in kfold.split(features, labels):
        model = linear_model.LinearRegression()
        train_features = [features[index] for index in train_index]
        train_labels = [labels[index] for index in train_index]
        test_features = [features[index] for index in test_index]
        model.fit(train_features, train_labels)
        predictions = model.predict(test_features)
        test_qd_ids = [qd_ids[index] for index in test_index]
        run_rows.extend(zip(test_qd_ids, predictions))

    result_dict = create_result_dict([qd_id for qd_id, _ in run_rows], [
                                     score for _, score in run_rows])
    result_dict = sort_result_dict(result_dict)
    write_trec_run(result_dict, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
