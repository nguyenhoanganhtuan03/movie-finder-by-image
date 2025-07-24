from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import check_connection
from app.routes.user_route import router as user_route
from app.routes.movie_route import router as movie_route
from app.routes.favorite_route import router as favorite_route
from app.routes.history_route import router as history_route
from app.routes.comment_route import router as comment_route
from app.routes.finder_route import router as finder_route
from app.routes.staff_route import router as staff_route
from app.routes.chatbot_route import router as chatbot_route
from app.routes.rating_route import router as rating_route
from app.routes.sp2text_route import router as sp2text_route

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa main.py
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads/uploaded_videos")
TEMP_DIR = os.path.join(BASE_DIR, "uploads/upload_temps")

app.mount("/uploaded_videos", StaticFiles(directory=UPLOAD_DIR), name="uploaded_videos")
app.mount("/upload_temps", StaticFiles(directory=TEMP_DIR), name="upload_temps")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await check_connection()

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/api")

# Thêm các route
app.include_router(user_route, prefix="/api/user")
app.include_router(movie_route, prefix="/api/movie")
app.include_router(favorite_route, prefix="/api/favorite")
app.include_router(history_route, prefix="/api/history")
app.include_router(comment_route, prefix="/api/comment")
app.include_router(finder_route, prefix="/api/finder")
app.include_router(staff_route, prefix="/api/staff")
app.include_router(chatbot_route, prefix="/api/chatbot")
app.include_router(rating_route, prefix="/api/rating")
app.include_router(sp2text_route, prefix="/api/sp2text")