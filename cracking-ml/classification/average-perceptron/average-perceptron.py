import numpy as np

class AveragePerceptron:
    def __init__(self):
        pass

    def fit(self, X: np.array, y: np.array):
        # W should be (n_features, value)
        self.W = np.zeros(X.shape[1])
        self.b = 0.0

        for epoch in range(epoches):
            for x, yi in zip(X, y):
                correct = self.W @ x + self.b
                if np.sign(correct) != yi:
                    # use true y value to steer the W
                    self.W = self.W + lr * yi * x
                    self.b = self.b + lr * yi
                print(f"Epoch: {epoch} Distance from true y: {abs(correct - yi)}")

    def predict(self, X_test: np.array):
        preds = []
        for x in X_test:
            y_pred = np.sign(self.W @ x + self.b)
            preds.append(y_pred)
        return np.array(preds)

epoches = 10
lr = 0.01

# Training Loop
np.random.seed(42)
X_train = np.random.randn(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, -1, 1)
X_test = np.random.randn(1000, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, -1, 1)

model = AveragePerceptron()
model.fit(X_train, y_train)
preds = model.predict(X_test)
print(preds)
print(np.mean(preds == y_test))
