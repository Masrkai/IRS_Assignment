"""S3 P3 complexity analysis for item-based collaborative filtering."""
from __future__ import annotations


def complexity_table(n_users: int, n_items: int, n_ratings: int, k: int) -> list[dict]:
    """Asymptotic costs for the implemented sparse item-based CF pipeline.

    E is the number of observed ratings. These are upper-level operation counts;
    actual wall-clock time depends on sparsity, BLAS/SciPy implementation and hardware.
    """
    return [
        {
            "stage": "Load and validate ratings",
            "time_complexity": "O(E)",
            "space_complexity": "O(E)",
            "explanation": "Each observed rating is parsed and checked once.",
        },
        {
            "stage": "80/20 split",
            "time_complexity": "O(E)",
            "space_complexity": "O(E)",
            "explanation": "Permutation and indexing over the observed interactions.",
        },
        {
            "stage": "Build sparse user-item matrix",
            "time_complexity": "O(E)",
            "space_complexity": "O(E + U + I)",
            "explanation": "CSR stores only observed ratings, not all U×I cells.",
        },
        {
            "stage": "Item-item similarity",
            "time_complexity": "data-dependent; dense upper bound O(U×I²)",
            "space_complexity": "O(I² + E)",
            "explanation": "Sparse products form item-item co-rating statistics; output similarity is dense I×I.",
        },
        {
            "stage": "One prediction",
            "time_complexity": "O(d_u + k log d_u)",
            "space_complexity": "O(d_u)",
            "explanation": "Compare target item with d_u items rated by that user, then select up to k neighbors.",
        },
        {
            "stage": "Predict T test ratings",
            "time_complexity": "O(T×(d̄ + k log d̄))",
            "space_complexity": "O(T)",
            "explanation": "T is the number of test interactions and d̄ is average user history length.",
        },
    ]


def dense_vs_sparse_bytes(n_users: int, n_items: int, n_ratings: int, value_bytes: int = 8) -> dict:
    dense = n_users * n_items * value_bytes
    # Approximate CSR: values + 32-bit column indices + 32-bit row pointer.
    sparse = n_ratings * (value_bytes + 4) + (n_users + 1) * 4
    return {
        "dense_bytes": dense,
        "csr_approx_bytes": sparse,
        "dense_mib": dense / (1024 ** 2),
        "csr_approx_mib": sparse / (1024 ** 2),
        "dense_to_sparse_ratio": dense / sparse if sparse else float("inf"),
    }
