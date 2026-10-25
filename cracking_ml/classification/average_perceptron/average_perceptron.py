import numpy as np

class AveragePerceptron:
    def __init__(self):
        pass

    def train(self, X: np.ndarray, y: np.ndarray):
        # W is (2,)
        self.W = np.zeros(X.shape[1])
        self.b = 0.0
        W_sum = np.zeros(X.shape[1])
        b_sum = 0.0

        for epoch in range(epoches):
            for x, yi in zip(X, y):
                y_pred = self.W @ x + self.b
                if np.sign(y_pred) != yi:
                    self.W = self.W + lr * yi * x
                    self.b = self.b + lr * yi
                W_sum += self.W
                b_sum += self.b

        # Sum / the total iteration that W_sum got added up
        self.W = W_sum / (epoches * len(X))
        self.b = b_sum / (epoches * len(X))

    def predict(self, X: np.ndarray):
        preds = []
        for x in X:
            pred = np.sign(self.W @ x + self.b)
            preds.append(pred)
        return preds

lr = 0.01
epoches = 100

X_train = np.random.rand(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 1, -1, 1)
X_test = np.random.rand(100, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 1, -1, 1)

model = AveragePerceptron()
model.train(X_train, y_train)
preds = model.predict(X_test)
print(np.mean(preds == y_test))