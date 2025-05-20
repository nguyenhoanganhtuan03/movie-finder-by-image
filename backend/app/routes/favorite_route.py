from fastapi import APIRouter, HTTPException, FastAPI
from typing import List

from app.controllers.favorite_controller import add_favorite_movie, get_all_favorites_from_db
from app.controllers.favorite_controller import get_favorites_by_user_id, delete_favorite_by_id
from app.entities.favorite_model import FavoriteMovie

app = FastAPI()
router = APIRouter()

# Route để thêm bộ phim yêu thích
@router.post("/add_favorite")
async def add_to_favorites(request: FavoriteMovie):
    try:
        # Truyền request.user_id và request.movie_id vào hàm add_favorite_movie
        result = await add_favorite_movie(request.user_id, request.movie_id)
        return result
    except HTTPException as e:
        raise e

# Route để hiển thị tất cả favorite movies
@router.get("/favorites", response_model=List[FavoriteMovie])
async def get_all_favorites():
    try:
        favorites = await get_all_favorites_from_db()  # Gọi hàm trong controller
        return favorites
    except HTTPException as e:
        raise e

# Route để hiển thị tất cả favorite movies của một user
@router.get("/favorites/{user_id}")
async def get_favorites(user_id: str):
    try:
        favorites = await get_favorites_by_user_id(user_id)
        return favorites
    except HTTPException as e:
        raise e

# Route để xóa favorite movie
@router.delete("/favorites/{favorite_id}")
async def delete_favorite(favorite_id: str):
    try:
        result = await delete_favorite_by_id(favorite_id)
        return result
    except HTTPException as e:
        raise e

# Thêm route vào app
app.include_router(router)