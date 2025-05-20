from pydantic import BaseModel
from typing import Optional

class FavoriteMovie(BaseModel):
    _id: Optional[str] = None
    user_id: str
    movie_id: str