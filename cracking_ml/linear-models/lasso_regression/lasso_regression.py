import numpy as np


class Value:
    """
    Stores value and its gradient.
    """

    def __init__(self, data):
        self.data = np.array(data, dtype=np.float64)
        self.grad = np.zeros_like(self.data)
        pass

    def __rmul__(self, other):
        return self * other


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


def mse_lasso_forward(y_pred: Value, y_true: Value, W: Value, alpha: np.float64):
    """
    MSE Loss Function \n
    L = (1/n) * sum((y_pred - y_true)^2) + alpha * sum(abs(W))
    """
    diff = y_pred.data - y_true.data
    loss = np.mean(diff**2) + alpha * np.sum(np.abs(W.data))
    return loss, diff


def mse_lasso_backward(y_pred: Value, diff: np.ndarray, n: int, alpha: np.float64, W: Value):
    """
    dL/dy_pred = (2/n) * (y_pred - y_true) \n
    dL/dW_data = alpha * sign(W)
    """
    d_pred = (2.0 / n) * diff
    d_W = alpha * np.sign(W.data)
    return d_pred, d_W


# Training Loop
np.random.seed(42)

# Pre-defined synthetic data with relationship: y = 3x1 + 5x2 + 7 + noise
n_samples, n_features = 200, 3

# Correlated features
x1 = np.random.rand(n_samples, 1)
x2 = x1 + np.random.randn(n_samples, 1) * 0.001  # near-duplicate
x3 = x1 * 2 + np.random.randn(n_samples, 1) * 0.001  # another collinear feature

X_data = np.hstack([x1, x2, x3])
y_data = (
    X_data @ np.array([[3.0], [5.0], [2.0]]) + 7.0 + np.random.randn(n_samples, 1) * 2.0
)

# Weight initializer
W = Value(np.random.rand(n_features, 1) * 0.01)
b = Value(np.zeros((1, 1)))

lr = 0.01
epoches = 300
alpha = 0.1

n_train = 160
X_train, X_val = X_data[:n_train], X_data[n_train:]
y_train, y_val = y_data[:n_train], y_data[n_train:]


def train(X_tr, y_tr, alpha, epochs=300, lr=0.01):
    W = Value(np.random.rand(n_features, 1) * 0.01)
    b = Value(np.zeros((1, 1)))
    X = Value(X_tr)
    y = Value(y_tr)

    for epoch in range(epochs):
        # Forward pass
        Z = matmul_forward(X, W)
        y_pred = add_forward(Z, b)
        loss, diff = mse_lasso_forward(y_pred, y, W, alpha)

        # Backward pass
        # Zero grad
        W.grad = np.zeros_like(W.data)
        b.grad = np.zeros_like(b.data)
        Z.grad = np.zeros_like(Z.data)
        y_pred.grad = np.zeros_like(y_pred.data)

        # Chain rule
        # Step 1: dL/dy_pred
        y_pred.grad, dW_reg = mse_lasso_backward(y_pred, diff, X_tr.shape[0], alpha, W)

        # Step 2: backprop through add (y_pred = Z + b)
        add_backward(Z, b, y_pred.grad)

        # Step 3: backprop through matmul (Z = X @ W)
        matmul_backward(X, W, Z.grad)
        W.grad += dW_reg  # add ridge regularization gradient

        # Gradient Descent
        W.data -= lr * W.grad
        b.data -= lr * b.grad

        if epoch % 50 == 0:
            print(
                f"Epoch {epoch:3d} | Loss: {loss:.4f} | W: {W.data.flatten()} | b: {b.data.flatten()}"
            )

    return W, b


def val_mse(W, b, X_v, y_v):
    Z = matmul_forward(Value(X_v), W)
    y_pred = add_forward(Z, b)
    return np.mean((y_pred.data - y_v) ** 2)


alphas = np.logspace(-12, 2, num=11)
best_alpha, best_val = None, float("inf")

for a in alphas:
    W_a, b_a = train(X_train, y_train, alpha=a)
    v = val_mse(W_a, b_a, X_val, y_val)
    print(f"alpha={a}: val_loss={v:.4f}")
    if v < best_val:
        best_val, best_alpha = v, a

print(f"\nBest alpha: {best_alpha}, val_loss={best_val:.4f}")

# Lasso (best_alpha)
W_lasso, b_lasso = train(X_train, y_train, alpha=best_alpha)
val_loss_lasso = val_mse(W_lasso, b_lasso, X_val, y_val)

# Plain linear regression (alpha=0, no regularization)
W_lin, b_lin = train(X_train, y_train, alpha=0.0)
val_loss_lin = val_mse(W_lin, b_lin, X_val, y_val)

print(
    f"Lasso  -> W={W_lasso.data.flatten()}, b={b_lasso.data.flatten()}, val_loss={val_loss_lasso:.4f}"
)
print(
    f"Linear -> W={W_lin.data.flatten()}, b={b_lin.data.flatten()}, val_loss={val_loss_lin:.4f}"
)
