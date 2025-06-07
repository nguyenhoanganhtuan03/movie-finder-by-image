import asyncio
from app.database import db
from app.controllers.rating_controller import create_rating

async def populate_ratings_for_all_movies(default_score: float = 5.0):
    cursor = db["movies"].find({})
    async for movie in cursor:
        movie_id = movie["_id"]
        
        try:
            result = await create_rating(movie_id, default_score)
            print(f"[✓] Rating created for movie_id={movie_id}: {result}")
        except Exception as e:
            print(f"[!] Skipped movie_id={movie_id}: {str(e)}")

# Chạy chương trình
if __name__ == "__main__":
    asyncio.run(populate_ratings_for_all_movies())
