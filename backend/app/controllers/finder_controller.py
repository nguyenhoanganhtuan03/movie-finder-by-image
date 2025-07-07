from fastapi import HTTPException
from typing import Optional, List
from pymongo import ReturnDocument

from app.database import db
from app.models.models_nlp.movie_by_content_api import search_movies_by_user_query
from app.models.models_audio.run_model_audio import predict_film_from_audio

# Tìm movie bằng văn bản
async def search_movie_by_content(content: str, SIMILARITY_THRESHOLD, n_movies):
    if not content:
        raise HTTPException(status_code=400, detail="Nội dung tìm kiếm không được để trống.")

    try:
        # Gọi hàm tìm kiếm
        _, results, _ = search_movies_by_user_query(content, SIMILARITY_THRESHOLD, n_movies)

        # Chỉ lấy danh sách tên phim
        movie_names = [name for name, _ in results]

        return movie_names

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình tìm kiếm: {str(e)}")

# Tìm movie bằng âm thanh
async def search_movie_by_audio(audio_path: str, SIMILARITY_THRESHOLD, n_movies):
    try:
        # Gọi hàm tìm kiếm
        results = predict_film_from_audio(audio_path, SIMILARITY_THRESHOLD, n_movies)
        movie_names = [name for name in results]
        print(movie_names)

        return movie_names

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình tìm kiếm: {str(e)}")