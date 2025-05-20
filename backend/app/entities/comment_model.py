from pydantic import BaseModel

class CommentModel(BaseModel):
    _id: str
    user_id: str
    movie_id: str
    comment: str