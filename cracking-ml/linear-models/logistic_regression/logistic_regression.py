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

def add_forward(Z: Value, b: Value):
    """
    out = Z + b (b is boardcast)
    """
    out = Value(Z.data + b.data)
    return out

def sigmoid_forward(A: Value):
    """
    out = 1 / ( 1 + np.exp(-A.data) )
    """
    out = Value(1/(1 + np.exp(-A.data)))
    return out

def bce_forward(y_pred: Value, y_true: Value):
    """
    BCE Loss Function \n
    L = -np.mean( y_true * log(y_pred + eps) + (1 - y_true) * log(1 - y_pred + eps) )
    """
    eps = 1e-7
    loss = -np.mean(
        y_true.data * np.log(y_pred.data + eps) +
        (1 - y_true.data) * np.log(1- y_pred.data + eps)
    )
    return loss

def matmul_backward(X: Value, W: Value, dout: np.ndarray):
    """
    dL/dX = dout @ W^T, dL/dW = X^T @ dout
    """
    X.grad += dout @ W.data.T
    W.grad += X.data.T @ dout

def add_backward(Z: Value, b: Value, dout: np.ndarray):
    """
    dL/dZ = dout, dL/db = sum over batch dim
    """
    Z.grad += dout
    b.grad += np.sum(dout, axis=0)

def sigmoid_backward(A: Value, dout: np.ndarray):
    """
    dL/dA = sigmoid(A) * (1 - sigmoid(A)) * dout
    """
    sig = 1 / (1 + np.exp(-A.data))
    return sig * (1 - sig) * dout

def bce_backward(y_pred: Value, y_true: Value):
    """
    dL/dy_pred = 
    ( - (y_true.data / (y_pred.data + eps)) + (1 - y_true.data / (1 - y_pred.data + eps)) / n )
    """
    n = y_pred.data.shape[0]
    eps = 1e-7
    grad = (-(y_true.data / (y_pred.data + eps)) + 
            (1 - y_true.data) / (1 - y_pred.data + eps)) / n
    return grad


# Training Loop
np.random.seed(42)

# Binary labels: 1 if y > 0, else 0
n_samples, n_features = 200, 2
X_data = np.random.randn(n_samples, n_features)
y_data = (X_data @ np.array([[1.0], [1.0]]) > 0).astype(np.float64)

# Weight initializer
W = Value(np.random.rand(n_features, 1) * 0.01)
b = Value(np.zeros((1, 1)))

lr = 0.1
epoches = 1000

for epoch in range(epoches):
    # Forward pass
    X = Value(X_data)
    y = Value(y_data)

    Z = matmul_forward(X, W)
    A = add_forward(Z, b)
    y_pred = sigmoid_forward(A)
    loss = bce_forward(y_pred, y)

    # Backward pass
    # Zero grads
    W.grad = np.zeros_like(W.data)
    b.grad = np.zeros_like(b.data)
    Z.grad = np.zeros_like(Z.data)
    A.grad = np.zeros_like(A.data)
    y_pred.grad = np.zeros_like(y_pred.data)

    # Chain rule
    # Step 1: dL/dy_pred
    y_pred.grad = bce_backward(y_pred, y)

    # Step 2: dL/dA
    A.grad = sigmoid_backward(A, y_pred.grad)

    # Step 3: backprop through add (A = Z + b)
    add_backward(Z, b, A.grad)

    # Step 4: backprop through add (Z = X @ W)
    matmul_backward(X, W, Z.grad)

    # Gradient Descent
    W.data -= lr * W.grad
    b.data -= lr * b.grad

    if epoch % 50 == 0:
        print(
            f"Epoch {epoch:3d} | Loss: {loss:.4f} | W: {W.data.flatten()} | b: {b.data.flatten()}"
        )

print(f"\nLearned:  W = {W.data.flatten()}, b = {b.data.flatten()}")

# Final decision
X_final = Value(X_data)
Z_final = matmul_forward(X_final, W)
A_final = add_forward(Z_final, b)
y_probs = sigmoid_forward(A_final)

y_classes = (y_probs.data > 0.5).astype(int)
accuracy = np.mean(y_classes == y_data)
print(f"Accuracy: {accuracy:.2%}")

# Visualization
# 3D
x1 = np.linspace(-3, 3, 100)
x2 = np.linspace(-3, 3, 100)
xx1, xx2 = np.meshgrid(x1, x2)
X_mesh = np.c_[xx1.ravel(), xx2.ravel()]
Z_mesh = X_mesh @ W.data + b.data
A = 1 / (1 + np.exp(-Z_mesh))
A = A.reshape(xx1.shape)

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

ax.plot_surface(xx1, xx2, A, cmap="RdBu", alpha=0.7)
ax.set_xlabel("x1")
ax.set_ylabel("x2")
ax.set_zlabel("P(y=1)")
plt.title("Sigmoid Surface")
plt.show()

# 2D
x1 = np.linspace(-3, 3, 100)
x2 = np.linspace(-3, 3, 100)
xx1, xx2 = np.meshgrid(x1, x2)

X_mesh = np.c_[xx1.ravel(), xx2.ravel()]
Z = X_mesh @ W.data + b.data
A = 1 / (1 + np.exp(-Z))
A = A.reshape(xx1.shape)

plt.contourf(xx1, xx2, A, levels=50, cmap="RdBu", alpha=0.6)
plt.contour(xx1, xx2, A, levels=[0.5], colors="black")  # decision boundary
plt.scatter(X_data[:, 0], X_data[:, 1], c=y_data.ravel(), cmap="RdBu", edgecolors="k")
plt.title("Decision Boundary")
plt.xlabel("x1")
plt.ylabel("x2")
plt.show()
