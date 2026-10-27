---
title: "Gaussian Naive Bayes from Scratch"
date: 2026-10-25
categories: [ml-dl, "Cracking ML - Classification Models"]
---

# Gaussian Naive Bayes from Scratch

## What is Gaussian Naive Bayes?

X_train is 2 features with 100 samples, (100, 2);
y_train is (100,)

Compute the mean and std of each class's samples,
and how dominate (priors) the X_c;

Then we apply the pdf of gaussian
now it have meaning of "given this class, how likely it is ...",
effectively P(X|C);

Find label (in this case is class) using bayes:
P(C|X) = P(X|C) * P(C) / P(X);

We normally do log transform with the formula,

log(P(C|X)) = log(P(X|C)) + log(P(C)) - log(P(X))
But we can remove log(P(X)) because it is the same for every class (no C in P(X)), thus, doesn't change the outcome of argmax.

Additionally, we also log transform the P(X|C).
We can do np.prod(pdf) to mutiply every features but
if it have many features, the mutiplication would involving really small 
number and hard to compute for the computer, so instead
we log transform it.

P(X|C) = P(X_1|C) * P(X_2|C) * .... * P(X_N|C) = np.prod(pdf),
with X_1, X_2, X_N is features 1/2/N of X.

log(P(X|C)) = log(P(X_1|C)) + log(P(X_2|C)) + ... + log(P(X_N|C));

After all that, we get log(P(C|X)), and use argmax() to find the index
of the highest scoring classes, then map it back to the class label. Finally
we get the predicted class.

## The Code
```python
class GaussianNB:
    def __init__(self):
        pass

    def train(self, X: np.ndarray, y: np.ndarray):
        self.mean = {}
        self.std = {}
        self.priors = {}
        self.classes = np.unique(y)
        for c in self.classes:
            X_c = X[y == c]
            self.mean[c] = np.mean(X_c, axis=0)
            self.std[c] = np.std(X_c, axis=0)
            self.priors[c] = X_c.shape[0]/X.shape[0]

    def predict(self, X: np.ndarray):
        preds = []
        for x in X:
            posteriors = []
            for c in self.classes:
                pdf = (1/(self.std[c] * np.sqrt(2*np.pi))) * np.exp(-1/2 * ((x - self.mean[c])/self.std[c])**2)
                posterior = np.sum(np.log(pdf)) + np.log(self.priors[c])
                posteriors.append(posterior)
            preds.append(self.classes[np.argmax(posteriors)])
        return preds
```