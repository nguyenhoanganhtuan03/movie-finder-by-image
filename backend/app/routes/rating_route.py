from fastapi import APIRouter, FastAPI
from fastapi import Body, Path

from app.entities.rating_model import CreateRatingRequest, UpdateRating
from app.controllers.rating_controller import create_rating, get_rating_by_movie_id, delete_rating, add_rating_score

app = FastAPI()
router = APIRouter()

# Route tạo rating đầu tiên
@router.post("/")
async def create_rating_movie(data: CreateRatingRequest):
    return await create_rating(data.movie_id, data.first_score)

# Route lấy rating theo movie_id
@router.get("/{movie_id}")
async def read_rating(movie_id: str = Path(..., description="ID của phim cần lấy rating")):
    return await get_rating_by_movie_id(movie_id)

# Route thêm điểm đánh giá mới cho movie
@router.put("/")
async def add_score(update_rating: UpdateRating):
    return await add_rating_score(update_rating)

# Route xóa rating theo rating_id
@router.delete("/{rating_id}")
async def delete_rating_by_id(rating_id: str = Path(..., description="ID rating cần xóa")):
    return await delete_rating(rating_id)

# Đăng ký router vào FastAPI app
app.include_router(router)