import numpy as np

class KNN:
    def __init__(self, k: int):
        self.k = k

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.X_train = X
        self.y_train = y

    def predict(self, X_test: np.ndarray):
        preds = []
        for x in X_test:
            diff = np.sqrt(np.sum(np.square(x - self.X_train), axis = 1))
            k_idx = np.argsort(diff)[:self.k]
            k_labels = self.y_train[k_idx]
            preds.append(np.bincount(k_labels).argmax())
        return np.array(preds)

np.random.seed(42)
# Train set to compute diff
X_train = np.random.randn(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, 0)

# Test set for inference
X_test = np.random.randn(50, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)


# Choose "k" by try a bunch of different values and compare its metric - between train/val/test set, between 1 and 20 for example.
model = KNN(k = 3)
model.fit(X_train, y_train)
preds = model.predict(X_test)
print(preds, np.mean(preds == y_test))
