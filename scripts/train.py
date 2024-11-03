import os
import pickle

import pandas as pd
from surprise import SVD, Dataset, Reader


def train_model():
    ratings_df = pd.read_csv(
        "https://files.grouplens.org/datasets/movielens/ml-100k/u.data",
        sep="\t",
        names=["user_id", "movie_id", "rating", "timestamp"],
    )

    movies_df = pd.read_csv(
        "https://files.grouplens.org/datasets/movielens/ml-100k/u.item",
        sep="|",
        encoding="latin-1",
        names=[
            "movie_id",
            "title",
            "release_date",
            "video_release_date",
            "IMDb_URL",
            "unknown",
            "Action",
            "Adventure",
            "Animation",
            "Children",
            "Comedy",
            "Crime",
            "Documentary",
            "Drama",
            "Fantasy",
            "Film-Noir",
            "Horror",
            "Musical",
            "Mystery",
            "Romance",
            "Sci-Fi",
            "Thriller",
            "War",
            "Western",
        ],
    )

    reader = Reader(rating_scale=(1, 5))

    data = Dataset.load_from_df(ratings_df[["user_id", "movie_id", "rating"]], reader)

    model = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=0)
    trainset = data.build_full_trainset()
    model.fit(trainset)

    if not os.path.exists("model"):
        os.makedirs("model")

    with open("model/svd_model.pkl", "wb") as f:
        pickle.dump(model, f)

    movies_df.to_csv("model/movies.csv", index=False)

    movie_popularity = (
        ratings_df.groupby("movie_id")["rating"].agg(["count", "mean"]).reset_index()
    )
    movie_popularity["popularity_score"] = movie_popularity["count"] * movie_popularity["mean"]
    movie_popularity = movie_popularity.sort_values("popularity_score", ascending=False)
    movie_popularity.to_csv("model/movie_popularity.csv", index=False)


if __name__ == "__main__":
    train_model()
