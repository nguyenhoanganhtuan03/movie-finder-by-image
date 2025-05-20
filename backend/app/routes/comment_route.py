from fastapi import APIRouter, HTTPException, FastAPI

from app.controllers.comment_controller import create_comment, get_all_comments, delete_comment_by_id
from app.controllers.comment_controller import get_comments_by_user_id, get_comments_by_movie_id
from app.entities.comment_model import CommentModel

app = FastAPI()
router = APIRouter()

# Route để tạo comment
@router.post("/create_comment", response_model=CommentModel)
async def create_comment_route(data: dict):
    try:
        return await create_comment(data)
    except HTTPException as e:
        raise e

# Route để lấy tất cả comment
@router.get("/", response_model=list[CommentModel])
async def read_all_comments():
    try:
        return await get_all_comments()
    except HTTPException as e:
        raise e

# Route để lấy comment theo user_id
@router.get("/user/{user_id}")
async def read_comments_by_user_id(user_id: str):
    try:
        return await get_comments_by_user_id(user_id)
    except HTTPException as e:
        raise e

# Route để lấy comment theo movie_id
@router.get("/movie/{movie_id}")
async def read_comments_by_movie_id(movie_id: str):
    try:
        return await get_comments_by_movie_id(movie_id)
    except HTTPException as e:
        raise e

# Route để xóa comment theo _id
@router.delete("/{comment_id}")
async def remove_comment_by_id(comment_id: str):
    try:
        return await delete_comment_by_id(comment_id)
    except HTTPException as e:
        raise e

# Thêm route vào FastAPI app
app.include_router(router)