---
title: "Average Perceptron from Scratch"
date: 2026-10-25
categories: [ml-dl, "Cracking ML - Classification Models"]
---

# Average Perceptron from Scratch

## What is Average Perceptron?
A linear binary classifier (labels +/- 1). It trains exactly like the plain perceptron (update W, b only on mistakes), but predicts with the average of W, b over every training step instead of the final ones. Making the boundary more stable and less sensitive to a few late updates, especially on noisy or non-separable data.

## The Math
$$
\hat{y} = \text{sign}(Wx + b)
$$

Update (only on mistake, $\text{sign}(Wx_i + b) \neq \hat{y}$):

$$
W \leftarrow W + \eta \, y_i \, x_i, \qquad b \leftarrow b + \eta \, y_i
$$

Average over all steps:

$$
W_{avg} = \frac{1}{T} \sum_{t=1}^{T} W_t, \qquad
b_{avg} = \frac{1}{T} \sum_{t=1}^{T} b_t, \qquad
T = \text{epochs} \times n
$$

## The Code
```python
import numpy as np

class AveragePerceptron:
    def __init__(self):
        pass

    def train(self, X: np.ndarray, y: np.ndarray):
        # W is (2,)
        self.W = np.zeros(X.shape[1])
        self.b = 0.0
        W_sum = np.zeros(X.shape[1])
        b_sum = 0.0

        for epoch in range(epoches):
            for x, yi in zip(X, y):
                y_pred = self.W @ x + self.b
                if np.sign(y_pred) != yi:
                    self.W = self.W + lr * yi * x
                    self.b = self.b + lr * yi
                W_sum += self.W
                b_sum += self.b
                print(f"Epoch: {epoch} Distance from true y: {abs(y_pred - yi)}")        

        # Sum / the total iteration that W_sum got added up
        self.W = W_sum / (epoches * len(X))
        self.b = b_sum / (epoches * len(X))

    def predict(self, X: np.ndarray):
        preds = []
        for x in X:
            pred = np.sign(self.W @ x + self.b)
            preds.append(pred)
        return preds

lr = 0.01
epoches = 100

X_train = np.random.rand(100, 2)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 1, -1, 1)
X_test = np.random.rand(100, 2)
y_test = np.where(X_test[:, 0] + X_test[:, 1] > 1, -1, 1)

model = AveragePerceptron()
model.train(X_train, y_train)
preds = model.predict(X_test)
print(np.mean(preds == y_test))
```

## How It Actually Works

### Training loop
y_pred = W @ x + b; which is a linear projection of x by W plus a bias.
then we use np.sign(y_pred) to decide the need of updating W and b.

And if not (ofc it isn't), we would steer it using yi * x; which mean with this x, i got this yi so just use it to change W accordingly, and finally steering the bias with yi;

After that, accumulate the W and b even if the prediciton is wrong or not. Usage of this would be explained later.


### Why b's update has no x
Each parameter is updated by y * (what it's mutiplied).
In W @ x + b, each w is multiplied by x, but b is multiplied by 1.
So W += lr * y * x and b += lr * y * 1 = lr * y.
In which, b is just a weight on a constant feature x₀ = 1.

### Why average
After that, accumulate both the W and the b; then average it for better generalization. Let's say without the average thing, first 900 samples decided the W and b then the last 100 samples with X and y being completely different from the 900 samples, it would make W and b to learn from the last 100 samples if it have very different distribution, effectively throw away all 900 previous samples.


## Maps to Real Frameworks
| NumPy | sklearn |
|---|---|
| manual loop | `Perceptron` (no averaging) |
| W_sum / T | `SGDClassifier(loss="perceptron", average=True)` |