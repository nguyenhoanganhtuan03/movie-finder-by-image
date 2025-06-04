from fastapi import APIRouter, FastAPI, Body

from app.controllers.chatbot_controller import chatbot

app = FastAPI()
router = APIRouter()

# Route chatbot trả lời
@router.post("/")
async def chatbot_answer(content: str = Body(..., embed=True)):
    return chatbot(content)

# Thêm route vào app
app.include_router(router)