import pandas as pd
import pytest
from fastapi.testclient import TestClient

from fallback_solution.app import app as fallback_app
from proper_solution.app import app

client = TestClient(app)
fallback_client = TestClient(fallback_app)


@pytest.fixture
def sample_request():
    return {"user_id": 1, "n_recommendations": 5}


@pytest.fixture
def movies_df():
    return pd.read_csv("model/movies.csv")


@pytest.fixture
def popularity_df():
    return pd.read_csv("model/movie_popularity.csv")


class TestHealthChecks:
    def test_proper_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_fallback_health_check(self):
        response = fallback_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestProperRecommender:
    def test_valid_recommendation_request(self, sample_request):
        response = client.post("/recommend", json=sample_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["recommendations"]) == sample_request["n_recommendations"]

    def test_recommendation_structure(self, sample_request):
        response = client.post("/recommend", json=sample_request)
        data = response.json()
        recommendation = data["recommendations"][0]

        assert isinstance(recommendation["movie_id"], int)
        assert isinstance(recommendation["title"], str)
        assert isinstance(recommendation["predicted_rating"], float)
        assert 0 <= recommendation["predicted_rating"] <= 5

    def test_different_n_recommendations(self):
        for n in [1, 3, 5, 10]:
            request = {"user_id": 1, "n_recommendations": n}
            response = client.post("/recommend", json=request)
            data = response.json()
            assert len(data["recommendations"]) == n

    def test_invalid_user_id(self):
        request = {"user_id": -1, "n_recommendations": 5}
        response = client.post("/recommend", json=request)
        assert response.status_code == 400

    def test_recommendations_are_unique(self, sample_request):
        response = client.post("/recommend", json=sample_request)
        data = response.json()
        movie_ids = [r["movie_id"] for r in data["recommendations"]]
        assert len(movie_ids) == len(set(movie_ids))


class TestFallbackRecommender:
    def test_valid_recommendation_request(self, sample_request):
        response = fallback_client.post("/recommend", json=sample_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["recommendations"]) == sample_request["n_recommendations"]

    def test_recommendation_structure(self, sample_request):
        response = fallback_client.post("/recommend", json=sample_request)
        data = response.json()
        recommendation = data["recommendations"][0]

        assert isinstance(recommendation["movie_id"], int)
        assert isinstance(recommendation["title"], str)
        assert isinstance(recommendation["popularity_score"], float)

    def test_recommendations_are_ordered(self, sample_request, popularity_df):
        response = fallback_client.post("/recommend", json=sample_request)
        data = response.json()
        scores = [r["popularity_score"] for r in data["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_different_n_recommendations(self):
        for n in [1, 3, 5, 10]:
            request = {"user_id": 1, "n_recommendations": n}
            response = fallback_client.post("/recommend", json=request)
            data = response.json()
            assert len(data["recommendations"]) == n


class TestModelBehavior:
    def test_recommendation_consistency(self, sample_request):
        response1 = client.post("/recommend", json=sample_request)
        response2 = client.post("/recommend", json=sample_request)
        assert response1.json() == response2.json()

    @pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5])
    def test_different_users_different_recommendations(self, user_id):
        request = {"user_id": user_id, "n_recommendations": 5}
        response = client.post("/recommend", json=request)
        recommendations = response.json()["recommendations"]

        if not hasattr(self, "previous_recommendations"):
            self.previous_recommendations = recommendations
        else:
            current_movies = set(r["movie_id"] for r in recommendations)
            previous_movies = set(r["movie_id"] for r in self.previous_recommendations)
            assert current_movies != previous_movies
