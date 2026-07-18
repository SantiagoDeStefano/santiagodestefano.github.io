import numpy as np

class LinearDA:
    def __init__(self):
        pass

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.mean = {}
        self.classes = np.unique(y)
        n_features = X.shape[1]
        S_W = np.zeros((n_features, n_features))
        S_B = np.zeros((n_features, n_features))
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis = 0)
            diff = X_c - self.mean[c]
            S_W += diff.T @ diff    

        self.mean_all = np.mean(X, axis = 0)
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis = 0)
            diff = np.mean(X_c, axis = 0) - self.mean_all
            S_B += X_c.shape[0] * np.outer(diff, diff)

        eigvals, eigvecs = np.linalg.eig(np.linalg.inv(S_W) @ S_B)
        idx = np.argsort(eigvals)[::-1]
        W = eigvecs[:, idx[: len(self.classes) - 1]]
        self.W = W

    def predict(self, X):
        X_proj = X @ self.W
        centroids = {c: self.mean[c] @ self.W for c in self.classes}
        preds = []
        for x in X_proj:
            dists = {c: np.linalg.norm(x - centroids[c]) for c in self.classes}
            preds.append(min(dists, key=lambda k: dists[k]))
        return np.array(preds)

np.random.seed(42)
X_train = np.random.randn(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, 0)
X_test = np.random.rand(50, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)

model = LinearDA()
model.fit(X_train, y_train)
preds = model.predict(X_test)
print(preds)
print(np.mean(preds == y_test))
