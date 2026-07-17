import numpy as np
import matplotlib.pyplot as plt


class Value:
    """
    Stores value and its gradient.
    """

    def __init__(self, data):
        self.data = np.array(data, dtype=np.float64)
        self.grad = np.zeros_like(self.data)
        pass


def matmul_forward(X: Value, W: Value):
    """
    Z = X @ W
    """
    out = Value(X.data @ W.data)
    return out


def matmul_backward(X: Value, W: Value, dout: np.ndarray):
    """
    dL/dX = dout @ W^T, dL/dW = X^T @ dout
    """
    X.grad += dout @ W.data.T
    W.grad += X.data.T @ dout


def add_forward(Z: Value, b: Value):
    """
    out = Z + b (b is boardcast)
    """
    out = Value(Z.data + b.data)
    return out


def add_backward(Z: Value, b: Value, dout: np.ndarray):
    """
    dL/dZ = dout, dL/db = sum over batch dim
    """
    Z.grad += dout
    b.grad += np.sum(dout, axis=0)


def softmax_forward(Z: Value):
    """
    softmax(z_i) = e^{z_i} / sum(e^{z_j})
    """
    exp_z = np.exp(Z.data)
    probs = exp_z / np.sum(exp_z, axis=1, keepdims=True)
    return Value(probs)


def softmax_cross_entropy_forward(y_pred: Value, y_true: Value):
    """
    L = -mean( sum( y_true * log( y_pred + eps ) ))
    """
    eps = 1e-7
    loss = -np.mean(np.sum(y_true.data * np.log(y_pred.data + eps), axis=1))
    return loss


def softmax_cross_entropy_backward(y_pred: Value, y_true: Value, n: int):
    """
    dL/dZ = (y_pred - y_true) / n
    """
    return (y_pred.data - y_true.data) / n

# Training Loop
np.random.seed(42)

# Binary labels: 1 if y > 0, else 0
# Multi-class labels (3 classes), one-hot encoded
n_samples, n_features, n_classes = 200, 2, 3
X_data = np.random.randn(n_samples, n_features)
scores = X_data @ np.array([[1, 0, -1], [0, 1, -1]])
raw_labels = np.argmax(scores, axis=1)
y_data = np.eye(n_classes)[raw_labels]

# Weight initializer
W = Value(np.random.rand(n_features, n_classes) * 0.01)
b = Value(np.zeros((1, n_classes)))

lr = 0.0001
epoches = 1000

for epoch in range(epoches):
    # Forward pass
    X = Value(X_data)
    y = Value(y_data)

    Z = matmul_forward(X, W)
    A = add_forward(Z, b)
    y_pred = softmax_forward(A)
    loss = softmax_cross_entropy_forward(y_pred, y)

    # Backward pass
    # Zero grads
    W.grad = np.zeros_like(W.data)
    b.grad = np.zeros_like(b.data)
    Z.grad = np.zeros_like(Z.data)
    A.grad = np.zeros_like(A.data)

    # Chain rule
    # Step 1: dL/dA
    A.grad = softmax_cross_entropy_backward(y_pred, y, n_samples)

    # Step 2: backprop through add (A = Z + b)
    add_backward(Z, b, A.grad)

    # Step 3: backprop through add (Z = X @ W)
    matmul_backward(X, W, Z.grad)

    # Gradient Descent
    W.data -= lr * W.grad
    b.data -= lr * b.grad

    if epoch % 50 == 0:
        print(
            f"Epoch {epoch:3d} | Loss: {loss:.4f} | W: {W.data.flatten()} | b: {b.data.flatten()}"
        )

print(f"\nLearned:  W = {W.data.flatten()}, b = {b.data.flatten()}")

# Accuracy
Z_final = matmul_forward(Value(X_data), W)
A_final = add_forward(Z_final, b)
y_probs = softmax_forward(A_final)
pred_classes = np.argmax(y_probs.data, axis=1)
true_classes = np.argmax(y_data, axis=1)
accuracy = np.mean(pred_classes == true_classes)
print(f"Accuracy: {accuracy:.2%}")
