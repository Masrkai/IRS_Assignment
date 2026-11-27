import numpy as np
import polars as pl
from scipy.sparse import csr_matrix

from irs_assignment.data import split_ratings, build_sparse_matrix, validate_ratings
from irs_assignment.item_based import adjusted_cosine_similarity, predict_rating


def sample():
    return pl.DataFrame({
        "user_id": [1, 1, 2, 2, 3, 3],
        "item_id": [10, 20, 10, 20, 10, 20],
        "rating": [5., 4., 4., 3., 2., 1.],
        "timestamp": [1, 2, 3, 4, 5, 6],
    })


def test_split_is_reproducible_and_complete():
    df = sample()
    a_train, a_test = split_ratings(df, seed=425)
    b_train, b_test = split_ratings(df, seed=425)
    assert a_train.equals(b_train)
    assert a_test.equals(b_test)
    assert a_train.height + a_test.height == df.height


def test_sparse_matrix_keeps_only_observed_entries():
    matrix, users, items = build_sparse_matrix(sample())
    assert matrix.shape == (3, 2)
    assert matrix.nnz == 6
    assert users[1] == 0
    assert items[10] == 0


def test_similarity_is_symmetric_and_diagonal_undefined():
    matrix, _, _ = build_sparse_matrix(sample())
    sim, overlap = adjusted_cosine_similarity(matrix, min_common=2)
    assert np.allclose(sim, sim.T, equal_nan=True)
    assert np.isnan(np.diag(sim)).all()
    assert overlap[0, 1] == 3


def test_duplicate_pairs_rejected():
    df = pl.concat([sample(), sample().head(1)])
    try:
        validate_ratings(df)
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("Duplicate user-item pairs should be rejected.")
