---
title: "Lasso Regression from Scratch with Backpropagation"
date: 2026-10-20
categories: [ml-dl, "Cracking ML - Linear Models"]
---

# Lasso Regression from Scratch with Backpropagation

## What is Lasso Regression?

Linear regression, but with an L1 penalty added to the loss: `alpha * sum(abs(W))`. This pushes unimportant weights to exactly 0, giving automatic feature selection; useful when you have correlated/redundant features and want the model to pick one instead of spreading weight across all of them.

## The Math

Standard linear prediction:

$$
\hat{y} = XW + b
$$

Loss = MSE + L1 penalty:

$$
L = \frac{1}{n}\sum(\hat{y} - y)^2 + \alpha \sum |W|
$$

`alpha` controls how aggressively weights get pushed to zero.

## The Code

```python
import numpy as np

class Value:
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

def mse_lasso_forward(y_pred: Value, y_true: Value, W: Value, alpha: np.float64):
    diff = y_pred.data - y_true.data
    loss = np.mean(diff**2) + alpha * np.sum(np.abs(W.data))
    return loss, diff

def mse_lasso_backward(y_pred: Value, diff: np.ndarray, n: int, alpha: np.float64, W: Value):
    d_pred = (2.0 / n) * diff
    d_W = alpha * np.sign(W.data)
    return d_pred, d_W
```

Training loop: forward → compute loss/diff → backprop through add/matmul → add the L1 gradient (`alpha * sign(W)`) on top of the regular `W.grad` → gradient descent step.

```python
W.grad += dW_reg  # L1 regularization gradient added on top
W.data -= lr * W.grad
```

## How It Actually Works

### Forward Pass
Same as linear regression (`Z = X@W`, `y_pred = Z + b`), plus the L1 term tacked onto the loss.

### The derivative of `|W|` is `sign(W)`
`d/dW |W| = sign(W)`; a constant `+1` or `-1` (0 at `W=0`), independent of magnitude. So every step, L1 pushes each weight toward zero by the same fixed amount `alpha`, regardless of the magnitude. Once a weight's gradient from the MSE term is smaller than this constant pull, it gets snapped to 0.

Compare to L2 (ridge), where `d/dW W^2 = 2W`; the pull shrinks as `W` shrinks, so it decays asymptotically but never hits exact zero.

### Backward Pass
Identical chain rule to linear regression, with one addition: after computing `W.grad` from `matmul_backward`, add `dW_reg = alpha * sign(W.data)` on top before the update step.

### Why Lasso works
Example: True relationship `3x1 + 5x2 + 0·x3`
Weight matrix: `[3.5, 6, 0.5]`

- Plain linear regression: nothing to remove the `0.5` on `x3`. As long as it doesn't hurt MSE, it can stay nonzero; nothing to push it to exactly 0, even though `x3` is irrelevant.

- Lasso fixes this: adds `alpha * sum(|W|)` to the loss. Now every nonzero weight has a cost. Since `x3`'s `0.5` barely reduces error, shrinking it toward 0 lowers total loss (penalty term drops, MSE barely changes); so the optimizer keeps pushing it down until it hits exactly 0 and stays there.

## Maps to Real Frameworks

| Numpy | sklearn | PyTorch |
|---|---|---|
| `mse_lasso_forward` (manual penalty) | `sklearn.linear_model.Lasso(alpha=...)` | `loss + alpha * sum(p.abs().sum() for p in params)` |
| `np.sign(W.data)` | handled internally (coordinate descent) | `param.grad += alpha * param.sign()` |
| grid search on `alphas` | `LassoCV` | manual sweep / Optuna |