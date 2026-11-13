import numpy as np
from cracking_ml.classification.svm_with_hinge_loss import SVM

def permutation_feature_importance(model: SVM, X: np.ndarray, y: np.ndarray, n_repeats=10):
    # Baseline score with nothing shuffled
    base_score = np.mean(model.predict(X) == y)

    importances = np.zeros(X.shape[1])

    for j in range(X.shape[1]):
        drops = []
        for _ in range(n_repeats):
            X_perm = X.copy()
            # Shuffle column j to break the link between feature j and label y
            X_perm[:, j] = np.random.permutation(X_perm[:, j])

            score = np.mean(model.predict(X_perm) == y)
            drops.append(base_score - score)

        # Average drop in score equals importance of feature j
        importances[j] = np.mean(drops)
    
    return importances


# test with your SVM
X_train = np.random.randn(200, 3)
y_train = np.where(X_train[:, 0] + X_train[:, 1] > 0, 1, -1)   # feature 2 is noise
X_val = np.random.randn(100, 3)
y_val = np.where(X_val[:, 0] + X_val[:, 1] > 0, 1, -1)

model = SVM()
model.fit(X_train, y_train)

imp = permutation_feature_importance(model, X_val, y_val)
for j, v in enumerate(imp):
    print(f"Feature {j}: {v:.4f}")