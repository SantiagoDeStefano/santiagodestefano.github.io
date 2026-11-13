import numpy as np

class DBSCAN:
    def __init__(self, eps=0.5, min_samples=5):
        # neighborhood radius
        self.eps = eps
        # min points (incl. itself) to be a core point
        self.min_samples = min_samples

    def get_neighbors(self, X, i):
        # indices of all points within eps of point i (includes i itself)
        dists = np.sqrt(np.sum((X - X[i]) ** 2, axis=1))
        return np.where(dists <= self.eps)[0]

    def fit(self, X: np.ndarray):
        n = X.shape[0]
        self.labels = np.full(n, -1)      # -1 = noise (until proven otherwise)
        visited = np.zeros(n, dtype=bool)
        cluster_id = 0

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            neighbors = self.get_neighbors(X, i)

            # not enough neighbors -> not a core point, leave as noise for now
            if len(neighbors) < self.min_samples:
                continue

            # core point -> start a new cluster and grow it
            self.labels[i] = cluster_id
            queue = list(neighbors)

            while queue:
                j = queue.pop()

                # noise point reached by cluster -> it's a border point
                if self.labels[j] == -1:
                    self.labels[j] = cluster_id

                if visited[j]:
                    continue
                visited[j] = True

                j_neighbors = self.get_neighbors(X, j)

                # j is also core -> keep expanding through its neighbors
                if len(j_neighbors) >= self.min_samples:
                    queue.extend(j_neighbors)

            cluster_id += 1

        return self.labels