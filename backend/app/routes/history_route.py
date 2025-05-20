from fastapi import APIRouter, HTTPException, FastAPI

from app.entities.history_model import HistoryCreateModel
from app.controllers.history_controller import create_history, get_all_histories
from app.controllers.history_controller import get_history_by_user, delete_history_by_id, delete_histories_by_user_id

app = FastAPI()
router = APIRouter()

# Route để thêm history
@router.post("/add_history")
async def add_history(history_data: HistoryCreateModel):
    try:
        result = await create_history(
            user_id=history_data.user_id,
            movie_id=history_data.movie_id,
            date_watched=history_data.date_watched
        )
        return result
    except HTTPException as e:
        raise e

# Route để lấy tất cả history
@router.get("/histories")
async def get_histories():
    try:
        histories = await get_all_histories()
        return histories
    except HTTPException as e:
        raise e

# Route để lấy history của user
@router.get("/histories/{user_id}")
async def get_history_by_user_id(user_id: str):
    try:
        history = await get_history_by_user(user_id)
        return history
    except HTTPException as e:
        raise e

# Route để xóa history
@router.delete("/{history_id}")
async def delete_history(history_id: str):
    try:
        result = await delete_history_by_id(history_id)
        return result
    except HTTPException as e:
        raise e

# Route để xóa tất cả history của user
@router.delete("/histories/{user_id}")
async def delete_histories_by_user(user_id: str):
    try:
        result = await delete_histories_by_user_id(user_id)
        return result
    except HTTPException as e:
        raise e

# Thêm route vào app
app.include_router(router)