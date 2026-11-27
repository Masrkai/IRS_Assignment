"""MovieLens loading, validation, deterministic split, and sparse matrix utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import polars as pl
from scipy.sparse import csr_matrix

RATING_COLUMNS = ["user_id", "item_id", "rating", "timestamp"]
SEED = 425


def load_ratings(path: str | Path) -> pl.DataFrame:
    """Load MovieLens 1M ratings.dat (UserID::MovieID::Rating::Timestamp).

    MovieLens uses a two-character delimiter, so parse each line explicitly
    rather than passing ``::`` to Polars' one-character CSV separator.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Put MovieLens 1M ratings.dat in data/raw/."
        )
    records = []
    with path.open("r", encoding="latin-1") as handle:
        for line_number, line in enumerate(handle, start=1):
            parts = line.rstrip("\\r\\n").split("::")
            if len(parts) != 4:
                raise ValueError(
                    f"Malformed ratings.dat row at line {line_number}: expected 4 fields."
                )
            try:
                records.append((int(parts[0]), int(parts[1]), float(parts[2]), int(parts[3])))
            except ValueError as exc:
                raise ValueError(f"Invalid value at ratings.dat line {line_number}.") from exc
    df = pl.DataFrame(
        records,
        schema={
            "user_id": pl.Int64,
            "item_id": pl.Int64,
            "rating": pl.Float64,
            "timestamp": pl.Int64,
        },
        orient="row",
    )
    return validate_ratings(df)


def validate_ratings(df: pl.DataFrame) -> pl.DataFrame:
    """Validate columns, rating scale, nulls, and duplicate user-item events."""
    missing = set(RATING_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if any(df[column].null_count() for column in RATING_COLUMNS):
        raise ValueError("Input contains null values in required columns.")
    invalid = df.filter(~pl.col("rating").is_between(1.0, 5.0))
    if invalid.height:
        raise ValueError("Ratings must be between 1 and 5.")
    duplicates = (
        df.group_by(["user_id", "item_id"]).len().filter(pl.col("len") > 1)
    )
    if duplicates.height:
        raise ValueError(
            f"Found {duplicates.height} duplicate user-item pairs; resolve them "
            "explicitly before splitting."
        )
    return df.select(RATING_COLUMNS).sort(["user_id", "item_id"])


def split_ratings(
    df: pl.DataFrame, test_fraction: float = 0.20, seed: int = SEED
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Random interaction-level 80/20 split, reproducible with seed 425."""
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1.")
    rng = np.random.default_rng(seed)
    order = rng.permutation(df.height)
    n_test = int(round(df.height * test_fraction))
    test_idx = order[:n_test]
    train_idx = order[n_test:]
    train = (
        df.with_row_index("_row")
        .filter(pl.col("_row").is_in(train_idx.tolist()))
        .drop("_row")
        .sort(["user_id", "item_id"])
    )
    test = (
        df.with_row_index("_row")
        .filter(pl.col("_row").is_in(test_idx.tolist()))
        .drop("_row")
        .sort(["user_id", "item_id"])
    )
    return train, test


def build_sparse_matrix(
    df: pl.DataFrame,
    user_ids: Iterable[int] | None = None,
    item_ids: Iterable[int] | None = None,
) -> tuple[csr_matrix, dict[int, int], dict[int, int]]:
    """Build a CSR user-item matrix; absent interactions remain implicit zeros.

    Keep the observation mask separately. A zero in the CSR storage is not a
    rating of zero; MovieLens ratings are 1..5 and unobserved cells are missing.
    """
    users = sorted(set(user_ids if user_ids is not None else df["user_id"].to_list()))
    items = sorted(set(item_ids if item_ids is not None else df["item_id"].to_list()))
    u_map = {value: idx for idx, value in enumerate(users)}
    i_map = {value: idx for idx, value in enumerate(items)}
    rows = np.fromiter((u_map[x] for x in df["user_id"].to_list()), dtype=np.int32)
    cols = np.fromiter((i_map[x] for x in df["item_id"].to_list()), dtype=np.int32)
    vals = df["rating"].to_numpy().astype(np.float64)
    matrix = csr_matrix((vals, (rows, cols)), shape=(len(users), len(items)))
    return matrix, u_map, i_map


def dataset_summary(df: pl.DataFrame) -> dict[str, float | int]:
    n_users = df["user_id"].n_unique()
    n_items = df["item_id"].n_unique()
    n_ratings = df.height
    possible = n_users * n_items
    return {
        "users": n_users,
        "items": n_items,
        "ratings": n_ratings,
        "possible_user_item_pairs": possible,
        "density_percent": 100.0 * n_ratings / possible,
        "sparsity_percent": 100.0 * (1.0 - n_ratings / possible),
        "mean_rating": float(df["rating"].mean()),
    }
