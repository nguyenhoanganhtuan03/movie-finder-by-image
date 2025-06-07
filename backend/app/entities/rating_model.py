from pydantic import BaseModel
from typing import Optional

class RatingModel(BaseModel):
    _id: Optional[str] = None
    movie_id: str
    total_score: float = 0.0
    num_ratings: int = 0
    average_rating: float = 0.0

class CreateRatingRequest(BaseModel):
    movie_id: str
    first_score: float

class UpdateRating(BaseModel):
    movie_id: str
    new_score: float