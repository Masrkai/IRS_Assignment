
# MovieLens-1M dataset downloader

`dataset/download.py` downloads the complete Kaggle dataset `odedgolden/movielens-1m-dataset` using Python only: `requests` for HTTP and `zipfile` for archives. It does not use the `kaggle` package, a Kaggle token, `curl`/`wget`, or shell utilities. This dataset is public, so the download works anonymously.

The downloaded bundle contains `README`, `movies.dat`, `ratings.dat` and `users.dat`. No other dataset is fetched.

## Layout

```
dataset/
  raw/      <- README, movies.dat, ratings.dat, users.dat
  treated/  <- future cleaned/split data
```

## Credentials

None needed. The Kaggle API serves this public dataset without a token, so there is nothing to configure or commit.

## Run

```bash
pip install -r requirements.txt
python dataset/download.py                  # writes all four files to dataset/raw/
python dataset/download.py --force           # download again
python dataset/download.py --version 1       # pin a dataset version
```

`python -m dataset.download` also works from the repository root. Re-running without `--force` skips the download and makes no network request.

## Use from Python

```python
from dataset.download import download_dataset

raw_dir = download_dataset()  # Path to dataset/raw/
ratings = raw_dir / "ratings.dat"
```

`ratings` can be read directly with `pl.read_csv(ratings, separator="::", has_header=False)`.
