import heapq
import pickle

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

with open("model/svd_model.pkl", "rb") as f:
    model = pickle.load(f)

movies_df = pd.read_csv("model/movies.csv")


class RecommendationRequest(BaseModel):
    user_id: int
    n_recommendations: int = 5


class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    predicted_rating: float


class RecommendationResponse(BaseModel):
    status: str
    recommendations: list[MovieRecommendation]


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    user_id = request.user_id
    n_users = model.pu.size
    if user_id < 0 or user_id >= n_users:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    try:
        movie_ids = movies_df["movie_id"].unique()

        predictions = []
        for movie_id in movie_ids:
            predicted_rating = model.predict(request.user_id, movie_id).est
            predictions.append((movie_id, predicted_rating))

        top_n = heapq.nlargest(request.n_recommendations, predictions, key=lambda x: x[1])

        recommendations = []
        for movie_id, predicted_rating in top_n:
            movie_info = movies_df[movies_df["movie_id"] == movie_id].iloc[0]
            recommendations.append(
                MovieRecommendation(
                    movie_id=int(movie_id),
                    title=movie_info["title"],
                    predicted_rating=round(predicted_rating, 2),
                )
            )

        return RecommendationResponse(status="success", recommendations=recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, workers=4)
