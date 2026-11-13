import numpy as np

class Node:
    def __init__(self, feature=None, threshold=None, left=None, right=None, value=None):
        # Which column to split on
        self.feature = feature 
        # Split value
        self.threshold = threshold
        # X[features] <= threshold
        self.left = left
        # X[features] > threshold
        self.right = right
        # Class label if leaf
        self.value = value

class DecisionTreeClassifier:
    def __init__(self, max_depth = 5, min_samples_split = 2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split

    def mse(self, y):
        return np.mean((y - np.mean(y)) ** 2)

    def best_split(self, X, y):
        best_gain = 0
        best_feature, best_threshold = None, None
        parent_mse = self.mse(y)
        n = len(y)

        for j in range(X.shape[1]):
            for t in np.unique(X[:, j]):
                left = X[:, j] <= t
                right = ~left
                if left.sum() == 0 or right.sum() == 0:
                    continue

                # Weighted mse of children
                child_mse = (left.sum() / n) * self.mse(y[left]) + \
                            (right.sum() / n) * self.mse(y[right])

                gain = parent_mse - child_mse
                if(gain > best_gain):
                    best_gain = gain
                    best_feature, best_threshold = j, t

        return best_feature, best_threshold

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.root = self.build(X, y, 0)

    def predict_one(self, x, node):
        if node.value is not None:
            return node.value
        if x[node.feature] <= node.threshold:
            return self.predict_one(x, node.left)
        return self.predict_one(x, node.right)

    def predict(self, X_test: np.ndarray):
        return np.array([self.predict_one(x, self.root) for x in X_test])
