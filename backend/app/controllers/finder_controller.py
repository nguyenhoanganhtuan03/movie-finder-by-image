from fastapi import HTTPException
from typing import Optional, List
from pymongo import ReturnDocument

from app.database import db
from app.models.models_nlp.movie_by_content_api import search_movies_by_user_query

# Tìm movie bằng văn bản
async def search_movie_by_content(content: str):
    if not content:
        raise HTTPException(status_code=400, detail="Nội dung tìm kiếm không được để trống.")

    try:
        # Gọi hàm tìm kiếm
        _, results, _ = search_movies_by_user_query(content)

        # Chỉ lấy danh sách tên phim
        movie_names = [name for name, _ in results]

        return movie_names

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình tìm kiếm: {str(e)}")