---
title: "Linear Discriminant Analysis from Scratch"
date: 2026-11-05
categories: [ml-dl, "Cracking ML - Classification Models"]
---

# Linear Discriminant Analysis from Scratch

## What is Linear Discriminant Analysis?

X_train with 2 features, 100 samples, thus, shape of (100, 2);
y_train of (100,);

Now we took out the mean and numbers of classes with numbers of features; In order to calculate S_W and S_B, we have to create a matrix of (num_features, num_features).

S_W:

For each classes, we took every samples of the respected class, being X_c (..., 2) for example, (420, 2); the mean should be (2,).
Calculate the difference of X_c and the mean of that respected class. The result being diff (420, 2).
Accumulate S_W with each class's scatter, being diff.T (2, 420) @ (420, 2) which result with (2, 2). To get the total spread of every class.

S_B:

Calculate mean of every classes using np.mean(), result in mean_all being (2,). Then again, calculate the scatter between each classes mean and total of every class's mean; result in (2,) - (2,) = diff (2,). Finally, accumulate, S_B with n_c * outer(diff, diff) with n_c being each classes sample.

After got both, we have to find a projection that minimize the spread within classes (S_W) and maximize the spread between classes (S_B).

$$
J(w)=\frac{w^T S_B w}{w^T S_W w}
$$

First, we simply the problem with:

$$
\max_w \; w^T S_B w
$$

With:

$$
w^T S_W w = 1
$$

Secondly, use the Lagrange multipliers:

$$
L(w) = w^T S_B w - \lambda \left( w^T S_W w - 1 \right)
$$

Take the derivate of w, S_B and S_W were calculated from the dataset, so those are fixed, and we want the projection w not lambda so we only take derivate of only w:

$$
\frac{\partial L}{\partial w} = 2S_Bw - 2\lambda S_Ww
$$

Set the derivative to zero:

$$
2S_Bw - 2\lambda S_Ww = 0
$$

Multiply both sides by $S_W^{-1}$:

$$
{S_W^{-1}S_Bw = \lambda w}
$$

With numpy, it is np.linalg.inv(S_W) @ S_B.

Then we compute the eigenvalues and eigenvectors. Each eigenvalue tells how well its eigenvector separates the classes (the Fisher ratio). We sort the eigenvalues from largest to smallest and keep the eigenvectors of the top C - 1. These form W (n_features, C - 1) = (2, 1), the projection matrix.

## The Code
```python
class LinearDA:
    def __init__(self):
        pass

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.mean = {}
        self.classes = np.unique(y)
        n_features = X.shape[1]
        S_W = np.zeros((n_features, n_features))
        S_B = np.zeros((n_features, n_features))
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis = 0)
            diff = X_c - self.mean[c]
            S_W += diff.T @ diff    

        self.mean_all = np.mean(X, axis = 0)
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis = 0)
            diff = np.mean(X_c, axis = 0) - self.mean_all
            S_B += X_c.shape[0] * np.outer(diff, diff)

        eigvals, eigvecs = np.linalg.eig(np.linalg.inv(S_W) @ S_B)
        idx = np.argsort(eigvals)[::-1]
        W = eigvecs[0:, idx[0: len(self.classes) - 1]]
        self.W = W

    def predict(self, X):
        X_proj = X @ self.W
        centroids = {c: self.mean[c] @ self.W for c in self.classes}
        preds = []
        for x in X_proj:
            dists = {c: np.linalg.norm(x - centroids[c]) for c in self.classes}
            preds.append(min(dists, key=lambda k: dists[k]))
        return np.array(preds)
```