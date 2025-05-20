from fastapi import HTTPException
from bson import ObjectId

from app.database import db
from app.entities.comment_model import CommentModel
from pymongo import ReturnDocument

async def get_next_comment_id():
    result = await db["counters"].find_one_and_update(
        {"_id": "comment_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    if result is None:
        # Lần đầu tạo comment id
        return "comment_1"
    else:
        return f"comment_{result['seq'] + 1}"

async def create_comment(data: dict):
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")
    comment = data.get("comment")

    # Kiểm tra user
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Kiểm tra movie
    movie = await db["movies"].find_one({"_id": movie_id})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Tạo _id mới cho comment
    comment_id = await get_next_comment_id()

    comment_data = {
        "_id": comment_id,
        "user_id": user_id,
        "movie_id": movie_id,
        "comment": comment
    }

    await db["comments"].insert_one(comment_data)

    return CommentModel(**comment_data)

# Hàm lấy tất cả comment
async def get_all_comments():
    comments_cursor = db["comments"].find()
    comments = await comments_cursor.to_list(length=None)

    if not comments:
        raise HTTPException(status_code=404, detail="No comments found")

    return [CommentModel(**comment) for comment in comments]

# Hàm lấy comment theo user_id
async def get_comments_by_user_id(user_id: str):
    comments_cursor = db["comments"].find({"user_id": user_id})
    comments = await comments_cursor.to_list(length=None)

    if not comments:
        raise HTTPException(status_code=404, detail=f"No comments found for user_id: {user_id}")

    return [CommentModel(**comment) for comment in comments]

# Hàm lấy comment theo movie_id
async def get_comments_by_movie_id(movie_id: str):
    comments_cursor = db["comments"].find({"movie_id": movie_id})
    comments = await comments_cursor.to_list(length=None)

    if not comments:
        raise HTTPException(status_code=404, detail=f"No comments found for movie_id: {movie_id}")

    # Chuyển _id từ ObjectId sang string để dễ sử dụng bên frontend
    for comment in comments:
        comment["_id"] = str(comment["_id"])

    return comments

# Hàm xóa comment theo _id
async def delete_comment_by_id(comment_id: str):
    result = await db["comments"].delete_one({"_id": comment_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Comment with _id {comment_id} not found")

    return {"detail": f"Comment with _id {comment_id} has been deleted"}