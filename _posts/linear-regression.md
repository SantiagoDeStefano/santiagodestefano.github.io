---
title: "Linear Regression from Scratch with Backpropagation"
date: 2026-05-13
---

# Linear Regression from Scratch with Backpropagation

## What is Linear Regression?

To predict data that exposes a linear relationship. In this blog, we'll work with only 2 dimensions.

## The Math

The model is pretty much this in high school terms: **y = ax + b**.

In this blog, it would be formulated as:

$$
\hat{y} = XW + b
$$

## The Code

```python
import numpy as np

class Value:
    """Stores a value and its gradient."""
    def __init__(self, data):
        self.data = np.array(data, dtype=np.float64)
        self.grad = np.zeros_like(self.data)

def matmul_forward(X: Value, W: Value):
    return Value(X.data @ W.data)

def matmul_backward(X: Value, W: Value, dout: np.ndarray):
    X.grad += dout @ W.data.T
    W.grad += X.data.T @ dout

def add_forward(Z: Value, b: Value):
    return Value(Z.data + b.data)

def add_backward(Z: Value, b: Value, dout: np.ndarray):
    Z.grad += dout
    b.grad += np.sum(dout, axis=0)

def mse_forward(y_pred: Value, y_true: Value):
    diff = y_pred.data - y_true.data
    loss = np.mean(diff ** 2)
    return loss, diff

def mse_backward(diff: np.ndarray, n: int):
    return (2.0 / n) * diff

np.random.seed(42)

n_samples, n_features = 200, 2
X_data = np.random.randn(n_samples, n_features)
y_data = X_data @ np.array([[3.0], [5.0]]) + 7.0 + np.random.randn(n_samples, 1) * 0.5

W = Value(np.random.randn(n_features, 1) * 0.01)
b = Value(np.zeros((1, 1)))

lr = 0.1
epochs = 1000

for epoch in range(epochs):
    X = Value(X_data)
    y = Value(y_data)

    Z = matmul_forward(X, W)
    y_pred = add_forward(Z, b)
    loss, diff = mse_forward(y_pred, y)

    W.grad = np.zeros_like(W.data)
    b.grad = np.zeros_like(b.data)
    Z.grad = np.zeros_like(Z.data)
    y_pred.grad = np.zeros_like(y_pred.data)

    y_pred.grad = mse_backward(diff, n_samples)
    add_backward(Z, b, y_pred.grad)
    matmul_backward(X, W, Z.grad)

    W.data -= lr * W.grad
    b.data -= lr * b.grad

    if epoch % 50 == 0:
        print(f"Epoch {epoch:3d} | Loss: {loss:.4f} | W: {W.data.flatten()} | b: {b.data.flatten()}")

print(f"\nLearned:  W = {W.data.flatten()}, b = {b.data.flatten()}")
print(f"True:     W = [3, 5],              b = [7]")
```

## How It Actually Works

### 1. Forward Pass

This part means: give input into the model, then get the result. Simple as that. The model **doesn't update** the weights during this pass.

It would be presented by this:

- `Z = X @ W` - multiply inputs by weights
- `y_pred = Z + b` - add bias
- `loss = mean((y_pred - y)²)` - measure how wrong the output is from the actual values

### 2. Backward Pass

This part means: the model learns from the loss. It updates the weights based on how wrong the model was in the last prediction.

The process would be:

**Step 1** - Compute the "wrong-ness" of the model:

$$
\frac{dL}{d\hat{y}} = \frac{2}{n}(\hat{y} - y)
$$

**Step 2** - Use the wrong-ness to compute gradients for `b` and `Z`. Since `y_pred = Z + b`:

$$
\frac{dL}{dZ} = dout, \quad \frac{dL}{db} = \sum dout \text{ (over batch dim)}
$$

`b` gets a summed gradient because one single `b` was added to all 200 samples.

**Step 3** - Since `Z = X @ W`, take one more step to get the gradients for `W`:

$$
\frac{dL}{dW} = X^T \cdot dout, \quad \frac{dL}{dX} = dout \cdot W^T
$$

```python
W.grad += X.data.T @ dout
X.grad += dout @ W.data.T  # not used here, but needed for deeper networks
```

**Step 4** - Finally, update both the weights and bias:

```python
W.data -= lr * W.grad
b.data -= lr * b.grad
```

This process repeats multiple times - each full pass is called an **epoch** (how many times the model has seen all the data).

The **learning rate** controls how fast the model converges. Imagine walking down a hill: the gradient is the direction, the learning rate is how far each step. Too much distance and we can't find the lowest point (divergence). Too narrow and we take too long to get there.

## Mistakes I Made

### Using `.grad` instead of `.data`

In `matmul_backward`, I accidentally wrote:

```python
# WRONG
X.grad += dout @ W.grad.T
W.grad += X.grad.T @ dout
```

The backward formula needs the **original data** from the forward pass, not the partially-computed gradients. Gradients tell you the direction to update - they don't hold the values that were actually multiplied together.

**Fix:**

```python
# CORRECT
X.grad += dout @ W.data.T
W.grad += X.data.T @ dout
```

### Accidentally updating X

I wrote:

```python
W.data -= lr * W.grad
X.data -= lr * X.grad  # WRONG
```

`X` is your input data - the raw measurements. You never want to change it. That would mean modifying your data to fit the model, instead of fitting the model to the data. Only **learnable parameters** (`W` and `b`) should be updated.

**Fix:** Simply remove `X.data -= lr * X.grad`.

### Forgetting to zero gradients

Gradients accumulate with `+=`. Without resetting them to zero before each epoch, new gradients pile on top of old ones, giving wrong values.

**Fix:** Reset before each backward pass:

```python
W.grad = np.zeros_like(W.data)
b.grad = np.zeros_like(b.data)
Z.grad = np.zeros_like(Z.data)
y_pred.grad = np.zeros_like(y_pred.data)
```

## What's Next

Logistic Regression.