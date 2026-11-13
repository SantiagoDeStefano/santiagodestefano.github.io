import numpy as np

class Stump:
    # Tree with 1 split: x[feature] <= threshold -> predict polarity, else -polarity
    def __init__(self):
        self.feature = None
        self.threshold = None
        self.polarity = 1
        # How much this stump's vote counts
        self.alpha = None

    def predict(self, X):
        preds = np.ones(X.shape[0])
        left = X[:, self.feature] <= self.threshold
        preds[left] = self.polarity
        preds[~left] = -self.polarity
        return preds

class AdaBoost:
    def __init__(self, n_estimators = 50):
        self.n_estimators = n_estimators

    def fit(self, X: np.ndarray, y: np.ndarray):
        # labels -1 / +1
        y = np.where(y <= 0, -1, 1)
        n = X.shape[0]

        # Start: every sample equally important
        w = np.ones(n) / n
        self.stumps = []

        for _ in range(self.n_estimators):
            stump = Stump()
            best_err = float('inf')

            # Find best stump using weighted error
            for j in range(X.shape[1]):
                for t in np.unique(X[:, j]):
                    for polarity in [1, -1]:
                        preds = np.where(X[:, j] <= t, polarity, -polarity)

                        # Weighted error = sum of weights of wrong samples
                        err = np.sum(w[preds != y])

                        if err < best_err:
                            best_err = err
                            stump.feature, stump.threshold, stump.polarity = j, t, polarity

            # Stump's vote power: low error -> big alpha
            eps = 1e-10
            stump.alpha = 0.5 * np.log((1 - best_err + eps) / (best_err + eps))

            # Update weights: wrong samples get heavier, right ones lighter
            preds = stump.predict(X)
            w *= np.exp(-stump.alpha * y * preds)
            # Normalize so weights sum to 1
            w /= np.sum(w)

            self.stumps.append(stump)

    def predict(self, X_test: np.ndarray):
        # Weighted vote of all stumps
        score = np.zeros(X_test.shape[0])
        for stump in self.stumps:
            score += stump.alpha * stump.predict(X_test)
        return np.where(score >= 0, 1, -1)
