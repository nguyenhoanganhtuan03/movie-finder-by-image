from fastapi import HTTPException
from typing import List

from app.database import db
from app.entities.favorite_model import FavoriteMovie
from pymongo import ReturnDocument

async def get_next_favorite_id():
    result = await db["counters"].find_one_and_update(
        {"_id": "favorite_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    if result is None:
        # Lần đầu tạo id
        return "favo_1"
    else:
        return f"favo_{result['seq'] + 1}"

async def add_favorite_movie(user_id: str, movie_id: str):
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    movie = await db["movies"].find_one({"_id": movie_id})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    existing_favorite = await db["favorite_movies"].find_one({"user_id": user_id, "movie_id": movie_id})
    if existing_favorite:
        return {
            "message": "Movie is already in the favorites list",
            "_id": existing_favorite["_id"]
        }

    favorite_id = await get_next_favorite_id()

    favorite_movie_dict = {
        "_id": favorite_id,
        "user_id": user_id,
        "movie_id": movie_id
    }

    await db["favorite_movies"].insert_one(favorite_movie_dict)

    return {
        "message": "Movie added to favorites successfully",
        "_id": favorite_id
    }


# Hàm truy vấn tất cả favorite movies
async def get_all_favorites_from_db() -> List[FavoriteMovie]:
    favorites_cursor = db["favorite_movies"].find()  # Truy vấn tất cả các favorite movie
    favorites = await favorites_cursor.to_list(length=None)  # Chuyển đổi kết quả thành list

    if not favorites:
        raise HTTPException(status_code=404, detail="No favorite movies found")

    return favorites


# Hàm truy vấn tất cả favorite movies theo user_id
async def get_favorites_by_user_id(user_id: str):
    favorites_cursor = db["favorite_movies"].find({"user_id": user_id})  # Truy vấn favorite theo user_id
    favorites = await favorites_cursor.to_list(length=None)  # Chuyển đổi kết quả thành list

    return favorites

# Hàm xóa favorite movie theo _id
async def delete_favorite_by_id(favorite_id: str):
    # Tìm kiếm favorite movie trong database theo _id
    result = await db["favorite_movies"].delete_one({"_id": favorite_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Favorite movie with _id {favorite_id} not found")

    return {"message": f"Favorite movie with _id {favorite_id} has been deleted"}