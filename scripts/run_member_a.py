from pathlib import Path
import json
import numpy as np
import polars as pl
import matplotlib.pyplot as plt

from irs_assignment.data import load_ratings, split_ratings, build_sparse_matrix, dataset_summary, SEED
from irs_assignment.statistics import rating_statistics
from irs_assignment.item_based import evaluate_item_based
from irs_assignment.complexity import complexity_table, dense_vs_sparse_bytes

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "ratings.dat"
OUT = ROOT / "reports" / "generated"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

ratings = load_ratings(DATA)
summary = dataset_summary(ratings)
stats = rating_statistics(ratings)
train, test = split_ratings(ratings, test_fraction=0.20, seed=SEED)

# Preserve the full ID universe in both matrices so row/column indices agree.
all_users = sorted(ratings["user_id"].unique().to_list())
all_items = sorted(ratings["item_id"].unique().to_list())
train_matrix, user_map, item_map = build_sparse_matrix(train, all_users, all_items)

test_rows = np.array([user_map[x] for x in test["user_id"].to_list()], dtype=np.int32)
test_cols = np.array([item_map[x] for x in test["item_id"].to_list()], dtype=np.int32)
test_values = test["rating"].to_numpy().astype(float)

evaluation = evaluate_item_based(train_matrix, test_rows, test_cols, test_values, k=20)
summary.update({
    "train_ratings": train.height,
    "test_ratings": test.height,
    "split_seed": SEED,
    "split_ratio": "80/20",
})
(OUT / "dataset_summary.json").write_text(json.dumps(summary, indent=2))
(OUT / "rating_statistics.json").write_text(json.dumps({
    "overall": stats["overall"],
    "user_activity_summary": stats["user_activity_summary"],
    "item_popularity_summary": stats["item_popularity_summary"],
}, indent=2))
stats["frequency"].write_csv(OUT / "rating_frequency.csv")
stats["per_user"].write_csv(OUT / "per_user_statistics.csv")
stats["per_item"].write_csv(OUT / "per_item_statistics.csv")

# S1 P1 figures.
freq = stats["frequency"].to_pandas()
plt.figure(figsize=(7, 4))
plt.bar(freq["rating"].astype(str), freq["len"])
plt.title("MovieLens 1M: Rating Frequency")
plt.xlabel("Rating (stars)")
plt.ylabel("Number of ratings")
plt.tight_layout()
plt.savefig(FIG / "rating_frequency.png", dpi=160)
plt.close()

user_means = stats["per_user"]["mean_rating"].to_numpy()
plt.figure(figsize=(7, 4))
plt.hist(user_means, bins=30)
plt.title("Distribution of Average Rating per User")
plt.xlabel("Mean user rating")
plt.ylabel("Number of users")
plt.tight_layout()
plt.savefig(FIG / "user_mean_distribution.png", dpi=160)
plt.close()

item_counts = stats["per_item"]["rating_count"].to_numpy()
plt.figure(figsize=(7, 4))
plt.hist(item_counts, bins=40)
plt.title("Distribution of Ratings per Movie")
plt.xlabel("Number of ratings per movie")
plt.ylabel("Number of movies")
plt.tight_layout()
plt.savefig(FIG / "item_popularity_distribution.png", dpi=160)
plt.close()

eval_summary = {key: evaluation[key] for key in ["mae", "rmse", "coverage", "n_test", "n_predicted"]}
(OUT / "item_based_evaluation.json").write_text(json.dumps(eval_summary, indent=2))

complexity = complexity_table(len(all_users), len(all_items), ratings.height, 20)
pl.DataFrame(complexity).write_csv(OUT / "complexity_analysis.csv")
memory = dense_vs_sparse_bytes(len(all_users), len(all_items), ratings.height)
(OUT / "matrix_memory_estimate.json").write_text(json.dumps(memory, indent=2))

print("=== Dataset ===")
print(json.dumps(summary, indent=2))
print("\n=== Rating statistics ===")
print(json.dumps(stats["overall"], indent=2))
print("\n=== Item-based CF evaluation ===")
print(json.dumps(eval_summary, indent=2))
print("\n=== Matrix memory estimate ===")
print(json.dumps(memory, indent=2))
print(f"\nGenerated outputs: {OUT}")
