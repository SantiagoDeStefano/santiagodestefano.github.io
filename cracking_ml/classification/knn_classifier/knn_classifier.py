import numpy as np

class KNN():
    def __init__(self, k):
        self.k = k
        pass
    
    def train(self):
        pass
    
    def predict(self, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray):
        preds = []
        for x in X_test:
            diff = np.sqrt(np.sum(np.square(x - X_train), axis = 1))
            k_idxes = np.argsort(diff)[0:self.k]
            k_labels = y_train[k_idxes]
            pred = np.bincount(k_labels).argmax()
            preds.append(pred)
        return preds

np.random.seed(42)
X_train = np.random.rand(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, 0)
X_test = np.random.rand(100, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 0, 1, 0)

model = KNN(3)
preds = model.predict(X_train, y_train, X_test)
print(np.sum(preds == y_test)/len(y_test))