import os
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16
})

RAW_DIR = Path("dataset/raw")
OUT_DIR = Path("dataset/visualize")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    print("Loading raw datasets...")

    # Users: UserID::Gender::Age::Occupation::Zip-code
    users_path = RAW_DIR / "users.dat"
    users = pd.read_csv(
        users_path,
        sep="::",
        engine="python",
        names=["UserID", "Gender", "Age", "Occupation", "ZipCode"],
        encoding="latin-1"
    )

    # Ratings: UserID::MovieID::Rating::Timestamp
    ratings_path = RAW_DIR / "ratings.dat"
    ratings = pd.read_csv(
        ratings_path,
        sep="::",
        engine="python",
        names=["UserID", "MovieID", "Rating", "Timestamp"],
        encoding="latin-1"
    )

    # Movies: MovieID::Title::Genres
    movies_path = RAW_DIR / "movies.dat"
    movies = pd.read_csv(
        movies_path,
        sep="::",
        engine="python",
        names=["MovieID", "Title", "Genres"],
        encoding="latin-1"
    )

    return users, ratings, movies

def visualize_ratings_distribution(ratings):
    print("Generating raw_ratings_distribution.svg...")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.countplot(data=ratings, x="Rating", palette="Blues_r", ax=ax, hue="Rating", legend=False)
    ax.set_title("Distribution of Raw Ratings (1-5)")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")

    # Add count labels on top of bars
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(f'{height:,}',
                    (p.get_x() + p.get_width() / 2., height),
                    ha='center', va='bottom',
                    xytext=(0, 3),
                    textcoords='offset points')

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_ratings_distribution.svg", format="svg")
    plt.close()

def visualize_user_demographics(users):
    print("Generating raw_user_demographics.svg...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Age distribution
    age_mapping = {
        1: "Under 18", 18: "18-24", 25: "25-34",
        35: "35-44", 45: "45-49", 50: "50-55", 56: "56+"
    }
    users_age = users.copy()
    users_age["AgeRange"] = users_age["Age"].map(age_mapping).fillna("Unknown")
    order = ["Under 18", "18-24", "25-34", "35-44", "45-49", "50-55", "56+"]

    sns.countplot(data=users_age, x="AgeRange", order=order, palette="viridis", ax=axes[0], hue="AgeRange", legend=False)
    axes[0].set_title("User Age Distribution")
    axes[0].set_xlabel("Age Group")
    axes[0].set_ylabel("User Count")
    axes[0].tick_params(axis='x', rotation=30)

    # Gender distribution
    sns.countplot(data=users, x="Gender", palette="Set2", ax=axes[1], hue="Gender", legend=False)
    axes[1].set_title("User Gender Distribution")
    axes[1].set_xlabel("Gender (M/F)")
    axes[1].set_ylabel("User Count")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_user_demographics.svg", format="svg")
    plt.close()

def visualize_user_occupations(users):
    print("Generating raw_user_occupations.svg...")
    occ_mapping = {
        0: "other/not specified", 1: "academic/educator", 2: "artist",
        3: "clerical/admin", 4: "college/grad student", 5: "customer service",
        6: "doctor/health care", 7: "executive/managerial", 8: "farmer",
        9: "homemaker", 10: "K-12 student", 11: "lawyer", 12: "programmer",
        13: "retired", 14: "sales/marketing", 15: "scientist", 16: "self-employed",
        17: "technician/engineer", 18: "tradesman/craftsman", 19: "unemployed", 20: "writer"
    }
    users_occ = users.copy()
    users_occ["OccupationLabel"] = users_occ["Occupation"].map(occ_mapping).fillna("unknown")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.countplot(data=users_occ, y="OccupationLabel", order=users_occ["OccupationLabel"].value_counts().index, palette="crest", ax=ax, hue="OccupationLabel", legend=False)
    ax.set_title("User Occupation Distribution")
    ax.set_xlabel("User Count")
    ax.set_ylabel("Occupation")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_user_occupations.svg", format="svg")
    plt.close()

def visualize_movie_release_years(movies):
    print("Generating raw_movie_release_years.svg...")
    # Extract year from title like "Toy Story (1995)"
    years = movies["Title"].str.extract(r'\((\d{4})\)$')[0].dropna().astype(int)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.histplot(years, bins=range(years.min(), years.max() + 2), color="coral", edgecolor="black", ax=ax)
    ax.set_title("Distribution of Movie Release Years")
    ax.set_xlabel("Release Year")
    ax.set_ylabel("Number of Movies")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_movie_release_years.svg", format="svg")
    plt.close()

def visualize_genre_popularity(movies):
    print("Generating raw_genre_popularity.svg...")
    genres_series = movies["Genres"].str.split("|").explode()
    genre_counts = genres_series.value_counts()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=genre_counts.values, y=genre_counts.index, palette="mako", ax=ax, hue=genre_counts.index, legend=False)
    ax.set_title("Movie Count by Genre (Raw)")
    ax.set_xlabel("Movie Count")
    ax.set_ylabel("Genre")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_genre_popularity.svg", format="svg")
    plt.close()

def visualize_rating_timestamps(ratings):
    print("Generating raw_rating_timestamps.svg...")
    dates = pd.to_datetime(ratings["Timestamp"], unit="s")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.histplot(dates, bins=50, color="teal", ax=ax)
    ax.set_title("Distribution of Rating Timestamps (Activity Over Time)")
    ax.set_xlabel("Time")
    ax.set_ylabel("Number of Ratings")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_rating_timestamps.svg", format="svg")
    plt.close()

def visualize_user_activity(ratings):
    print("Generating raw_user_activity.svg...")
    user_counts = ratings.groupby("UserID").size()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(user_counts, bins=50, color="purple", log_scale=(False, False), ax=ax)
    ax.set_title("Distribution of Ratings per User")
    ax.set_xlabel("Number of Ratings Given")
    ax.set_ylabel("Number of Users")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_user_activity.svg", format="svg")
    plt.close()

def visualize_movie_popularity(ratings, movies):
    print("Generating raw_movie_popularity.svg...")
    movie_counts = ratings.groupby("MovieID").size().reset_index(name="RatingCount")
    movie_merged = pd.merge(movies, movie_counts, on="MovieID", how="left").fillna(0)
    top_movies = movie_merged.sort_values(by="RatingCount", ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.barplot(data=top_movies, x="RatingCount", y="Title", palette="rocket", ax=ax, hue="Title", legend=False)
    ax.set_title("Top 20 Most Rated Movies (Raw)")
    ax.set_xlabel("Number of Ratings")
    ax.set_ylabel("Movie Title")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "raw_movie_popularity.svg", format="svg")
    plt.close()

def main():
    users, ratings, movies = load_data()

    print(f"Loaded {len(users)} users, {len(ratings)} ratings, {len(movies)} movies.")

    visualize_ratings_distribution(ratings)
    visualize_user_demographics(users)
    visualize_user_occupations(users)
    visualize_movie_release_years(movies)
    visualize_genre_popularity(movies)
    visualize_rating_timestamps(ratings)
    visualize_user_activity(ratings)
    visualize_movie_popularity(ratings, movies)

    print("All visualizations generated successfully in dataset/visualize/")

if __name__ == "__main__":
    main()
