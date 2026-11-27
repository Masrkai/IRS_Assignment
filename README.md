# AIE425 — Intelligent Recommender Systems Assignment 1

## Dataset

This project uses **MovieLens 1M**. The ratings file is expected at
`data/raw/ratings.dat` and uses the original format:

`UserID::MovieID::Rating::Timestamp`

The MovieLens 1M collection contains 1,000,209 ratings from 6,040 users. The
rating scale is 1–5 stars. The full matrix is sparse: unobserved user-item
pairs are missing values, **not zero-star ratings**.

Download `ml-1m.zip` from the official GroupLens dataset endpoint or use the
team's selected Kaggle mirror. Extract `ratings.dat` into `data/raw/`.
Do not commit the dataset unless the course and dataset terms explicitly allow it.

## Member A scope

- **S1 P1:** rating frequency, overall descriptive statistics, user-rating
  behavior, and item popularity distributions.
- **S3 P3:** time and space complexity analysis for the pipeline and item-CF.
- Shared: validation, reproducible 80/20 interaction split (seed `425`),
  sparse CSR matrix construction, and item-based CF baseline implementation.
- Shared documentation: dataset/methodology notes, README and dependencies.

## Stack

- Python 3.13
- Polars for loading and tabular summaries
- NumPy for numerical operations
- SciPy sparse matrices for memory-efficient user-item storage and sparse products
- Matplotlib for figures
- pytest for tests

JAX is intentionally not a dependency in Member A's implementation: the
required operations are sparse matrix construction and sparse algebra, for
which SciPy provides the appropriate CSR operations. Adding JAX would not
improve this CPU sparse workflow and would increase setup complexity.

## Setup (NixOS)

```bash
nix-shell -p python313 python313Packages.pip python313Packages.virtualenv git
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## Run

```bash
python scripts/run_member_a.py
pytest -q
```

Generated CSV, JSON and figures are written to `reports/generated/`.

## Methodology and conventions

1. Validate required columns, rating range, nulls and duplicate user-item pairs.
2. Shuffle rating interactions with NumPy's `default_rng(425)` and allocate
   80% to training and 20% to testing.
3. Build the training matrix as CSR. Only observed ratings are stored.
4. Compute user means from training observations only.
5. Compute adjusted cosine between items using users who rated both items.
   Similarities with insufficient overlap or zero denominator are undefined
   (`NaN`), not fabricated as zero.
6. Predict a held-out rating from the top-k item neighbors rated by that user.
   The prediction is user mean plus the similarity-weighted deviation from
   that user's mean. MAE, RMSE and coverage are reported.

The exact split and algorithm conventions must be aligned with the group's
final agreed specification before submission.

## S1 P1 interpretation guide

Discuss the rating-frequency distribution (which star values dominate), the
overall mean/median and spread, variation in user generosity using per-user
means, and item popularity skew using ratings-per-item. Distinguish popularity
(number of ratings) from quality (average rating); they are not interchangeable.

## S3 P3 interpretation guide

The complexity table is exported to `reports/generated/complexity_analysis.csv`.
The item-item similarity matrix requires O(I²) output storage. Sparse input
storage is O(E), where E is the number of observed ratings, rather than O(U×I).
Sparse matrix multiplication cost is data-dependent; do not report a single
tight runtime bound without measuring the actual run on the selected dataset.

## Citation

Harper, F. M., & Konstan, J. A. (2015). The MovieLens Datasets: History and
Context. *ACM Transactions on Interactive Intelligent Systems*, 5(4), Article
19. https://doi.org/10.1145/2827872

## Team

| Member | ID | Track |
|---|---:|---|
| Ahmed Essa | 223106563 | A |
| Maryam Othman | 223105468 | B |
| Ahmed Allam | 223102168 | C |

Add the course-required AI acknowledgment and any further references required
by the instructor before final submission.
