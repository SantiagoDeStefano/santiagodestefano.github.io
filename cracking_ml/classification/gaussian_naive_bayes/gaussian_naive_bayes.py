import numpy as np

class GaussianNB:
    def __init__(self):
        pass

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.mean = {}
        self.std = {}
        self.priors = {}
        self.classes = np.unique(y)
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis = 0)
            self.std[c] = np.std(X_c, axis = 0)
            self.priors[c] = X_c.shape[0] / X.shape[0]

    def predict(self, X_test: np.ndarray):
        preds = []
        for x in X_test:
            posteriors = []
            for c in self.classes:
                pdf = (1/(np.sqrt(2*np.pi)*self.std[c])) * np.exp(-((x-self.mean[c])**2)/(2*self.std[c]**2))
                # We can do np.prod(pdf) but with many features would make it near zero; log() is safer
                likelihood = np.sum(np.log(pdf))
                posterior = likelihood + np.log(self.priors[c])
                posteriors.append(posterior)
            preds.append(self.classes[np.argmax(posteriors)])
        return np.array(preds)

np.random.seed(42)
X_train = np.random.randn(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, 0)
X_test = np.random.randn(800, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)

model = GaussianNB()
model.fit(X_train, y_train)
preds = model.predict(X_test)
print(preds)
print(np.mean(preds == y_test))
