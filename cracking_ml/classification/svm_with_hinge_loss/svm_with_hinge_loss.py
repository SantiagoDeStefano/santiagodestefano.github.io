import numpy as np

class SVM:
    def __init__(self):
        pass

    def fit(self, X: np.ndarray, y: np.ndarray):
        # SVM needs label -1/+1 for steering
        y = np.where(y <= 0, -1, 1)

        # As X is (n_rows, n_features) we wanted W to be (n_features,)
        self.W = np.zeros(X.shape[1])
        self.b = 0.0
        n = X.shape[0]

        for epoch in range(epoches):
            # Derivate of W
            dW = np.zeros(X.shape[1])
            # Derivate of b
            db = 0.0
            # Loss
            loss = 0.0
            for x, yi in zip(X, y):
                # Calculate the margin, as self.W @ x + self.b
                # Is the raw scores, mutiply by yi for:
                # margin >= 1: safely far
                # 0 < margin < 1: correct but close, need a loss to push it further
                # margin < 0: wrong side, big loss
                margin = yi * (self.W @ x + self.b)

                # hinge = max(0, 1 - margin)
                # else: correct outside margin -> loss = 0, gradient = 0
                if margin < 1:
                    dW += -yi * x
                    db += -yi
                    loss += 1 - margin

                # Average over samples with L2 regularization
                dW = dW / n + 2 * lambda_l2 * self.W
                db = db / n
                loss = loss / n + lambda_l2 * np.sum(np.square(self.W))

                self.W -= lr * dW
                self.b -= lr * db

                if epoch % 100 == 0:
                    print("Epoch: ", epoch, "Loss: ", loss)


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
X_test = np.random.randn(50, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)

model = SVM()
model.fit(X_train, y_train)
preds = model.predict(X_test)
y_test_ = np.where(y_test <= 0, -1, 1)
print(preds)
print(np.mean(preds == y_test_))