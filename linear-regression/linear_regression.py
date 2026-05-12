import numpy as np

class Value:
    """
    Stores a value and its gradient.
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
    b.grad += np.sum(dout, axis = 0)


def mse_forward(y_pred: Value, y_true: Value):
    """
    MSE Loss Function \n
    L = (1/n) * sum((y_pred - y_true)^2)
    """
    diff = y_pred.data - y_true.data
    loss = np.mean(diff ** 2)
    return loss, diff

def mse_backward(y_pred: Value, diff: Value, n: int):
    """
    dL/dy_pred = (2/n) * (y_pred - y_true)
    """
    return (2.0/n) * diff

# Training Loop
np.random.seed(42)

# Pre-defined synthetic data with relationship: y = 3x1 + 5x2 + 7 + noise
n_samples, n_features = 200, 2
X_data = np.random.randn(n_samples, n_features)
y_data = X_data @ np.array([[3.0], [5.0]]) + 7.0 + np.random.randn(n_samples, 1) * 0.5

# Weight initializer
W = Value(np.random.rand(n_features, 1) * 0.01)
b = Value(np.zeros((1, 1)))

lr = 0.01
epoches = 300

for epoch in range(epoches):
    # Forward pass
    X = Value(X_data)
    y = Value(y_data)

    Z = matmul_forward(X, W)
    y_pred = add_forward(Z, b)
    loss, diff = mse_forward(y_pred, y)

    # Backward pass
    # Zero grad
    W.grad = np.zeros_like(W.data)
    b.grad = np.zeros_like(b.data)
    Z.grad = np.zeros_like(Z.data)
    y_pred.grad = np.zeros_like(y_pred.data)

    # Chain rule
    # Step 1: dL/dy_pred
    y_pred.grad = mse_backward(y_pred, diff, n_samples)

    # Step 2: backprop through add (y_pred = Z + b)
    add_backward(Z, b, y_pred.grad)

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
print(f"True:     W = [3, 5],              b = [7]")
