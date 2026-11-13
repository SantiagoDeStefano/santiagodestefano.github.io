import numpy as np

class PCA:
    def __init__(self, n_components=2):
        self.n_components = n_components

    def fit(self, X: np.ndarray):
        # Step 1: center data (subtract mean of each feature)
        self.mean = np.mean(X, axis=0)
        X_centered = X - self.mean

        # Step 2: covariance matrix (d, d)
        cov = (X_centered.T @ X_centered) / (X.shape[0] - 1)

        # Step 3: eigenvectors = directions, eigenvalues = variance along them
        eigvals, eigvecs = np.linalg.eigh(cov)   # eigh: for symmetric matrices

        # Step 4: sort by eigenvalue, biggest first
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]

        # Step 5: keep top k directions
        self.components = eigvecs[:, :self.n_components]
        self.explained_variance_ratio = eigvals[:self.n_components] / np.sum(eigvals)
