import math
import time

class Page:
    def __init__(self, page):
        self.page = page
        self.auth = 1.0
        self.hub = 1.0
        self.inLinks = set()
        self.outLinks = set()

graphPages = {}

# ----------------------------
# LOAD GRAPH
# ----------------------------
with open("linkgraph.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        if not parts:
            continue

        page = parts[0]
        outlinks = parts[1:]

        if page not in graphPages:
            graphPages[page] = Page(page)

        for ol in outlinks:
            if ol not in graphPages:
                graphPages[ol] = Page(ol)

            graphPages[page].outLinks.add(ol)
            graphPages[ol].inLinks.add(page)

print("Pages loaded:", len(graphPages))

# ----------------------------
# HITS ITERATION
# ----------------------------
def get_top_k(scores, k=10):
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

def compare_topk(old, new, k=10):
    old_top = set([x[0] for x in get_top_k(old, k)])
    new_top = set([x[0] for x in get_top_k(new, k)])
    overlap = len(old_top.intersection(new_top))
    return overlap / k
    print("Top-K stability:", compare_topk(prev_scores, current_scores))
def hits_iteration():
    norm = 0

    # update authority
    for p in graphPages.values():
        p.auth = sum(graphPages[q].hub for q in p.inLinks)
        norm += p.auth ** 2

    norm = math.sqrt(norm) if norm != 0 else 1

    for p in graphPages.values():
        p.auth /= norm

    # update hub
    norm = 0
    for p in graphPages.values():
        p.hub = sum(graphPages[q].auth for q in p.outLinks)
        norm += p.hub ** 2

    norm = math.sqrt(norm) if norm != 0 else 1

    for p in graphPages.values():
        p.hub /= norm

# ----------------------------
# RUN
# ----------------------------
start = time.time()

for _ in range(20):
    hits_iteration()

# ----------------------------
# SAVE RESULTS
# ----------------------------
with open("authority.txt", "w") as f:
    for p in sorted(graphPages.values(), key=lambda x: x.auth, reverse=True)[:50]:
        f.write(f"{p.page} {p.auth}\n")

with open("hub.txt", "w") as f:
    for p in sorted(graphPages.values(), key=lambda x: x.hub, reverse=True)[:50]:
        f.write(f"{p.page} {p.hub}\n")

print("Done. Runtime:", time.time() - start)