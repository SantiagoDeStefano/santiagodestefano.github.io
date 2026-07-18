import numpy as np
from cracking_ml.classification.svm_with_hinge_loss import SVM

def permutation_importance(
        model: SVM, 
        X: np.array, 
        y: np.array,
        n_repeats = 10,
        random_state = 42
    ):
    rng = np.random.default_rng(random_state)
    baseline = metric(y, model.predict(X))
