queries = ['1', '5', '10', '13', '23']
files = {
    'ES Built-in': r'C:\Information-Retrieval\HW1\results_bm25.txt',
    'TF-IDF':      r'C:\Information-Retrieval\HW1\TFIDF_Results_File.txt',
    'BM25':        r'C:\Information-Retrieval\HW1\BM25_Results_File.txt',
    'LM Jelinek':  r'C:\Information-Retrieval\HW1\JelinekMercer_Results_File.txt',
}

for qid in queries:
    print(f"\n========== Query {qid} ==========")
    print(f"{'Rank':<6} {'ES Built-in':<12} {'TF-IDF':<12} {'BM25':<12} {'LM Jelinek':<12}")
    print("-" * 54)

    results = {}
    for model, filepath in files.items():
        docs = []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3 and parts[0] == qid:
                    docs.append(parts[2])
                if len(docs) == 10:
                    break
        results[model] = docs

    for rank in range(10):
        row = f"{rank+1:<6}"
        for model in files:
            doc = results[model][rank] if rank < len(results[model]) else 'N/A'
            row += f" {doc:<12}"
        print(row)
