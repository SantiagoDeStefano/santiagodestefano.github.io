import numpy as np

def kmeans_plus_plus_init(X: np.ndarray, k: int):
    n = X.shape[0]
    centroids = []

    # Step 1: first centroid = random point
    first = np.random.randint(n)
    centroids.append(X[first])

    for _ in range(k - 1):
        # Step 2: for each point, squared distance to its NEAREST centroid so far
        dists = []
        for x in X:
            d = min(np.sum((x - c) ** 2) for c in centroids)
            dists.append(d)
        dists = np.array(dists)

        # Step 3: pick next centroid with probability distance^2
        probs = dists / np.sum(dists)
        next_idx = np.random.choice(n, p=probs)
        centroids.append(X[next_idx])

    return np.array(centroids)