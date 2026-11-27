"""Item-based CF using adjusted cosine similarity and neighborhood prediction."""
from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix


def adjusted_cosine_similarity(
    ratings: csr_matrix, min_common: int = 2
) -> tuple[np.ndarray, np.ndarray]:
    """Compute exact adjusted cosine using only users who rated both items.

    User means are computed from the training ratings. Sparse matrix products
    calculate pairwise dot products, overlap counts, and pair-specific norms.
    Similarities with fewer than min_common co-raters are NaN.
    """
    R = ratings.tocsr().astype(np.float64)
    observed = R.copy()
    observed.data = np.ones_like(observed.data)
    user_counts = np.asarray(observed.sum(axis=1)).ravel()
    user_sums = np.asarray(R.sum(axis=1)).ravel()
    user_means = np.divide(
        user_sums, user_counts, out=np.zeros_like(user_sums), where=user_counts > 0
    )

    centered = R.copy()
    for u in range(centered.shape[0]):
        start, end = centered.indptr[u], centered.indptr[u + 1]
        centered.data[start:end] -= user_means[u]

    X = centered.tocsc()
    M = observed.tocsc()
    X2 = X.copy()
    X2.data **= 2

    numerator = (X.T @ X).toarray()
    overlap = (M.T @ M).toarray()
    left_sq = (X2.T @ M).toarray()
    right_sq = left_sq.T
    denominator = np.sqrt(np.maximum(left_sq, 0) * np.maximum(right_sq, 0))

    similarity = np.full(numerator.shape, np.nan, dtype=np.float64)
    valid = (overlap >= min_common) & (denominator > 0)
    np.divide(numerator, denominator, out=similarity, where=valid)
    np.fill_diagonal(similarity, np.nan)
    return similarity, overlap.astype(np.int32)


def predict_rating(
    user_row: csr_matrix,
    user_mean: float,
    item_index: int,
    similarity: np.ndarray,
    k: int = 20,
) -> float:
    """Predict an unrated item from the user's rated items and top-k neighbors."""
    row = user_row.tocsr()
    rated_items = row.indices
    rated_values = row.data
    if rated_items.size == 0:
        return float("nan")

    scores = similarity[item_index, rated_items]
    valid = np.isfinite(scores) & (np.abs(scores) > 0)
    if not np.any(valid):
        return float("nan")

    scores = scores[valid]
    values = rated_values[valid]
    neighbors = rated_items[valid]
    order = np.argsort(np.abs(scores))[::-1][:k]
    weights = scores[order]
    deviations = values[order] - user_mean
    denom = np.abs(weights).sum()
    if denom == 0:
        return float("nan")
    return float(user_mean + np.dot(weights, deviations) / denom)


def evaluate_item_based(
    train: csr_matrix,
    test_rows: np.ndarray,
    test_cols: np.ndarray,
    test_values: np.ndarray,
    k: int = 20,
    min_common: int = 2,
) -> dict:
    """Evaluate item-CF predictions; report MAE/RMSE and prediction coverage."""
    similarity, overlap = adjusted_cosine_similarity(train, min_common=min_common)
    row_counts = np.diff(train.indptr)
    row_sums = np.asarray(train.sum(axis=1)).ravel()
    means = np.divide(
        row_sums, row_counts, out=np.zeros_like(row_sums), where=row_counts > 0
    )

    predictions = np.full(len(test_values), np.nan, dtype=float)
    for idx, (u, i) in enumerate(zip(test_rows, test_cols)):
        predictions[idx] = predict_rating(train.getrow(int(u)), means[int(u)], int(i), similarity, k)

    valid = np.isfinite(predictions)
    if not valid.any():
        return {
            "mae": float("nan"), "rmse": float("nan"), "coverage": 0.0,
            "n_test": int(len(test_values)), "n_predicted": 0,
            "similarity": similarity, "overlap": overlap, "predictions": predictions,
        }

    errors = predictions[valid] - test_values[valid]
    return {
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors ** 2))),
        "coverage": float(valid.mean()),
        "n_test": int(len(test_values)),
        "n_predicted": int(valid.sum()),
        "similarity": similarity,
        "overlap": overlap,
        "predictions": predictions,
    }
