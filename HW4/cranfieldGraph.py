import math

graph = {}
auth = {}
hub = {}

# Load graph
with open("linkgraph.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        node = parts[0]
        links = parts[1:]
        graph[node] = links
        auth[node] = 1.0
        hub[node] = 1.0

def normalize(scores):
    norm = math.sqrt(sum(v*v for v in scores.values()))
    if norm == 0:
        return scores
    return {k: v/norm for k, v in scores.items()}

def hits(iterations=20):
    global auth, hub

    for _ in range(iterations):
        new_auth = {n: 0 for n in graph}
        new_hub = {n: 0 for n in graph}

        for n in graph:
            for l in graph[n]:
                if l in new_auth:
                    new_auth[l] += hub[n]

        for n in graph:
            for l in graph[n]:
                if l in new_hub:
                    new_hub[n] += auth[l]

        auth = normalize(new_auth)
        hub = normalize(new_hub)

hits()

def topk(scores, k=10):
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

print("\nTOP 10 AUTHORITY")
print(topk(auth))

print("\nTOP 10 HUB")
print(topk(hub))