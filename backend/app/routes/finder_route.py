from fastapi import APIRouter, FastAPI, Body, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
from uuid import uuid4
from pydantic import BaseModel
from typing import List

from app.controllers.finder_controller import search_movie_by_content, search_movie_by_audio
from app.controllers.movie_controller import search_movies_by_name

app = FastAPI()
router = APIRouter()

TEMP_DIR = "backend/app/uploads/upload_temps"

# Route tìm kiếm bằng văn bản
@router.post("/search_by_content")
async def finder_movie_by_content(content: str = Body(..., embed=True), 
                                  SIMILARITY_THRESHOLD: float = Form(default=None),
                                  n_movies: int = Form(default=None)):
    predicted_names = await search_movie_by_content(content, SIMILARITY_THRESHOLD, n_movies)

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

# Route tìm kiếm bằng âm thanh
@router.post("/search_by_audio")
async def finder_movie_by_audio(audio_file: UploadFile = File(...),
                                  SIMILARITY_THRESHOLD: float = Form(default=None),
                                  n_movies: int = Form(default=None)):

    allowed_extensions = ['.mp3', '.wav', 'mp4']
    if not any(audio_file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail="Chỉ chấp nhận file âm thanh (MP3, WAV, MP4)"
        )

    file_ext = os.path.splitext(audio_file.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(TEMP_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Upload failed: {str(e)}"})

    predicted_names = await search_movie_by_audio(file_path, SIMILARITY_THRESHOLD, n_movies)

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

# Thêm route vào app
app.include_router(router)