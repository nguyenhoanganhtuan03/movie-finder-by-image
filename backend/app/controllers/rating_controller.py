from fastapi import HTTPException
from pymongo import ReturnDocument

from app.entities.rating_model import RatingModel, UpdateRating
from app.database import db

async def get_next_rating_id():
    result = await db["counters"].find_one_and_update(
        {"_id": "rating_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    return f"rating_{(result['seq'] + 1) if result else 1}"


# Tạo mới rating (phim chưa có ai đánh giá)
async def create_rating(movie_id: str, first_score: float):
    # Kiểm tra phim tồn tại
    movie = await db["movies"].find_one({"_id": movie_id})
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie ID does not exist")

    # Đã có rating rồi thì không tạo nữa
    existing_rating = await db["rating"].find_one({"movie_id": movie_id})
    if existing_rating:
        raise HTTPException(status_code=400, detail="Rating for this movie already exists")

    rating_id = await get_next_rating_id()

    rating = RatingModel(
        _id=rating_id,
        movie_id=movie_id,
        total_score=first_score,
        num_ratings=1,
        average_rating=first_score
    )
    rating_dict = rating.dict()
    rating_dict["_id"] = rating_id

    await db["rating"].insert_one(rating_dict)
    return {"message": "Rating registered successfully", "rating_id": rating_id}


# Lấy rating theo movie_id
async def get_rating_by_movie_id(movie_id: str) -> RatingModel:
    doc = await db["rating"].find_one({"movie_id": movie_id})
    if not doc:
        raise HTTPException(status_code=404, detail="No rating found for this movie")
    return RatingModel(**doc)


# Cập nhật rating bằng cách thêm 1 điểm mới
async def add_rating_score(update_rating: UpdateRating):
    rating_doc = await db["rating"].find_one({"movie_id": update_rating.movie_id})
    if not rating_doc:
        raise HTTPException(status_code=404, detail="Rating record not found for this movie")

    rating = RatingModel(**rating_doc)

    rating.total_score += update_rating.new_score
    rating.num_ratings += 1
    rating.average_rating = rating.total_score / rating.num_ratings

    await db["rating"].update_one(
        {"movie_id": update_rating.movie_id},
        {"$set": {
            "total_score": rating.total_score,
            "num_ratings": rating.num_ratings,
            "average_rating": rating.average_rating
        }}
    )

    return {"message": "Rating updated successfully", "average_rating": rating.average_rating}


# Xóa rating theo ID
async def delete_rating(rating_id: str):
    result = await db["rating"].delete_one({"_id": rating_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return {"message": "Rating deleted successfully"}
