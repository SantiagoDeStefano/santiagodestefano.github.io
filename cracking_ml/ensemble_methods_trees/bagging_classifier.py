import numpy as np
from cracking_ml.ensemble_methods_trees.decision_tree_classifier import DecisionTreeClassifier

class BaggingClassifier:
    def __init__(self, n_estimators = 10, max_depth = None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth if max_depth is not None else 100

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.models = []
        n = X.shape[0]

        for _ in range(self.n_estimators):
            # Bootsrap: sample n rows with replacement
            idx = np.random.choice(n, n, replace=True)
            X_boot, y_boot = X[idx], y[idx]

            model = DecisionTreeClassifier(max_depth = self.max_depth)
            model.fit(X_boot, y_boot)
            self.models.append(model)

    def predict(self, X_test: np.ndarray):
        # Each tree votes -> shape (n_estimators, n_test)
        all_preds = np.array([model.predict(X_test) for model in self.models])

        # Majority vote per test sample (column)
        preds = []
        for col in all_preds.T:
            preds.append(np.bincount(col).argmax())
        return np.array(preds)