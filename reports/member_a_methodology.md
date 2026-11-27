# Member A — Methodology and Results Notes

## S1 P1: Rating statistics

The analysis reports:
- Total number of observed ratings and the overall mean, median, standard
  deviation, minimum, maximum, and quartiles.
- Frequency and percentage of each rating from 1 to 5.
- Per-user mean rating and rating count.
- Per-item mean rating and rating count.

Interpretation must distinguish user generosity from item quality and item
popularity. A high item rating count indicates popularity/exposure, not
necessarily a high average rating. The actual numeric results are generated
from the chosen `ratings.dat`; do not copy dataset-wide figures as if they
were computed from the team's train/test subset.

## Shared preprocessing

The code validates required fields and rejects duplicate user-item pairs.
A seeded random interaction split (`seed=425`) reserves 20% for testing.
The training matrix uses CSR storage. Missing interactions are implicit
absences and are never interpreted as observed rating zero.

## Shared item-based CF baseline

The implementation uses adjusted cosine similarity. For items i and j, the
calculation is restricted to users who rated both items, and each rating is
centered by that user's mean computed from the training set. A similarity is
undefined when overlap is below the minimum or either centered norm is zero.
The prediction is the user's training mean plus the similarity-weighted
deviation of the user's ratings on neighboring items.

The baseline exports MAE, RMSE, and prediction coverage. These results should
be compared with the group user-based CF results using the same split and
evaluation definitions.

## S3 P3: Complexity

Let U be users, I items, E observed ratings, T test interactions, d_u the
number of training ratings by user u, and k the neighborhood size.

| Operation | Time | Space |
|---|---|---|
| Loading and validation | O(E) | O(E) |
| Random split | O(E) | O(E) |
| CSR construction | O(E) | O(E + U + I) |
| Item-item similarity | Data-dependent; dense upper bound O(U I²) | O(I² + E) |
| One prediction | O(d_u + k log d_u) | O(d_u) |
| T predictions | O(T(d̄ + k log d̄)) | O(T) |

The similarity matrix has I² entries, so its dense output can become the
memory bottleneck even when the user-item input is sparse. The runtime
depends on rating sparsity and sparse multiplication implementation.
