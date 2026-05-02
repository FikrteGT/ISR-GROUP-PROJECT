import re
import os
import matplotlib.pyplot as plt

SUMMARY_FILE = "cacm_evaluation_summary.txt"
OUT_DIR = "cacm_outputs"
OUT_PNG = os.path.join(OUT_DIR, "metrics_summary.png")


def parse_summary(path):
    text = open(path, "r", encoding="utf-8").read()
    pattern = r"(\S+):\s*MAP\s*=\s*([0-9.]+)\s*;\s*nDCG@10\s*=\s*([0-9.]+)\s*;\s*P@10\s*=\s*([0-9.]+)"
    matches = re.findall(pattern, text)
    results = {}
    for name, mapv, ndcg, p10 in matches:
        results[name] = {
            "MAP": float(mapv),
            "nDCG@10": float(ndcg),
            "P@10": float(p10),
        }
    return results


def plot_results(results):
    if not results:
        print("No results found in", SUMMARY_FILE)
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    labels = list(results.keys())
    maps = [results[k]["MAP"] for k in labels]
    ndcgs = [results[k]["nDCG@10"] for k in labels]
    p10s = [results[k]["P@10"] for k in labels]

    x = range(len(labels))
    width = 0.22

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([i - width for i in x], maps, width, label="MAP")
    ax.bar(x, ndcgs, width, label="nDCG@10")
    ax.bar([i + width for i in x], p10s, width, label="P@10")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("CACM: Aggregated Evaluation Metrics by Run")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_PNG)
    print("Saved metrics plot to", OUT_PNG)


def main():
    if not os.path.exists(SUMMARY_FILE):
        print(SUMMARY_FILE,
              "not found. Run the pipeline first to generate evaluation summary.")
        return
    results = parse_summary(SUMMARY_FILE)
    plot_results(results)


if __name__ == "__main__":
    main()
