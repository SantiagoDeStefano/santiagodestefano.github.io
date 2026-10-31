---
title: "K Nearest Neighbor from Scratch"
date: 2026-11-01
categories: [ml-dl, "Cracking ML - Classification Models"]
---

# K Nearest Neighbor from Scratch

## What is K Nearest Neighbor?

Data with 2 features and 200 samples, and two classes for that 200 samples;
X (200, 2) and y (200, 1).

KNN doesn't need training, it's an unsupervised algorithm that predict class during inference.

Let's say X_test is the data used in inference and X_train being input data;
For every x in X_test:

- Compute np.sqrt(np.sum(np.square(x - X_train), axis = 1));

In x (2,) - X_train (200, 2), x would get boardcasted to compute the  squared difference. Rule of thumb, comparing dimensions from right to left, and if any of the dimension is equal OR one of them is 1 and missing dim would always be inserted from the left and 1, for example: (2,) would be treated as (1, 2).
The 1 in (1, 2) then would be stretched to x (200, 2); then the result of x - X_train = (200, 2);

After that, we do np.sum[ (200, 2) ] which, sum everything (lol) but on what dimension? Horizontal or vertical? The answer is horizontal using the distance formula in Descartes coordinate system. And implement it by using axis = 1 (which collapse second dimension). With the result being (200,).

Finally, we square it for the final distance, now the difference is computed being (200,).

- Then we sort the difference to get the smallest difference, being implemented with argsort(), which output the indices of the elements in ascending order. For example:
argsort([5, 3, 6, 0]) would result in [3, 1, 0, 2].
Then we take the first k indices using [0, k]. I will call it k_idx.

- After that, we assign the label to the k_idx by using y_train[k_idx].

- Finally, giving indices of the predictions using bincount(k_labels); For example: 
bincount([1, 1, 0, 0, 0]) would result in [3, 2], then .argmax() would gave 0.

## The Code
```python
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
```