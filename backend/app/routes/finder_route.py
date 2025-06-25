from fastapi import APIRouter, FastAPI, Body, Form
from pydantic import BaseModel
from typing import List

from app.controllers.finder_controller import search_movie_by_content
from app.controllers.movie_controller import search_movies_by_name

app = FastAPI()
router = APIRouter()

@router.post("/search_by_content")
async def finder_movie_by_content(content: str = Body(..., embed=True), 
                                  SIMILARITY_THRESHOLD: float = Form(default=None),
                                  n_movies: int = Form(default=None)):
    predicted_names = await search_movie_by_content(content, SIMILARITY_THRESHOLD, n_movies)

    results = []
    for name in predicted_names:
        matched = await search_movies_by_name(name)
        results.extend(matched)

    if not results:
        return {
            "predicted_names": predicted_names,
            "results": []
        }

    return {
        "predicted_names": predicted_names,
        "results": list(results)
    }

# Thêm route vào app
app.include_router(router)