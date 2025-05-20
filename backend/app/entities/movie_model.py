from pydantic import BaseModel
from typing import List, Optional

class MovieModel(BaseModel):
    _id: str
    poster: Optional[str] = None
    name: str
    duration: int
    genre: Optional[List[str]] = None
    director: str
    actor: List[str]
    year_of_release: int
    describe: Optional[str] = None
    movie_url: str