from pydantic import BaseModel
from typing import Optional

class HistoryCreateModel(BaseModel):
    user_id: str
    movie_id: str
    date_watched: Optional[str] = None