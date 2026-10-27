import numpy as np

class GaussianNB:
    def __init__(self):
        pass

    def train(self, X: np.ndarray, y: np.ndarray):
        self.mean = {}
        self.std = {}
        self.priors = {}
        self.classes = np.unique(y)
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis=0)
            self.std[c] = np.std(X_c, axis=0)
            self.priors[c] = X_c.shape[0]/X.shape[0]

    def predict(self, X: np.ndarray):
        preds = []
        for x in X:
            posteriors = []
            for c in self.classes:
                pdf = (1/(self.std[c] * np.sqrt(2*np.pi))) * np.exp(-1/2 * ((x - self.mean[c])/self.std[c])**2)
                posterior = np.sum(np.log(pdf)) + np.log(self.priors[c])
                posteriors.append(posterior)
            preds.append(self.classes[np.argmax(posteriors)])
        return preds

np.random.seed(42)
X_train = np.random.rand(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, 0)
X_test = np.random.rand(100, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)

model = GaussianNB()
model.train(X_train, y_train)
preds = model.predict(X_test)
print(np.sum(preds == y_test)/len(y_test))
