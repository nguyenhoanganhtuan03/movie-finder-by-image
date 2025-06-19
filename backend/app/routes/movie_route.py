from fastapi import APIRouter, HTTPException, FastAPI, UploadFile, File
from fastapi import Body, Path, Query
from fastapi.responses import JSONResponse
import shutil
import os
from uuid import uuid4
from urllib.parse import unquote

from app.controllers.movie_controller import add_movie, update_movie, delete_movie, search_movies_by_genre, get_movies_by_year
from app.controllers.movie_controller import get_all_movies, get_movie_by_id, search_movies_by_name, get_all_genres
from app.entities.movie_model import MovieModel
from app.models.run_model_cnn_faiss import predict_film_auto
# from app.models.run_model_sift_faiss import predict_film_auto
# from app.models.run_model_hog_faiss import predict_film_auto

app = FastAPI()
router = APIRouter()

UPLOAD_DIR = "backend/app/uploads/uploaded_videos"
TEMP_DIR = "backend/app/uploads/upload_temps"

# Tạo thư mục lưu file nếu chưa tồn tại
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/uploadFiles")
async def upload_video_file(file: UploadFile = File(...)):
    # Tạo tên file mới tránh trùng, giữ nguyên phần mở rộng
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Upload failed: {str(e)}"})

    # URL trả về file đã upload, bạn có thể thay đổi domain/port cho phù hợp
    file_url = f"http://127.0.0.1:8000/uploaded_videos/{unique_filename}"

    return {"file_url": file_url}

# Route thêm movie
@router.post("/add_movie")
async def create_movie(movie: MovieModel):
    try:
        result = await add_movie(movie.name, movie.duration, movie.genre, movie.director,
                                 movie.actor, movie.year_of_release, movie.describe, movie.movie_url, movie.poster)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route cập nhật movie
@router.put("/update_movie/{movie_id}")
async def update_movie_route(
    movie_id: str = Path(..., title="The ID of the movie to update"),
    update_data: dict = Body(..., title="The data to update the movie")
):
    try:
        # Gọi hàm update_movie để cập nhật thông tin movie
        result = await update_movie(movie_id, update_data)
        return result
    except Exception as e:
        # Trả về HTTPException nếu có lỗi
        raise HTTPException(status_code=500, detail=str(e))

# Route xóa movie
@router.delete("/delete_movie/{movie_id}")
async def delete_movie_route(movie_id: str):
    try:
        # Gọi hàm delete_movie để xóa movie
        result = await delete_movie(movie_id)
        return result
    except Exception as e:
        # Trả về HTTPException nếu có lỗi
        raise HTTPException(status_code=500, detail=str(e))

# Route lấy tất cả movie
@router.get("/movies")
async def get_all_movies_route():
    return await get_all_movies()

# Route lấy movie theo ID
@router.get("/movies/{movie_id}")
async def get_movie_by_id_route(movie_id: str):
    return await get_movie_by_id(movie_id)

# Route tìm kiếm phim theo tên
@router.get("/search")
async def search_movie(name: str = Query(..., description="Partial movie name")):
    return await search_movies_by_name(name)

# Tìm kiếm phim bằng file ảnh, video
@router.post("/search-by-file")
async def search_movie_by_file(file: UploadFile = File(...)):
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.mov']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Chỉ chấp nhận file ảnh (JPG, PNG) hoặc video (MP4, MOV)"
        )
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(TEMP_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Upload failed: {str(e)}"})

    predicted_names = predict_film_auto(file_path)  

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

# Route tìm kiếm phim theo thể loại
@router.post("/genre")
async def get_movies_by_genre(payload: dict = Body(...)):
    genre = payload.get("genre", "").strip()
    if not genre:
        raise HTTPException(status_code=400, detail="Thiếu thể loại")

    try:
        movies = await search_movies_by_genre(genre)
        return movies
    except HTTPException as e:
        raise e
    
# Route lấy tất cả genre
@router.get("/genres")
async def list_all_genres():
    return await get_all_genres()

# Route lấy phim theo nhóm năm
@router.get("/yor/{year}")
async def fetch_movies_by_year(year: int):
    return await get_movies_by_year(year)

# Thêm route vào app
app.include_router(router)