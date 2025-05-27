from fastapi import HTTPException
from typing import Optional, List

from app.entities.movie_model import MovieModel
from app.database import db

from pymongo import ReturnDocument

# Hàm thêm movie vào cơ sở dữ liệu
async def get_next_movie_id():
    result = await db["counters"].find_one_and_update(
        {"_id": "movie_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    if result is None:
        # Lần đầu tạo id
        return "movie_1"
    else:
        return f"movie_{result['seq'] + 1}"

async def add_movie(
    name: str,
    duration: int,
    genre: Optional[List[str]],
    director: str,
    actor: List[str],
    year_of_release: int,
    describe: Optional[str],
    movie_url: str,
    poster: Optional[str] = None,
):
    existing_movie = await db["movies"].find_one({"name": name, "director": director})
    if existing_movie:
        raise HTTPException(status_code=400, detail="Movie with this name and director already exists")

    movie_id = await get_next_movie_id()

    movie_dict = {
        "_id": movie_id,
        "name": name,
        "duration": duration,
        "genre": genre,
        "director": director,
        "actor": actor,
        "year_of_release": year_of_release,
        "describe": describe,
        "movie_url": movie_url,
        "poster": poster
    }

    await db["movies"].insert_one(movie_dict)

    return {"message": "Movie added successfully", "_id": movie_id}

# Cập nhật movie
async def update_movie(movie_id: str, update_data: dict):
    # Kiểm tra xem movie có tồn tại hay không
    existing_movie = await db["movies"].find_one({"_id": movie_id})
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Cập nhật movie trong cơ sở dữ liệu
    result = await db["movies"].update_one(
        {"_id": movie_id},
        {"$set": update_data}  # Cập nhật các trường cần thay đổi
    )

    # Kiểm tra nếu không có thay đổi nào được thực hiện
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="No changes made")

    return {"message": "Movie updated successfully", "_id": movie_id}

# Xóa movie
async def delete_movie(movie_id: str):
    # Kiểm tra phim có tồn tại không
    existing_movie = await db["movies"].find_one({"_id": movie_id})
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Xóa phim
    result = await db["movies"].delete_one({"_id": movie_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete movie")

    return {"message": "Movie deleted successfully", "_id": movie_id}

# Lấy tất cả movie
async def get_all_movies():
    movies = await db["movies"].find().to_list(length=None)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found")

    # Chuyển ObjectId (nếu có) sang string nếu cần
    for movie in movies:
        movie["_id"] = str(movie["_id"])

    return {"movies": movies}

# Lấy movie theo ID
async def get_movie_by_id(movie_id: str):
    movie = await db["movies"].find_one({"_id": movie_id})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

# Tìm kiếm phim theo tên
async def search_movies_by_name(partial_name: str):
    print("🔍 Searching for:", partial_name)

    movies_cursor = db["movies"].find({
        "name": {
            "$regex": partial_name,
            "$options": "i"
        }
    })
    movies = await movies_cursor.to_list(length=None)

    print("🟢 Found:", len(movies), "movies")

    return movies

# Tìm kiếm phim theo thể loại
async def search_movies_by_genre(genre: str):
    # Tìm kiếm các bộ phim có chứa thể loại trong danh sách genre (không phân biệt hoa thường)
    movies_cursor = db["movies"].find({
        "genre": genre
    })

    # Chuyển các kết quả tìm được thành một danh sách
    movies = await movies_cursor.to_list(length=None)

    # Kiểm tra nếu không có phim nào tìm được
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found for this genre")

    return movies