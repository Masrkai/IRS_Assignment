# Members

| Name | ID | Selected |
| --- | --- | --- |
| Ahmed Essa | 223106563 | A |
| Maryam Othman | 223105468 | B |
| Ahmed Allam | 223102168 | C |


## planned timeline (gannt)

```mermaid
gantt
    title AIE425 Assignment 1 - Group Plan
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Setup
    Pick dataset and agree equations - All :setup1, 2026-11-24, 2d
    Registration email 4 PM :milestone, m1, 2026-11-26, 0d

    section Foundation
    Cleaning and split seed 425 - A :f1, 2026-11-26, 4d
    Target users and metric utils - B :f2, 2026-11-26, 4d
    Core similarity and prediction utils - C :f3, 2026-11-26, 5d
    Freeze split and target users :milestone, m2, 2026-12-01, 0d

    section Section 1
    S1 P1 Rating distribution - A :s1a, 2026-12-01, 3d
    S1 P2 Co-rating evidence - B :s1b, 2026-12-01, 4d

    section Section 2
    S2 P1 User-based CF - C :s2a, 2026-12-01, 7d
    S2 P2 Item-based CF - A :s2b, 2026-12-04, 5d
    Item significance weighting - B :s2c, 2026-12-07, 3d
    Consolidated comparison - All :s2d, 2026-12-08, 2d

    section Section 3
    S3 P1 K-means - C :s3a, 2026-12-04, 6d
    S3 P2 Missing neighbors - B :s3b, 2026-12-08, 3d
    S3 P3 Complexity - A :s3c, 2026-12-08, 3d
    S3 P4 Final decision - All :s3d, 2026-12-10, 1d

    section Report and Submission
    Draft report sections :r1, 2026-12-03, 7d
    Cross-review rotation :r2, 2026-12-09, 2d
    Full pipeline run on each machine :r3, 2026-12-10, 2d
    Format QC :r4, 2026-12-10, 2d
    README and AI acknowledgment :r5, 2026-12-10, 2d
    Upload to CANVAS and GitHub :crit, r6, 2026-12-11, 1d
    Deadline Dec 12 end of day :milestone, crit, m3, 2026-12-12, 0d
```

Notes on the plan:

- **`excludes`**  Saturdays and Sundays from the bars.
- **C starts S2 P1 immediately** after the foundation, since Section 3 needs the best similarity measure, β and k. The K-means feature work (S3 P1) can begin early because it only uses training data.
- **The Dec 12 deadline is a Saturday**, so the plan finishes uploads on Dec 11. The late penalty is 50%, and anything more than 24 hours late scores zero.
- **The Week 12 individual lab** isn't dated in the spec. Once you know the date, add a section for walkthrough sessions before it.

## Dataset Selected

https://www.kaggle.com/datasets/odedgolden/movielens-1m-dataset/data?select=ratings.dat

## Proposed Stack

- python 3.13
- polars (pandas replacement)
- jax (tensorflow and pytorch replacement)
- numpy 
