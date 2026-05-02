import math

graph = {}
d = 0.85

with open("linkgraph.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        node = parts[0]
        links = parts[1:]
        graph[node] = links

N = len(graph)
rank = {n: 1/N for n in graph}

def pagerank(iterations=30):
    global rank

    for _ in range(iterations):
        new_rank = {n: (1-d)/N for n in graph}

        sink_rank = sum(rank[n] for n in graph if len(graph[n]) == 0)

        for n in graph:
            if len(graph[n]) == 0:
                continue
            share = rank[n] / len(graph[n])
            for l in graph[n]:
                if l in new_rank:
                    new_rank[l] += d * share

        for n in graph:
            new_rank[n] += d * sink_rank / N

        rank = new_rank

pagerank()

def topk(scores, k=10):
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

print("\nTOP 10 PAGERANK")
print(topk(rank))