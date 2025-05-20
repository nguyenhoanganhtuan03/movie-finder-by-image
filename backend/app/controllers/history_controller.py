from fastapi import HTTPException
from typing import Optional

from app.database import db
from datetime import datetime
from pymongo import ReturnDocument

async def get_next_history_id():
    # Thử cập nhật và tăng seq
    result = await db["counters"].find_one_and_update(
        {"_id": "history_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    # Nếu result['seq'] không tồn tại (mới tạo doc), khởi tạo seq = 1
    if "seq" not in result:
        # Khởi tạo seq = 1 cho document mới
        await db["counters"].update_one({"_id": "history_id"}, {"$set": {"seq": 1}})
        return "his_1"

    return f"his_{result['seq']}"

async def create_history(user_id: str, movie_id: str, date_watched: Optional[str]):
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    movie = await db["movies"].find_one({"_id": movie_id})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if not date_watched:
        date_watched = datetime.now().strftime("%Y-%m-%d")

    history_id = await get_next_history_id()

    history_dict = {
        "_id": history_id,
        "user_id": user_id,
        "movie_id": movie_id,
        "date_watched": date_watched
    }

    await db["history"].insert_one(history_dict)

    return {"message": "History added successfully", "_id": history_id}

# Lấy tất cả history
async def get_all_histories():
    histories_cursor = db["history"].find()
    histories = await histories_cursor.to_list(length=None)

    if not histories:
        raise HTTPException(status_code=404, detail="No history records found")

    return histories

# Tìm lịch sử theo user_id
async def get_history_by_user(user_id: str):
    histories_cursor = db["history"].find({"user_id": user_id})
    histories = await histories_cursor.to_list(length=None)

    return histories

# Xóa lịch sử xem theo _id
async def delete_history_by_id(history_id: str):
    result = await db["history"].delete_one({"_id": history_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="History not found")

    return {"message": f"History with _id '{history_id}' has been deleted successfully."}

# Xóa tất cả lịch sử xem theo user_id
async def delete_histories_by_user_id(user_id: str):
    result = await db["history"].delete_many({"user_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"No histories found for user_id '{user_id}'")

    return {"message": f"Deleted {result.deleted_count} history records for user_id '{user_id}'"}