import numpy as np

class SVM:
    def __init__(self):
        pass

    def fit(self, X: np.ndarray, y: np.ndarray):
        # As X is (n_rows, n_features) so we want W to be (n_features,)
        self.W = np.zeros(X.shape[1])
        self.b = 0.0
        self.z = np.zeros(X.shape[0])
        self.J = np.zeros(X.shape[0])
        self.u = np.zeros(X.shape[0])
        self.Z = np.zeros((X.shape[0], X.shape[1]))

        for epoch in range(epoches):
            for n, (x, yi) in enumerate(zip(X, y)):
                self.Z[n] = yi * x
                self.u[n] = (yi * (self.W.T @ x + self.b)) if (yi * (self.W.T @ x + self.b)) < 1 else 0
                self.J[n] = max(0, 1 - self.u[n])

            H = self.u < 1

            self.W -= lr * (np.sum(-self.Z[H], axis = 0) + lambda_l2*self.W)
            self.b -= lr * np.sum(-y[H])

            hinge_loss = np.sum(self.J) + lambda_l2 / 2 * np.sum(np.square(self.W))
            print("Epoch: ", epoch, "Loss: ", hinge_loss)

    def predict(self, X_test: np.ndarray):
        preds = []
        for x in X_test:
            y_pred = x @ self.W + self.b
            preds.append(1 if y_pred >= 0 else -1)
        return np.array(preds)

lr = 0.1
epoches = 1000
lambda_l2 = 0.01
X_train = np.random.randn(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, 0)
X_test = np.random.rand(50, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)

model = SVM()
model.fit(X_train, y_train)
preds = model.predict(X_test)
y_test_ = np.where(y_test <= 0, -1, 1)
print(preds)
print(np.mean(preds == y_test_))
