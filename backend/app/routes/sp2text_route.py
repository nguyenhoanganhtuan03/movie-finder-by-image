from fastapi import APIRouter, FastAPI
from app.controllers.sp2text_controller import spech_2_text

app = FastAPI()
router = APIRouter()

@router.get("/")
async def speech_to_text_route():
    result = await spech_2_text()
    return result

# Thêm route vào app
app.include_router(router)