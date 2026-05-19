---
title: "Logistic Regression from Scratch with Backpropagation"
date: 2026-05-20
---

# Logistic Regression from Scratch with Backpropagation

## What is Logistic Regression?

A machine learning algorithm used for **classification** - supervised learning. Instead of predicting a number like linear regression, it predicts a **probability** (0 to 1): is this data point class 0 or class 1?

## The Math

It looks just like linear regression:

$$
z = XW + b
$$

Then we apply **sigmoid** to squash the output into a probability between 0 and 1:

$$
p = \frac{1}{1 + e^{-z}}
$$

Full formula:

$$
p(y=1 \mid x) = \frac{1}{1 + e^{-(XW + b)}}
$$

The decision rule: if `p > 0.5` → class 1, else → class 0. The 0.5 threshold can be adjusted depending on your problem.

## The Code

```python
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
```

## How It Actually Works

### 1. Forward Pass

Same as linear regression, but with one new step - applying sigmoid after the linear part:

- `Z = X @ W` - multiply inputs by weights
- `A = Z + b` - add bias
- `y_pred = sigmoid(A)` - squash output to probability (0 to 1)
- `loss = BCE(y_pred, y)` - measure how wrong the prediction is

### 2. BCE Loss Function

This model uses **Binary Cross-Entropy (BCE)** instead of MSE. Think of it as a penalty system:

| Prediction | True Label | Penalty       |
| ---------- | ---------- | ------------- |
| 0.99       | 1          | tiny (0.01)   |
| 0.51       | 1          | medium (0.67) |
| 0.01       | 1          | huge (4.6)    |

The formula behind it: `-log(y_pred)` when true label is 1. The closer to 0, the more `-log` explodes - that's the punishment.

```python
L = -mean( y * log(y_pred) + (1-y) * log(1-y_pred) )
```

When `y=1`, the second term dies (multiplied by 0). When `y=0`, the first term dies. So only the relevant side gets penalized.

### 3. Backward Pass

Same chain rule as linear regression, just one extra step for sigmoid.

**Step 1** - Compute `dL/dy_pred` (BCE backward):

$$
\frac{dL}{d\hat{y}} = \frac{1}{n}\left(-\frac{y}{\hat{y}} + \frac{1-y}{1-\hat{y}}\right)
$$

**Step 2** - Backprop through sigmoid (the extra step):

$$
\frac{dL}{dA} = \sigma(A)(1 - \sigma(A)) \cdot dout
$$

The derivative of sigmoid is elegantly `σ(x) * (1 - σ(x))`.

**Step 3** - Backprop through add (`A = Z + b`):

$$
\frac{dL}{dZ} = dout, \quad \frac{dL}{db} = \sum dout
$$

**Step 4** - Backprop through matmul (`Z = X @ W`):

$$
\frac{dL}{dW} = X^T \cdot dout, \quad \frac{dL}{dX} = dout \cdot W^T
$$

**Step 5** - Update weights:

```python
W.data -= lr * W.grad
b.data -= lr * b.grad
```

## Visualization

![Decision Boundary](/assets/images/decision_boundary.jpg)
![Sigmoid Surface](/assets/images/sigmoid_surface.jpg)

## Mistakes I Made

### Negative loss

I forgot logistic regression needs binary labels (0s and 1s). I used the same continuous `y_data` from linear regression, which gave BCE a negative loss - mathematically impossible.

**Fix:** Convert to binary labels:

```python
y_data = (X_data @ np.array([[1.0], [1.0]]) > 0).astype(np.float64)
```

### Overwriting `y_pred` with a numpy array

In the zero grad section I wrote:

```python
y_pred = np.zeros_like(y_pred.data)  # WRONG - y_pred is now a numpy array
```

This replaced the `Value` object with a raw numpy array. The next line `y_pred.grad = bce_backward(...)` then crashed because numpy arrays don't have `.grad`.

**Fix:**

```python
y_pred.grad = np.zeros_like(y_pred.data)  # correct
```

### Wrong variable names in `matmul_backward`

I copy-pasted `add_backward`'s body into `matmul_backward` and forgot to change the variable names:

```python
# WRONG
def matmul_backward(X: Value, W: Value, dout: np.ndarray):
    Z.grad += dout
    b.grad += np.sum(dout, axis=0)
```

**Fix:**

```python
# CORRECT
def matmul_backward(X: Value, W: Value, dout: np.ndarray):
    X.grad += dout @ W.data.T
    W.grad += X.data.T @ dout
```

## Maps to Real Frameworks - Personal cheatsheet

| Numpy                         | PyTorch                             | TensorFlow                             |
| ----------------------------- | ----------------------------------- | -------------------------------------- |
| `sigmoid_forward(A)`          | `torch.sigmoid(A)`                  | `tf.sigmoid(A)`                        |
| `bce_forward(y_pred, y)`      | `F.binary_cross_entropy(y_pred, y)` | `tf.keras.losses.BinaryCrossentropy()` |
| `bce_backward(...)`           | `loss.backward()`                   | `tape.gradient(loss, [W, b])`          |
| `(y_probs > 0.5).astype(int)` | `(y_probs > 0.5).int()`             | `tf.cast(y_probs > 0.5, tf.int32)`     |

## What's Next

Decision Tree.
