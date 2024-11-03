import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

popularity_df = pd.read_csv("model/movie_popularity.csv")
movies_df = pd.read_csv("model/movies.csv")


class RecommendationRequest(BaseModel):
    user_id: int
    n_recommendations: int = 5


class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    popularity_score: float


class RecommendationResponse(BaseModel):
    status: str
    recommendations: list[MovieRecommendation]


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    try:
        top_movies = popularity_df.head(request.n_recommendations)

        recommendations = []
        for _, row in top_movies.iterrows():
            movie_info = movies_df[movies_df["movie_id"] == row["movie_id"]].iloc[0]
            recommendations.append(
                MovieRecommendation(
                    movie_id=int(row["movie_id"]),
                    title=movie_info["title"],
                    popularity_score=round(row["popularity_score"], 2),
                )
            )

        return RecommendationResponse(status="success", recommendations=recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, workers=4)
