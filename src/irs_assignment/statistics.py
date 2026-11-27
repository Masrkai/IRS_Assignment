"""S1 P1 descriptive statistics for MovieLens ratings."""
from __future__ import annotations

import polars as pl


def rating_statistics(ratings: pl.DataFrame) -> dict:
    """Return overall, rating-frequency, per-user, and per-item statistics."""
    overall = ratings.select(
        pl.len().alias("n_ratings"),
        pl.col("rating").mean().alias("mean"),
        pl.col("rating").median().alias("median"),
        pl.col("rating").std().alias("std"),
        pl.col("rating").min().alias("min"),
        pl.col("rating").max().alias("max"),
        pl.col("rating").quantile(0.25).alias("q1"),
        pl.col("rating").quantile(0.75).alias("q3"),
    ).to_dicts()[0]

    frequency = (
        ratings.group_by("rating")
        .len()
        .sort("rating")
        .with_columns((pl.col("len") / ratings.height * 100).alias("percentage"))
    )
    per_user = ratings.group_by("user_id").agg(
        pl.len().alias("rating_count"), pl.col("rating").mean().alias("mean_rating")
    )
    per_item = ratings.group_by("item_id").agg(
        pl.len().alias("rating_count"), pl.col("rating").mean().alias("mean_rating")
    )

    return {
        "overall": overall,
        "frequency": frequency,
        "per_user": per_user,
        "per_item": per_item,
        "user_activity_summary": per_user.select(
            pl.col("rating_count").mean().alias("mean"),
            pl.col("rating_count").median().alias("median"),
            pl.col("rating_count").min().alias("min"),
            pl.col("rating_count").max().alias("max"),
        ).to_dicts()[0],
        "item_popularity_summary": per_item.select(
            pl.col("rating_count").mean().alias("mean"),
            pl.col("rating_count").median().alias("median"),
            pl.col("rating_count").min().alias("min"),
            pl.col("rating_count").max().alias("max"),
        ).to_dicts()[0],
    }
