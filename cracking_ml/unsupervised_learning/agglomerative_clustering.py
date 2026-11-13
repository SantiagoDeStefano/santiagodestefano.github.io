import numpy as np

def agglomerative(X: np.ndarray, k):
    clusters = [ [i] for i in range(len(X)) ]

    while len(clusters) > k:
        best = (None, None, float("inf"))
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                # Single linkage: closest pair between the 2 clusters
                d = min(np.linalg.norm(X[i] - X[j]) for i in clusters[a] for j in clusters[b])
                if d < best[2]:
                    best = (a, b, d)
        
        a, b, _ = best
        # merge b into a
        clusters[a] += clusters[b]
        clusters.pop(b)

    labels = np.zeros(len(X), dtype=int)
    for c, members in enumerate(clusters):
        labels[members] = c
    return labels