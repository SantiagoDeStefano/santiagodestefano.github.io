import numpy as np

class KMeans:
    def __init__(self, k=3, max_iters=100):
        self.k = k
        self.max_iters = max_iters

    def fit(self, X: np.ndarray):
        n = X.shape[0]

        # Step 1: pick k random points as starting centroids
        idx = np.random.choice(n, self.k, replace=False)
        self.centroids = X[idx]

        for it in range(self.max_iters):
            # Step 2: assign each point to the nearest centroid
            labels = []
            for x in X:
                dist = [np.sum((x - c) ** 2) for c in self.centroids]
                labels.append(np.argmin(dist))
            labels = np.array(labels)

            # Step 3: move each centroid to the mean of its point
            new_centroids = []
            for j in range(self.k):
                points = X[labels == j]
                if len(points) == 0:          # empty cluster -> keep old centroid
                    new_centroids.append(self.centroids[j])
                else:
                    new_centroids.append(points.mean(axis=0))
            new_centroids = np.array(new_centroids)

            # Step 4: stop if centroids didn't move
            if np.allclose(new_centroids, self.centroids):
                break
            self.centroids = new_centroids

        self.labels = labels

        # inertia = total squared distance to own centroid (lower = tighter clusters)
        self.inertia = np.sum((X - self.centroids[labels]) ** 2)

    def predict(self, X_test: np.ndarray):
        preds = []
        for x in X_test:
            dists = [np.sum((x - c) ** 2) for c in self.centroids]
            preds.append(np.argmin(dists))
        return np.array(preds)
